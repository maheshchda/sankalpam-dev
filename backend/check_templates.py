"""
Quick script to check templates in database
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app.models import SankalpamTemplate

db = SessionLocal()
try:
    templates = db.query(SankalpamTemplate).filter(
        SankalpamTemplate.is_active == True
    ).all()
    
    print(f"Found {len(templates)} active templates:")
    for t in templates:
        print(f"  - ID: {t.id}, Name: {t.name}, Language: {t.language}, Active: {t.is_active}")
        
    if len(templates) == 0:
        print("\nNo active templates found!")
        all_templates = db.query(SankalpamTemplate).all()
        print(f"Total templates (including inactive): {len(all_templates)}")
        for t in all_templates:
            print(f"  - ID: {t.id}, Name: {t.name}, Active: {t.is_active}")
finally:
    db.close()

