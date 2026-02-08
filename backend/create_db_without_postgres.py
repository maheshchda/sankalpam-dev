#!/usr/bin/env python3
"""
Create database and user without needing postgres password
Uses Windows authentication or tries common default passwords
"""
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import getpass
import os

# Database configuration
DB_NAME = "sankalpam_db"
DB_USER = "sankalpam_user"
DB_PASSWORD = "sankalpam_password"
DB_HOST = "localhost"
DB_PORT = 5432

print("="*60)
print("  Create Database Without Postgres Password")
print("="*60)
print()

# Try different connection methods
connection_methods = []

# Method 1: Try Windows username
windows_user = os.environ.get('USERNAME') or os.environ.get('USER')
if windows_user:
    connection_methods.append(("Windows user", windows_user, None))

# Method 2: Try common default passwords
common_passwords = [
    "postgres",
    "admin",
    "password",
    "",
    None  # No password
]

print("Trying to connect to PostgreSQL...")
print()

success = False
admin_conn = None
admin_user = None

# Try Windows authentication first
if windows_user:
    print(f"Trying Windows authentication with user: {windows_user}")
    try:
        admin_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=windows_user,
            database="postgres"
        )
        admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        admin_user = windows_user
        print(f"[OK] Connected using Windows authentication!")
        success = True
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")

# Try common passwords
if not success:
    print("\nTrying common passwords for 'postgres' user...")
    for password in common_passwords:
        try:
            print(f"  Trying password: {'(empty)' if password == '' or password is None else password}")
            admin_conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user="postgres",
                password=password or "",
                database="postgres"
            )
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            admin_user = "postgres"
            print(f"[OK] Connected with password: {'(empty)' if password == '' or password is None else password}")
            success = True
            break
        except Exception as e:
            print(f"  [X] Failed")
            continue

# If still not connected, ask user
if not success:
    print("\n" + "="*60)
    print("Could not connect automatically.")
    print("="*60)
    print("\nOptions:")
    print("1. Enter postgres password manually")
    print("2. Reset postgres password (see RESET-POSTGRES-PASSWORD.md)")
    print("3. Use pgAdmin to create database manually")
    print()
    
    choice = input("Enter '1' to try password, or 'q' to quit: ").strip()
    if choice == '1':
        password = getpass.getpass("Enter postgres password: ")
        try:
            admin_conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user="postgres",
                password=password,
                database="postgres"
            )
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            admin_user = "postgres"
            success = True
            print("[OK] Connected!")
        except Exception as e:
            print(f"[X] Failed: {str(e)}")
            sys.exit(1)
    else:
        print("\nPlease see RESET-POSTGRES-PASSWORD.md for instructions.")
        sys.exit(1)

if not success or not admin_conn:
    print("\n[X] Could not connect to PostgreSQL")
    print("\nPlease:")
    print("  1. Check if PostgreSQL is running")
    print("  2. Reset postgres password (see RESET-POSTGRES-PASSWORD.md)")
    print("  3. Use pgAdmin to create database manually")
    sys.exit(1)

# Now create database and user
try:
    admin_cursor = admin_conn.cursor()
    
    # Check if database exists
    admin_cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (DB_NAME,)
    )
    db_exists = admin_cursor.fetchone()
    
    if not db_exists:
        print(f"\nCreating database '{DB_NAME}'...")
        admin_cursor.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(DB_NAME)
        ))
        print(f"[OK] Database '{DB_NAME}' created")
    else:
        print(f"\n[OK] Database '{DB_NAME}' already exists")
    
    # Check if user exists, drop if exists
    admin_cursor.execute(
        "SELECT 1 FROM pg_user WHERE usename = %s",
        (DB_USER,)
    )
    user_exists = admin_cursor.fetchone()
    
    if user_exists:
        print(f"User '{DB_USER}' exists. Recreating...")
        try:
            admin_cursor.execute(
                sql.SQL("DROP USER IF EXISTS {}").format(
                    sql.Identifier(DB_USER)
                )
            )
        except:
            pass
    
    # Create user
    print(f"Creating user '{DB_USER}'...")
    admin_cursor.execute(
        sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
            sql.Identifier(DB_USER)
        ),
        (DB_PASSWORD,)
    )
    print(f"[OK] User '{DB_USER}' created")
    
    # Grant privileges
    print(f"Granting privileges...")
    admin_cursor.execute(
        sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(DB_NAME),
            sql.Identifier(DB_USER)
        )
    )
    admin_cursor.execute(
        sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
            sql.Identifier(DB_NAME),
            sql.Identifier(DB_USER)
        )
    )
    print("[OK] Privileges granted")
    
    admin_cursor.close()
    admin_conn.close()
    
    # Test connection
    print(f"\nTesting connection with '{DB_USER}'...")
    test_conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    test_conn.close()
    print("[OK] Connection test successful!")
    
    print("\n" + "="*60)
    print("[OK] Database setup complete!")
    print("="*60)
    print(f"\nDatabase: {DB_NAME}")
    print(f"User: {DB_USER}")
    print(f"Password: {DB_PASSWORD}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print("\nYou can now start the backend server!")
    print()
    
except Exception as e:
    print(f"\n[X] Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


