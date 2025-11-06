#!/usr/bin/env python3
"""
Create Initial Super Admin User
Bootstraps the system with the first admin account
Created: November 5, 2025

Usage:
    python3 create_admin.py --email admin@opextech.com --name "Admin User" --password "SecureP@ssw0rd123"

    Or interactive mode:
    python3 create_admin.py
"""

import sys
import os
import argparse
import getpass
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from common.config import config
    from common.logger import get_logger
    from common.bigquery_client import get_bigquery_client, execute_query, insert_rows
    from common.validators import validate_email, validate_password
except ImportError:
    from config_standalone import config
    from logger_standalone import get_logger
    from bigquery_client_standalone import get_bigquery_client, execute_query, insert_rows
    from validators_standalone import validate_email, validate_password

from password_utils import hash_password
from permissions_utils import grant_permission

logger = get_logger('admin.setup')


def check_existing_admin(email: str) -> bool:
    """
    Check if user already exists

    Args:
        email: Email to check

    Returns:
        bool: True if user exists
    """
    try:
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'users')
        query = f"""
        SELECT user_id
        FROM `{table_ref}`
        WHERE email = @email
        LIMIT 1
        """

        from google.cloud import bigquery
        results = execute_query(
            query,
            params=[bigquery.ScalarQueryParameter("email", "STRING", email)]
        )

        return len(results) > 0

    except Exception as e:
        logger.error('Failed to check existing user', error=str(e))
        return False


def create_admin_user(email: str, full_name: str, password: str, skip_permission: bool = False) -> tuple:
    """
    Create super admin user

    Args:
        email: Admin email address
        full_name: Admin full name
        password: Admin password
        skip_permission: Skip permission grant (for testing)

    Returns:
        tuple: (success: bool, user_id: str, error: str)
    """
    try:
        # Validate email
        is_valid, error = validate_email(email)
        if not is_valid:
            return False, None, error

        # Validate password
        is_valid, error = validate_password(password)
        if not is_valid:
            return False, None, error

        # Check if user already exists
        if check_existing_admin(email):
            return False, None, f"User with email {email} already exists"

        # Hash password
        password_hash = hash_password(password)

        # Create user record
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()

        user_data = {
            'user_id': user_id,
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'mfa_secret': None,
            'failed_login_attempts': 0,
            'account_locked_until': None,
            'created_at': now.isoformat(),
            'last_login': None,
            'password_changed_at': now.isoformat(),
            'status': 'active',
            'created_by': user_id,  # Self-created
            'updated_at': None,
            'updated_by': None
        }

        # Insert user into BigQuery
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'users')
        insert_rows(table_ref, [user_data])

        logger.info('Admin user created successfully', user_id=user_id, email=email)
        print(f"✓ Admin user created: {email} (ID: {user_id})")

        # Grant super admin permission if not skipped
        if not skip_permission:
            # Note: This uses 'system' as granted_by for initial bootstrap
            # We'll bypass the admin check for this initial grant
            success, perm_id, error = grant_super_admin_permission(user_id)

            if not success:
                print(f"⚠ Warning: Failed to grant super admin permission: {error}")
                print(f"  You can grant it manually later using:")
                print(f"  python3 grant_permission.py --user-id {user_id} --level admin")
            else:
                logger.info('Super admin permission granted', permission_id=perm_id, user_id=user_id)
                print(f"✓ Super admin permission granted (ID: {perm_id})")

        return True, user_id, None

    except Exception as e:
        logger.exception('Failed to create admin user', error=str(e))
        return False, None, str(e)


def grant_super_admin_permission(user_id: str) -> tuple:
    """
    Grant super admin permission (NULL company, NULL category, admin level)

    This is a special function that bypasses the normal admin check
    for the initial bootstrap process.

    Args:
        user_id: User to grant super admin to

    Returns:
        tuple: (success: bool, permission_id: str, error: str)
    """
    try:
        permission_id = str(uuid.uuid4())
        now = datetime.utcnow()

        permission_data = {
            'permission_id': permission_id,
            'user_id': user_id,
            'company': None,  # Super admin
            'category': None,  # Super admin
            'permission_level': 'admin',
            'granted_by': 'system',  # Special bootstrap grant
            'granted_at': now.isoformat(),
            'expires_at': None,  # Never expires
            'is_active': True,
            'revoked_by': None,
            'revoked_at': None,
            'notes': 'Initial super admin - system bootstrap'
        }

        # Insert permission
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'permission_groups')
        insert_rows(table_ref, [permission_data])

        return True, permission_id, None

    except Exception as e:
        logger.exception('Failed to grant super admin permission', error=str(e))
        return False, None, str(e)


def interactive_create_admin():
    """
    Interactive mode for creating admin user
    """
    print("\n" + "="*60)
    print("Create Initial Super Admin User")
    print("="*60 + "\n")

    # Get email
    while True:
        email = input("Admin email address: ").strip()
        is_valid, error = validate_email(email)
        if is_valid:
            break
        print(f"  ✗ {error}")

    # Get full name
    full_name = input("Admin full name: ").strip()
    if not full_name:
        full_name = "System Administrator"

    # Get password
    while True:
        password = getpass.getpass("Admin password: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            print("  ✗ Passwords do not match")
            continue

        is_valid, error = validate_password(password)
        if is_valid:
            break
        print(f"  ✗ {error}")

    print("\nCreating admin user...")
    success, user_id, error = create_admin_user(email, full_name, password)

    if success:
        print("\n" + "="*60)
        print("✓ SUCCESS - Admin User Created")
        print("="*60)
        print(f"\nEmail: {email}")
        print(f"User ID: {user_id}")
        print(f"Name: {full_name}")
        print(f"\n⚠️ IMPORTANT: BigQuery Limitation")
        print("-" * 60)
        print("Due to BigQuery's streaming buffer limitation, you must wait")
        print("90 minutes before logging in with this account.")
        print(f"\nYou can login after: {(datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')} UTC + 90 minutes")
        print("\nFor production, consider migrating authentication to Firestore.")
        print("See backend/auth/BIGQUERY_LIMITATIONS.md for details.")
        print("="*60 + "\n")
    else:
        print("\n✗ Failed to create admin user:")
        print(f"  {error}\n")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Create initial super admin user',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python3 create_admin.py

  # Command line mode
  python3 create_admin.py --email admin@opextech.com --name "Admin User" --password "SecureP@ss123"

  # Skip permission grant (for testing)
  python3 create_admin.py --email test@example.com --name "Test" --password "TestP@ss123" --skip-permission

Note:
  Due to BigQuery streaming buffer limitations, newly created admins
  cannot login for 90 minutes. Consider migrating to Firestore for
  production use.
        """
    )

    parser.add_argument('--email', help='Admin email address')
    parser.add_argument('--name', '--full-name', dest='full_name', help='Admin full name')
    parser.add_argument('--password', help='Admin password')
    parser.add_argument('--skip-permission', action='store_true',
                       help='Skip granting super admin permission')

    args = parser.parse_args()

    # Check if running in interactive mode
    if not args.email or not args.password:
        interactive_create_admin()
        return

    # Command line mode
    email = args.email
    full_name = args.full_name or "System Administrator"
    password = args.password

    print(f"\nCreating admin user: {email}")
    success, user_id, error = create_admin_user(email, full_name, password, args.skip_permission)

    if success:
        print(f"✓ Admin user created successfully")
        print(f"  User ID: {user_id}")
        print(f"  Email: {email}")
        print(f"\n⚠️  IMPORTANT: Wait 90 minutes before attempting to login due to BigQuery limitation")
    else:
        print(f"✗ Failed: {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
