#!/usr/bin/env python3
"""
Fix database user authentication issue
Creates user and sets correct password
"""
import sys
import getpass
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database configuration
DB_NAME = "sankalpam_db"
DB_USER = "sankalpam_user"
DB_PASSWORD = "sankalpam_password"
DB_HOST = "localhost"
DB_PORT = 5432

print("="*60)
print("  Fixing Database User Authentication")
print("="*60)
print()

# Get postgres admin password
print("You need to enter your PostgreSQL 'postgres' user password")
print("(This is the password you set when installing PostgreSQL)")
print()
ADMIN_PASSWORD = getpass.getpass(f"Enter password for 'postgres' user: ")

try:
    # Connect as postgres admin
    print(f"\nConnecting to PostgreSQL as 'postgres'...")
    admin_conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user="postgres",
        password=ADMIN_PASSWORD,
        database="postgres"
    )
    admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    admin_cursor = admin_conn.cursor()
    
    print("✓ Connected to PostgreSQL")
    
    # Check if database exists, create if not
    admin_cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (DB_NAME,)
    )
    db_exists = admin_cursor.fetchone()
    
    if not db_exists:
        print(f"Creating database '{DB_NAME}'...")
        admin_cursor.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(DB_NAME)
        ))
        print(f"✓ Database '{DB_NAME}' created")
    else:
        print(f"✓ Database '{DB_NAME}' already exists")
    
    # Check if user exists
    admin_cursor.execute(
        "SELECT 1 FROM pg_user WHERE usename = %s",
        (DB_USER,)
    )
    user_exists = admin_cursor.fetchone()
    
    if user_exists:
        print(f"User '{DB_USER}' exists. Updating password...")
        # Drop user and recreate to ensure clean state
        try:
            admin_cursor.execute(
                sql.SQL("DROP USER IF EXISTS {}").format(
                    sql.Identifier(DB_USER)
                )
            )
            print(f"  Dropped existing user")
        except:
            pass
    
    # Create user with correct password
    print(f"Creating user '{DB_USER}' with password...")
    admin_cursor.execute(
        sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
            sql.Identifier(DB_USER)
        ),
        (DB_PASSWORD,)
    )
    print(f"✓ User '{DB_USER}' created")
    
    # Grant privileges
    print(f"Granting privileges...")
    admin_cursor.execute(
        sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(DB_NAME),
            sql.Identifier(DB_USER)
        )
    )
    
    # Also grant schema privileges
    admin_cursor.execute(
        sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
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
    
    print("\n" + "="*60)
    print("✓ Database user fixed successfully!")
    print("="*60)
    print(f"\nDatabase: {DB_NAME}")
    print(f"User: {DB_USER}")
    print(f"Password: {DB_PASSWORD}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print("\nYou can now start the backend server!")
    print()
    
except psycopg2.OperationalError as e:
    print(f"\n✗ Error: {e}")
    print("\nPossible issues:")
    print("  1. Wrong postgres password")
    print("  2. PostgreSQL is not running")
    print("  3. PostgreSQL is on a different port")
    print("\nTry:")
    print("  - Check if PostgreSQL service is running")
    print("  - Verify the postgres password")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


