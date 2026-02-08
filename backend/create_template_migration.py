"""
Script to manually create the sankalpam_templates table
Run this if Alembic migration doesn't work
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from app.config import settings

load_dotenv()

def create_templates_table():
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as connection:
            # Check if table exists
            result = connection.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='sankalpam_templates');"
            )).fetchone()

            if result and result[0]:
                print("Table 'sankalpam_templates' already exists.")
                return

            # Create table
            connection.execute(text("""
                CREATE TABLE sankalpam_templates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    pdf_file_path VARCHAR(500) NOT NULL,
                    language VARCHAR(50) NOT NULL DEFAULT 'sanskrit',
                    variables TEXT,
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE
                );
            """))
            
            # Create index
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sankalpam_templates_created_by 
                ON sankalpam_templates(created_by);
            """))
            
            connection.commit()
            print("Table 'sankalpam_templates' created successfully!")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    create_templates_table()

