#!/usr/bin/env python3
"""
Setup database for Sankalpam (without Docker)
Creates database and user if they don't exist
"""
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database configuration
DB_NAME = "sankalpam_db"
DB_USER = "sankalpam_user"
DB_PASSWORD = "sankalpam_password"
DB_HOST = "localhost"
DB_PORT = 5432

# Admin connection (uses default postgres user)
ADMIN_USER = "postgres"
# You'll need to enter the postgres password
ADMIN_PASSWORD = input(f"Enter password for PostgreSQL '{ADMIN_USER}' user: ")

try:
    # Connect as postgres admin to create database
    print(f"\nConnecting to PostgreSQL as '{ADMIN_USER}'...")
    admin_conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=ADMIN_USER,
        password=ADMIN_PASSWORD,
        database="postgres"  # Connect to default postgres database
    )
    admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    admin_cursor = admin_conn.cursor()
    
    print("✓ Connected to PostgreSQL")
    
    # Check if database exists
    admin_cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (DB_NAME,)
    )
    db_exists = admin_cursor.fetchone()
    
    if db_exists:
        print(f"✓ Database '{DB_NAME}' already exists")
    else:
        print(f"Creating database '{DB_NAME}'...")
        admin_cursor.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(DB_NAME)
        ))
        print(f"✓ Database '{DB_NAME}' created")
    
    # Check if user exists
    admin_cursor.execute(
        "SELECT 1 FROM pg_user WHERE usename = %s",
        (DB_USER,)
    )
    user_exists = admin_cursor.fetchone()
    
    if user_exists:
        print(f"✓ User '{DB_USER}' already exists")
        # Update password in case it changed
        admin_cursor.execute(
            sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                sql.Identifier(DB_USER)
            ),
            (DB_PASSWORD,)
        )
        print(f"✓ User '{DB_USER}' password updated")
    else:
        print(f"Creating user '{DB_USER}'...")
        admin_cursor.execute(
            sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                sql.Identifier(DB_USER)
            ),
            (DB_PASSWORD,)
        )
        print(f"✓ User '{DB_USER}' created")
    
    # Grant privileges
    print(f"Granting privileges to '{DB_USER}' on '{DB_NAME}'...")
    admin_cursor.execute(
        sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(DB_NAME),
            sql.Identifier(DB_USER)
        )
    )
    print("✓ Privileges granted")
    
    admin_cursor.close()
    admin_conn.close()
    
    # Test connection with new user
    print(f"\nTesting connection with '{DB_USER}'...")
    test_conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    test_conn.close()
    print("✓ Connection test successful!")
    
    print("\n" + "="*50)
    print("✓ Database setup complete!")
    print("="*50)
    print(f"\nDatabase: {DB_NAME}")
    print(f"User: {DB_USER}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print("\nYou can now run database migrations:")
    print("  alembic upgrade head")
    print("\n")
    
except psycopg2.OperationalError as e:
    print(f"\n✗ Error connecting to PostgreSQL: {e}")
    print("\nMake sure:")
    print("  1. PostgreSQL is running")
    print("  2. You entered the correct postgres password")
    print("  3. PostgreSQL is accessible on port 5432")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


