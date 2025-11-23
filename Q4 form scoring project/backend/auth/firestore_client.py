"""
Firestore Client for Authentication
Handles all Firestore operations for user authentication
Created: November 16, 2025
"""

from google.cloud import firestore
from datetime import datetime
from typing import Dict, Any, Optional, List
import os

# Initialize Firestore client
_firestore_client = None


def get_firestore_client():
    """Get or create Firestore client instance"""
    global _firestore_client
    if _firestore_client is None:
        project_id = os.environ.get('GCP_PROJECT', 'opex-data-lake-k23k4y98m')
        _firestore_client = firestore.Client(project=project_id)
    return _firestore_client


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get user by email from Firestore

    Args:
        email: User email address

    Returns:
        User document as dict or None if not found
    """
    db = get_firestore_client()
    doc_ref = db.collection('users').document(email)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user by user_id from Firestore

    Args:
        user_id: User ID

    Returns:
        User document as dict or None if not found
    """
    db = get_firestore_client()
    users_ref = db.collection('users')
    query = users_ref.where('user_id', '==', user_id).limit(1)
    docs = list(query.stream())

    if docs:
        user = docs[0].to_dict()
        user['email'] = docs[0].id  # Email is the document ID
        return user
    return None


def create_user(email: str, password_hash: str, full_name: str, user_id: str = None) -> Dict[str, Any]:
    """
    Create a new user in Firestore

    Args:
        email: User email (will be document ID)
        password_hash: Bcrypt password hash
        full_name: User's full name
        user_id: Optional user ID (generated if not provided)

    Returns:
        Created user document
    """
    import uuid

    db = get_firestore_client()
    now = datetime.utcnow()

    if not user_id:
        user_id = str(uuid.uuid4())

    user_data = {
        'user_id': user_id,
        'email': email,
        'password_hash': password_hash,
        'full_name': full_name,
        'created_at': now,
        'updated_at': now,
        'last_login': None,
        'failed_login_attempts': 0,
        'account_locked_until': None,
        'is_active': True
    }

    # Email is the document ID
    db.collection('users').document(email).set(user_data)

    return user_data


def update_user_login(email: str, success: bool = True) -> None:
    """
    Update user login timestamp and failed attempts

    Args:
        email: User email
        success: Whether login was successful
    """
    db = get_firestore_client()
    doc_ref = db.collection('users').document(email)
    now = datetime.utcnow()

    if success:
        # Successful login - update timestamp and reset failed attempts
        doc_ref.update({
            'last_login': now,
            'failed_login_attempts': 0,
            'account_locked_until': None,
            'updated_at': now
        })
    else:
        # Failed login - increment counter
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            failed_attempts = data.get('failed_login_attempts', 0) + 1

            updates = {
                'failed_login_attempts': failed_attempts,
                'updated_at': now
            }

            # Lock account after 5 failed attempts for 15 minutes
            if failed_attempts >= 5:
                from datetime import timedelta
                lock_until = now + timedelta(minutes=15)
                updates['account_locked_until'] = lock_until

            doc_ref.update(updates)


def create_session(session_id: str, user_id: str, token_hash: str, expires_at: datetime) -> None:
    """
    Create a new session in Firestore

    Args:
        session_id: Unique session ID
        user_id: User ID
        token_hash: SHA-256 hash of refresh token
        expires_at: Session expiration datetime
    """
    db = get_firestore_client()

    session_data = {
        'session_id': session_id,
        'user_id': user_id,
        'token_hash': token_hash,
        'created_at': datetime.utcnow(),
        'expires_at': expires_at,
        'is_active': True
    }

    db.collection('sessions').document(session_id).set(session_data)


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session by ID from Firestore

    Args:
        session_id: Session ID

    Returns:
        Session document as dict or None if not found
    """
    db = get_firestore_client()
    doc_ref = db.collection('sessions').document(session_id)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    return None


def revoke_session(session_id: str) -> None:
    """
    Revoke a session by marking it inactive

    Args:
        session_id: Session ID to revoke
    """
    db = get_firestore_client()
    doc_ref = db.collection('sessions').document(session_id)

    if doc_ref.get().exists:
        doc_ref.update({
            'is_active': False,
            'revoked_at': datetime.utcnow()
        })


def revoke_all_user_sessions_firestore(user_id: str) -> int:
    """
    Revoke all sessions for a user

    Args:
        user_id: User ID

    Returns:
        Number of sessions revoked
    """
    db = get_firestore_client()
    sessions_ref = db.collection('sessions')
    query = sessions_ref.where('user_id', '==', user_id).where('is_active', '==', True)

    count = 0
    for doc in query.stream():
        doc.reference.update({
            'is_active': False,
            'revoked_at': datetime.utcnow()
        })
        count += 1

    return count
