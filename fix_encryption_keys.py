#!/usr/bin/env python3
"""
Fix Invalid Encryption Keys
Migrates old token_urlsafe(32) format to proper Fernet format
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from binary.dashboard.database import get_pg_session, get_mongo_db
from binary.dashboard.models import Agent
from cryptography.fernet import Fernet
from datetime import datetime


def is_valid_fernet_key(key: str) -> bool:
    """Check if a key is valid Fernet format"""
    try:
        Fernet(key.encode('utf-8'))
        return True
    except Exception:
        return False


def fix_postgresql_keys():
    """Fix encryption keys in PostgreSQL"""
    try:
        session = get_pg_session()
        agents = session.query(Agent).all()

        fixed_count = 0
        for agent in agents:
            if agent.encryption_key and not is_valid_fernet_key(agent.encryption_key):
                # Generate new valid key
                new_key = Fernet.generate_key().decode('utf-8')
                old_key_preview = agent.encryption_key[:20] + '...'

                agent.encryption_key = new_key
                agent.updated_at = datetime.utcnow()

                print(f"✓ Fixed PostgreSQL agent: {agent.name}")
                print(f"  Old key (invalid): {old_key_preview}")
                print(f"  New key (valid):   {new_key}")
                print()

                fixed_count += 1

        if fixed_count > 0:
            session.commit()
            print(f"✅ Fixed {fixed_count} PostgreSQL agents")
        else:
            print("✓ All PostgreSQL agents have valid encryption keys")

        return fixed_count

    except RuntimeError as e:
        print(f"⚠ PostgreSQL not available: {e}")
        return 0


def fix_mongodb_keys():
    """Fix encryption keys in MongoDB"""
    try:
        db = get_mongo_db()
        agents = db.agents.find({})

        fixed_count = 0
        for agent in agents:
            encryption_key = agent.get('encryption_key')
            if encryption_key and not is_valid_fernet_key(encryption_key):
                # Generate new valid key
                new_key = Fernet.generate_key().decode('utf-8')
                old_key_preview = encryption_key[:20] + '...'

                db.agents.update_one(
                    {'_id': agent['_id']},
                    {'$set': {
                        'encryption_key': new_key,
                        'updated_at': datetime.utcnow()
                    }}
                )

                print(f"✓ Fixed MongoDB agent: {agent.get('name', 'Unknown')}")
                print(f"  Old key (invalid): {old_key_preview}")
                print(f"  New key (valid):   {new_key}")
                print()

                fixed_count += 1

        if fixed_count > 0:
            print(f"✅ Fixed {fixed_count} MongoDB agents")
        else:
            print("✓ All MongoDB agents have valid encryption keys")

        return fixed_count

    except RuntimeError as e:
        print(f"⚠ MongoDB not available: {e}")
        return 0


def main():
    """Main migration script"""
    print("=" * 60)
    print("Encryption Key Migration Script")
    print("=" * 60)
    print()
    print("This script will update invalid encryption keys to proper Fernet format.")
    print()

    # Ask for confirmation
    response = input("Continue? [y/N]: ")
    if response.lower() not in ['y', 'yes']:
        print("Aborted.")
        return

    print()
    print("Starting migration...")
    print()

    # Fix PostgreSQL
    print("Checking PostgreSQL...")
    pg_fixed = fix_postgresql_keys()
    print()

    # Fix MongoDB
    print("Checking MongoDB...")
    mongo_fixed = fix_mongodb_keys()
    print()

    # Summary
    total_fixed = pg_fixed + mongo_fixed
    print("=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print(f"Total agents fixed: {total_fixed}")
    print()

    if total_fixed > 0:
        print("⚠ IMPORTANT: You must update the encryption keys on the agent servers!")
        print()
        print("For each agent, run these commands on the agent server:")
        print()
        print("  1. Stop the agent:")
        print("     sudo systemctl stop suricata-agent")
        print()
        print("  2. Edit the config file:")
        print("     sudo nano /etc/suricata-agent/config.yaml")
        print()
        print("  3. Update the encryption_key field with the new key shown above")
        print()
        print("  4. Restart the agent:")
        print("     sudo systemctl restart suricata-agent")
        print()
        print("Or use the 'Rotate Key' button in the dashboard UI to get the new key!")
        print()


if __name__ == '__main__':
    main()
