#!/usr/bin/env python3
"""
Grant Permission CLI Tool
Command-line tool for manually granting permissions
Created: November 5, 2025

Usage:
    # Grant super admin
    python3 grant_permission_cli.py --user-id USER_ID --level admin

    # Grant company admin
    python3 grant_permission_cli.py --user-id USER_ID --level admin --company "Acme Corp"

    # Grant category-specific permission
    python3 grant_permission_cli.py --user-id USER_ID --level edit --company "Acme Corp" --category "SASE"
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from common.config import config
    from common.logger import get_logger
    from common.bigquery_client import insert_rows
except ImportError:
    from config_standalone import config
    from logger_standalone import get_logger
    from bigquery_client_standalone import insert_rows

import uuid

logger = get_logger('admin.grant_permission')


def grant_permission_direct(user_id: str, level: str, company: str = None,
                           category: str = None, granted_by: str = 'system',
                           expires_days: int = None, notes: str = None) -> tuple:
    """
    Directly grant permission without admin checks

    This bypasses the normal grant_permission function which requires
    the granter to have admin permission. Use this for initial setup only.

    Args:
        user_id: User to grant permission to
        level: Permission level ('view', 'edit', 'admin')
        company: Company scope (None = all companies)
        category: Category scope (None = all categories)
        granted_by: Who is granting (default: 'system')
        expires_days: Optional expiration in days
        notes: Optional notes

    Returns:
        tuple: (success: bool, permission_id: str, error: str)
    """
    try:
        # Validate level
        valid_levels = ['view', 'edit', 'admin']
        if level not in valid_levels:
            return False, None, f"Invalid permission level. Must be one of: {', '.join(valid_levels)}"

        # Create permission record
        permission_id = str(uuid.uuid4())
        now = datetime.utcnow()

        expires_at = None
        if expires_days:
            from datetime import timedelta
            expires_at = now + timedelta(days=expires_days)

        permission_data = {
            'permission_id': permission_id,
            'user_id': user_id,
            'company': company,
            'category': category,
            'permission_level': level,
            'granted_by': granted_by,
            'granted_at': now.isoformat(),
            'expires_at': expires_at.isoformat() if expires_at else None,
            'is_active': True,
            'revoked_by': None,
            'revoked_at': None,
            'notes': notes or f'Manually granted via CLI by {granted_by}'
        }

        # Insert directly into BigQuery
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'permission_groups')
        insert_rows(table_ref, [permission_data])

        logger.info('Permission granted directly', permission_id=permission_id,
                   user_id=user_id, level=level, company=company, category=category)

        return True, permission_id, None

    except Exception as e:
        logger.exception('Failed to grant permission directly', error=str(e))
        return False, None, str(e)


def main():
    parser = argparse.ArgumentParser(
        description='Grant permission to a user',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Grant super admin (access to everything)
  python3 grant_permission_cli.py --user-id abc-123 --level admin

  # Grant company admin (all categories for company)
  python3 grant_permission_cli.py --user-id abc-123 --level admin --company "Acme Corp"

  # Grant category-specific edit permission
  python3 grant_permission_cli.py --user-id abc-123 --level edit \\
    --company "Acme Corp" --category "SASE"

  # Grant temporary permission (expires in 90 days)
  python3 grant_permission_cli.py --user-id abc-123 --level view \\
    --company "Acme Corp" --category "SASE" --expires-days 90 \\
    --notes "90-day contractor access"

Scope Rules:
  company=None, category=None  : Super admin (access to ALL data)
  company='X', category=None   : Company admin (all categories for company X)
  company='X', category='Y'    : Category-specific (only Y for company X)

Permission Levels:
  admin : Full access + can grant/revoke permissions
  edit  : Can create, read, update, delete data
  view  : Read-only access
        """
    )

    parser.add_argument('--user-id', required=True,
                       help='User ID to grant permission to')
    parser.add_argument('--level', required=True, choices=['view', 'edit', 'admin'],
                       help='Permission level')
    parser.add_argument('--company', default=None,
                       help='Company scope (omit for all companies)')
    parser.add_argument('--category', default=None,
                       help='Category scope (omit for all categories)')
    parser.add_argument('--granted-by', default='system',
                       help='Who is granting the permission (default: system)')
    parser.add_argument('--expires-days', type=int, default=None,
                       help='Permission expiration in days (omit for never)')
    parser.add_argument('--notes', default=None,
                       help='Optional notes about this permission')

    args = parser.parse_args()

    # Display what will be granted
    print("\nGranting Permission")
    print("-" * 60)
    print(f"User ID:    {args.user_id}")
    print(f"Level:      {args.level}")
    print(f"Company:    {args.company or '(all companies)'}")
    print(f"Category:   {args.category or '(all categories)'}")
    print(f"Granted by: {args.granted_by}")
    if args.expires_days:
        print(f"Expires:    {args.expires_days} days")
    if args.notes:
        print(f"Notes:      {args.notes}")
    print("-" * 60)

    # Confirm
    confirm = input("\nProceed? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        sys.exit(0)

    # Grant permission
    print("\nGranting permission...")
    success, perm_id, error = grant_permission_direct(
        user_id=args.user_id,
        level=args.level,
        company=args.company,
        category=args.category,
        granted_by=args.granted_by,
        expires_days=args.expires_days,
        notes=args.notes
    )

    if success:
        print(f"✓ Permission granted successfully")
        print(f"  Permission ID: {perm_id}")
        print(f"\nThe user now has '{args.level}' permission for:")
        if args.company:
            print(f"  Company: {args.company}")
        else:
            print(f"  Company: ALL")
        if args.category:
            print(f"  Category: {args.category}")
        else:
            print(f"  Category: ALL")
    else:
        print(f"✗ Failed to grant permission:")
        print(f"  {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
