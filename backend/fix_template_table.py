"""
Fix the sankalpam_templates table schema
Make pdf_file_path nullable since we're using template_text now
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from app.config import settings

load_dotenv()

def fix_template_table():
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as connection:
            # Check if pdf_file_path column exists and is NOT NULL
            result = connection.execute(text("""
                SELECT 
                    column_name, 
                    is_nullable,
                    data_type
                FROM information_schema.columns 
                WHERE table_name='sankalpam_templates' 
                AND column_name='pdf_file_path';
            """)).fetchone()
            
            if result:
                is_nullable = result[1]
                print(f"Current pdf_file_path column: nullable={is_nullable}")
                
                if is_nullable == 'NO':
                    print("Making pdf_file_path nullable...")
                    connection.execute(text("""
                        ALTER TABLE sankalpam_templates 
                        ALTER COLUMN pdf_file_path DROP NOT NULL;
                    """))
                    connection.commit()
                    print("✅ pdf_file_path is now nullable")
                else:
                    print("✅ pdf_file_path is already nullable")
            else:
                print("⚠️  pdf_file_path column doesn't exist (already removed?)")
            
            # Verify template_text exists and is NOT NULL
            result2 = connection.execute(text("""
                SELECT 
                    column_name, 
                    is_nullable
                FROM information_schema.columns 
                WHERE table_name='sankalpam_templates' 
                AND column_name='template_text';
            """)).fetchone()
            
            if result2:
                print(f"✅ template_text column exists: nullable={result2[1]}")
            else:
                print("❌ template_text column doesn't exist!")
                print("Running migration to add it...")
                connection.execute(text("""
                    ALTER TABLE sankalpam_templates ADD COLUMN template_text TEXT;
                """))
                connection.execute(text("""
                    UPDATE sankalpam_templates SET template_text = '' WHERE template_text IS NULL;
                """))
                connection.execute(text("""
                    ALTER TABLE sankalpam_templates ALTER COLUMN template_text SET NOT NULL;
                """))
                connection.commit()
                print("✅ template_text column added")
            
            print("\n✅ Table schema is now correct!")
            
    except Exception as e:
        print(f"❌ Error fixing table: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

if __name__ == "__main__":
    fix_template_table()

