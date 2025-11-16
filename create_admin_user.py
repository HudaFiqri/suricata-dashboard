#!/usr/bin/env python3
"""
Create default admin user in MongoDB or PostgreSQL
Run this script to create the default admin/admin user
"""

import sys
import os
from dotenv import load_dotenv
import bcrypt
from datetime import datetime

# Load environment variables
load_dotenv()

def create_user_mongodb():
    """Create admin user in MongoDB"""
    from pymongo import MongoClient

    host = os.getenv('MONGO_HOST', 'localhost')
    port = int(os.getenv('MONGO_PORT', 27017))
    database_name = os.getenv('MONGO_DB', 'suricata')
    user = os.getenv('MONGO_USER', '')
    password = os.getenv('MONGO_PASSWORD', '')
    auth_source = os.getenv('MONGO_AUTH_SOURCE', 'admin')

    # Build URI
    if user and password:
        uri = f"mongodb://{user}:{password}@{host}:{port}/?authSource={auth_source}"
    else:
        uri = f"mongodb://{host}:{port}/"

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        db = client[database_name]

        # Check if admin user already exists
        existing = db.users.find_one({'username': 'admin'})
        if existing:
            print("✓ Admin user already exists in MongoDB")
            return True

        # Create admin user
        password_hash = bcrypt.hashpw('admin'.encode(), bcrypt.gensalt()).decode()

        user_doc = {
            'username': 'admin',
            'email': 'admin@localhost',
            'password_hash': password_hash,
            'role': 'admin',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        result = db.users.insert_one(user_doc)
        print(f"✓ Admin user created in MongoDB (ID: {result.inserted_id})")
        print("  Username: admin")
        print("  Password: admin")
        print("  Role: admin")
        return True

    except Exception as e:
        print(f"✗ Failed to create user in MongoDB: {e}")
        return False

def create_user_postgresql():
    """Create admin user in PostgreSQL"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    database = os.getenv('POSTGRES_DB', 'suricata_dashboard')
    user = os.getenv('POSTGRES_USER', 'suricata')
    password = os.getenv('POSTGRES_PASSWORD', 'password')

    uri = f"postgresql://{user}:{password}@{host}:{port}/{database}"

    try:
        engine = create_engine(uri)
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")

        Session = sessionmaker(bind=engine)
        session = Session()

        # Import User model
        from binary.dashboard.models import User, Base

        # Create tables if they don't exist
        Base.metadata.create_all(engine)

        # Check if admin user already exists
        existing = session.query(User).filter_by(username='admin').first()
        if existing:
            print("✓ Admin user already exists in PostgreSQL")
            return True

        # Create admin user
        password_hash = bcrypt.hashpw('admin'.encode(), bcrypt.gensalt()).decode()

        admin_user = User(
            username='admin',
            email='admin@localhost',
            password_hash=password_hash,
            role='admin',
            is_active=True
        )

        session.add(admin_user)
        session.commit()

        print(f"✓ Admin user created in PostgreSQL (ID: {admin_user.id})")
        print("  Username: admin")
        print("  Password: admin")
        print("  Role: admin")
        return True

    except Exception as e:
        print(f"✗ Failed to create user in PostgreSQL: {e}")
        return False

def main():
    print("=" * 60)
    print("Creating default admin user...")
    print("=" * 60)

    # Try PostgreSQL first
    print("\nTrying PostgreSQL...")
    if create_user_postgresql():
        print("\n✓ User created successfully in PostgreSQL")
        return 0

    # Fallback to MongoDB
    print("\nPostgreSQL not available, trying MongoDB...")
    if create_user_mongodb():
        print("\n✓ User created successfully in MongoDB")
        return 0

    print("\n✗ Failed to create user in any database")
    print("Please ensure at least one database (PostgreSQL or MongoDB) is available")
    return 1

if __name__ == '__main__':
    sys.exit(main())
