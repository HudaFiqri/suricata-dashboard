#!/usr/bin/env python3
"""
Create Default User
Creates admin user for first-time setup
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from binary.dashboard.database import init_postgresql, get_pg_session, create_tables
from binary.dashboard.models import User
import bcrypt
import getpass

def create_user(username, password, role='admin'):
    """Create a new user"""

    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Create user
    user = User(
        username=username,
        password_hash=password_hash,
        role=role,
        is_active=True
    )

    session = get_pg_session()

    try:
        # Check if user exists
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            print(f"Error: User '{username}' already exists")
            return False

        session.add(user)
        session.commit()

        print(f"✓ User '{username}' created successfully")
        print(f"  Role: {role}")
        return True

    except Exception as e:
        session.rollback()
        print(f"Error creating user: {e}")
        return False
    finally:
        session.remove()

def main():
    print("=" * 60)
    print("Create Dashboard User")
    print("=" * 60)

    # Initialize database
    try:
        init_postgresql()
        create_tables()
        print("✓ Database connection established\n")
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        print("\nMake sure PostgreSQL is running and .env is configured correctly")
        sys.exit(1)

    # Get user input
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input("Username [admin]: ").strip() or "admin"

    if len(sys.argv) > 2:
        password = sys.argv[2]
    else:
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("Error: Passwords do not match")
            sys.exit(1)

    if len(sys.argv) > 3:
        role = sys.argv[3]
    else:
        role = input("Role [admin]: ").strip() or "admin"

    # Create user
    if create_user(username, password, role):
        print("\n" + "=" * 60)
        print("User created successfully!")
        print("=" * 60)
        print(f"\nYou can now login with:")
        print(f"  Username: {username}")
        print(f"  Password: ********")
        print(f"\nAccess dashboard at: http://localhost:5000")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
