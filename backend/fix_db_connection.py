#!/usr/bin/env python3
"""
Fix database connection for Sankalpam backend
This script will create the database user and database if they don't exist
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

def main():
    print("\n" + "="*60)
    print("  Fix Database Connection for Sankalpam")
    print("="*60)
    print()
    
    # Get postgres admin password
    print("To fix the database connection, we need to connect as the")
    print("PostgreSQL admin user (usually 'postgres').")
    print()
    admin_password = getpass.getpass("Enter password for PostgreSQL 'postgres' user: ")
    print()
    
    try:
        # Connect as postgres admin
        print(f"Connecting to PostgreSQL as 'postgres'...")
        admin_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user="postgres",
            password=admin_password,
            database="postgres"
        )
        admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        admin_cursor = admin_conn.cursor()
        
        print("✓ Connected to PostgreSQL")
        print()
        
        # Check if user exists
        admin_cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (DB_USER,)
        )
        user_exists = admin_cursor.fetchone()
        
        if user_exists:
            print(f"User '{DB_USER}' already exists. Updating password...")
            admin_cursor.execute(
                sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                    sql.Identifier(DB_USER)
                ),
                (DB_PASSWORD,)
            )
            print(f"✓ Password updated for user '{DB_USER}'")
        else:
            print(f"Creating user '{DB_USER}'...")
            admin_cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                    sql.Identifier(DB_USER)
                ),
                (DB_PASSWORD,)
            )
            print(f"✓ User '{DB_USER}' created")
        
        # Check if database exists
        admin_cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        db_exists = admin_cursor.fetchone()
        
        if db_exists:
            print(f"Database '{DB_NAME}' already exists")
        else:
            print(f"Creating database '{DB_NAME}'...")
            admin_cursor.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(DB_NAME),
                    sql.Identifier(DB_USER)
                )
            )
            print(f"✓ Database '{DB_NAME}' created")
        
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
        print()
        print(f"Testing connection with '{DB_USER}'...")
        test_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        test_conn.close()
        print("✓ Connection test successful!")
        
        print()
        print("="*60)
        print("✓ Database connection fixed!")
        print("="*60)
        print()
        print("You can now start the backend server:")
        print("  cd backend")
        print("  .\\venv\\Scripts\\Activate.ps1")
        print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print()
        
    except psycopg2.OperationalError as e:
        print(f"\n✗ Error connecting to PostgreSQL: {e}")
        print()
        print("Possible issues:")
        print("  1. Wrong postgres password")
        print("  2. PostgreSQL is not running")
        print("  3. PostgreSQL is on a different port")
        print()
        print("To check if PostgreSQL is running:")
        print("  Get-Service | Where-Object {$_.Name -like '*postgres*'}")
        print()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
