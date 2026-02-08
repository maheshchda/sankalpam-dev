"""
Migration script to update sankalpam_templates table
Changes from pdf_file_path to template_text (storing text directly in database)
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from app.config import settings

load_dotenv()

def migrate_template_table():
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as connection:
            # Check if template_text column exists
            result = connection.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='sankalpam_templates' AND column_name='template_text';"
            )).fetchone()

            if result:
                print("✅ Column 'template_text' already exists. Migration may have already been done.")
                return

            # Add template_text column
            print("Adding template_text column...")
            connection.execute(text(
                "ALTER TABLE sankalpam_templates ADD COLUMN template_text TEXT;"
            ))
            
            # Set default empty string for existing rows
            connection.execute(text(
                "UPDATE sankalpam_templates SET template_text = '' WHERE template_text IS NULL;"
            ))
            
            # Make it NOT NULL
            connection.execute(text(
                "ALTER TABLE sankalpam_templates ALTER COLUMN template_text SET NOT NULL;"
            ))
            
            connection.commit()
            print("✅ Column 'template_text' added successfully!")
            
            # Check if pdf_file_path exists and can be dropped
            pdf_result = connection.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='sankalpam_templates' AND column_name='pdf_file_path';"
            )).fetchone()
            
            if pdf_result:
                print("\n⚠️  Note: 'pdf_file_path' column still exists.")
                print("   After verifying your templates are working correctly, you can drop it:")
                print("   ALTER TABLE sankalpam_templates DROP COLUMN pdf_file_path;")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

if __name__ == "__main__":
    migrate_template_table()

