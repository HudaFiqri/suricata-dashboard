#!/usr/bin/env python3
"""
Database Migration Runner
Runs PostgreSQL and MongoDB migrations
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log_info(msg):
    print(f"{BLUE}[INFO]{RESET} {msg}")

def log_success(msg):
    print(f"{GREEN}[SUCCESS]{RESET} {msg}")

def log_warn(msg):
    print(f"{YELLOW}[WARN]{RESET} {msg}")

def log_error(msg):
    print(f"{RED}[ERROR]{RESET} {msg}")

def get_db_config():
    """Get database configuration from environment"""
    return {
        'postgresql': {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'suricata_dashboard'),
            'user': os.getenv('POSTGRES_USER', 'suricata'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password')
        },
        'mongodb': {
            'host': os.getenv('MONGO_HOST', 'localhost'),
            'port': os.getenv('MONGO_PORT', '27017'),
            'database': os.getenv('MONGO_DB', 'suricata'),
            'user': os.getenv('MONGO_USER', 'suricata'),
            'password': os.getenv('MONGO_PASSWORD', 'password'),
            'auth_source': os.getenv('MONGO_AUTH_SOURCE', 'admin')
        }
    }

def migrate_postgresql(action='upgrade'):
    """Run PostgreSQL migrations"""
    log_info("Running PostgreSQL migrations...")

    config = get_db_config()['postgresql']
    migrations_dir = Path(__file__).parent / 'postgresql'

    # Get all migration files
    migration_files = sorted(migrations_dir.glob('*.sql'))

    if not migration_files:
        log_warn("No PostgreSQL migration files found")
        return

    # Build psql connection string
    pg_env = os.environ.copy()
    pg_env['PGPASSWORD'] = config['password']

    for migration_file in migration_files:
        log_info(f"Applying {migration_file.name}...")

        cmd = [
            'psql',
            '-h', config['host'],
            '-p', config['port'],
            '-U', config['user'],
            '-d', config['database'],
            '-f', str(migration_file)
        ]

        try:
            result = subprocess.run(
                cmd,
                env=pg_env,
                capture_output=True,
                text=True,
                check=True
            )
            log_success(f"Applied {migration_file.name}")

        except subprocess.CalledProcessError as e:
            log_error(f"Failed to apply {migration_file.name}")
            log_error(e.stderr)
            sys.exit(1)

    log_success("PostgreSQL migrations completed")

def migrate_mongodb():
    """Run MongoDB migrations"""
    log_info("Running MongoDB migrations...")

    config = get_db_config()['mongodb']
    migrations_dir = Path(__file__).parent / 'mongodb'

    # Get all migration files
    migration_files = sorted(migrations_dir.glob('*.js'))

    if not migration_files:
        log_warn("No MongoDB migration files found")
        return

    # Build mongo connection string
    if config['user'] and config['password']:
        auth_str = f"{config['user']}:{config['password']}@"
        auth_db = f"--authenticationDatabase {config['auth_source']}"
    else:
        auth_str = ""
        auth_db = ""

    for migration_file in migration_files:
        log_info(f"Applying {migration_file.name}...")

        cmd = f"mongo {config['database']} --host {config['host']} --port {config['port']} {auth_db} < {migration_file}"

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )

            # Print migration output
            if result.stdout:
                for line in result.stdout.splitlines():
                    if line.strip():
                        print(f"  {line}")

            log_success(f"Applied {migration_file.name}")

        except subprocess.CalledProcessError as e:
            log_error(f"Failed to apply {migration_file.name}")
            if e.stderr:
                log_error(e.stderr)
            sys.exit(1)

    log_success("MongoDB migrations completed")

def check_dependencies():
    """Check if required tools are installed"""
    log_info("Checking dependencies...")

    # Check psql
    try:
        subprocess.run(['psql', '--version'], capture_output=True, check=True)
        log_success("PostgreSQL client (psql) found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_error("PostgreSQL client (psql) not found")
        log_error("Install it: apt-get install postgresql-client (Debian/Ubuntu) or yum install postgresql (CentOS)")
        sys.exit(1)

    # Check mongo
    try:
        subprocess.run(['mongo', '--version'], capture_output=True, check=True)
        log_success("MongoDB client (mongo) found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_error("MongoDB client (mongo) not found")
        log_error("Install it: https://docs.mongodb.com/manual/installation/")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Run database migrations')
    parser.add_argument(
        '--database',
        choices=['postgresql', 'mongodb', 'all'],
        default='all',
        help='Which database to migrate (default: all)'
    )
    parser.add_argument(
        '--action',
        choices=['upgrade', 'downgrade'],
        default='upgrade',
        help='Migration action (default: upgrade)'
    )
    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='Skip dependency checks'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Suricata Dashboard - Database Migration")
    print("=" * 60)
    print()

    # Check dependencies
    if not args.skip_checks:
        check_dependencies()
        print()

    # Run migrations
    if args.database in ['postgresql', 'all']:
        migrate_postgresql(args.action)
        print()

    if args.database in ['mongodb', 'all']:
        migrate_mongodb()
        print()

    print("=" * 60)
    log_success("All migrations completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    main()
