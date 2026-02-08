from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from app.database import get_db
from app.models import User, Pooja, SankalpamTemplate, Language
from app.schemas import (
    PoojaCreate, PoojaResponse,
    SankalpamTemplateCreate, SankalpamTemplateResponse
)
from app.dependencies import get_admin_user
from app.services.template_service import identify_variables

router = APIRouter()

@router.post("/poojas", response_model=PoojaResponse, status_code=status.HTTP_201_CREATED)
async def create_pooja(
    pooja_data: PoojaCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    db_pooja = Pooja(
        name=pooja_data.name,
        description=pooja_data.description,
        duration_minutes=pooja_data.duration_minutes,
        created_by=current_user.id
    )
    
    db.add(db_pooja)
    db.commit()
    db.refresh(db_pooja)
    
    return db_pooja

@router.get("/poojas", response_model=List[PoojaResponse])
async def get_all_poojas(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    poojas = db.query(Pooja).all()
    return poojas

@router.put("/poojas/{pooja_id}", response_model=PoojaResponse)
async def update_pooja(
    pooja_id: int,
    pooja_data: PoojaCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    pooja = db.query(Pooja).filter(Pooja.id == pooja_id).first()
    
    if not pooja:
        raise HTTPException(
            status_code=404,
            detail="Pooja not found"
        )
    
    pooja.name = pooja_data.name
    pooja.description = pooja_data.description
    pooja.duration_minutes = pooja_data.duration_minutes
    
    db.commit()
    db.refresh(pooja)
    
    return pooja

@router.delete("/poojas/{pooja_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pooja(
    pooja_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    pooja = db.query(Pooja).filter(Pooja.id == pooja_id).first()
    
    if not pooja:
        raise HTTPException(
            status_code=404,
            detail="Pooja not found"
        )
    
    pooja.is_active = False
    db.commit()
    
    return None

# Template Management Endpoints
@router.post("/templates", response_model=SankalpamTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: SankalpamTemplateCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a Sankalpam template from text.
    The text should contain variables in {{variable_name}} format.
    
    Supports plain text, markdown, or any readable format.
    """
    
    if not template_data.template_text or not template_data.template_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Template text cannot be empty"
        )
    
    # Identify variables in the template
    variables = identify_variables(template_data.template_text)
    
    # Handle language - convert enum to string if needed
    language_value = template_data.language
    if isinstance(language_value, Language):
        language_value = language_value.value
    elif isinstance(language_value, str):
        # Validate it's a valid language
        try:
            language_value = Language(language_value.lower()).value
        except ValueError:
            language_value = Language.SANSKRIT.value
    
    # Create template record
    template = SankalpamTemplate(
        name=template_data.name,
        description=template_data.description,
        template_text=template_data.template_text,
        language=language_value,
        variables=json.dumps(variables),
        created_by=current_user.id,
        is_active=True
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template

@router.post("/templates/upload-file", response_model=SankalpamTemplateResponse, status_code=status.HTTP_201_CREATED)
async def upload_template_from_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    language: str = Form("sanskrit"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Upload a text file (txt, md, etc.) as a template.
    Supports any text-based format: .txt, .md, .text, etc.
    """
    
    # Validate file type - accept common text formats
    allowed_extensions = ['.txt', '.md', '.text', '.markdown']
    file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Only text files are supported: {', '.join(allowed_extensions)}"
        )
    
    # Read file contents
    try:
        content = await file.read()
        template_text = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded text"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading file: {str(e)}"
        )
    
    if not template_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Template file is empty"
        )
    
    # Identify variables in the template
    variables = identify_variables(template_text)
    
    # Create template record
    template = SankalpamTemplate(
        name=name,
        description=description,
        template_text=template_text,
        language=language,
        variables=json.dumps(variables),
        created_by=current_user.id,
        is_active=True
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template

@router.get("/templates", response_model=List[SankalpamTemplateResponse])
async def get_all_templates(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all Sankalpam templates"""
    templates = db.query(SankalpamTemplate).all()
    return templates

@router.get("/templates/{template_id}", response_model=SankalpamTemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get a specific template"""
    template = db.query(SankalpamTemplate).filter(SankalpamTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail="Template not found"
        )
    
    return template

@router.put("/templates/{template_id}", response_model=SankalpamTemplateResponse)
async def update_template(
    template_id: int,
    template_data: SankalpamTemplateCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update an existing Sankalpam template"""
    template = db.query(SankalpamTemplate).filter(SankalpamTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail="Template not found"
        )
    
    # Handle language - convert enum to string if needed
    language_value = template_data.language
    if isinstance(language_value, Language):
        language_value = language_value.value
    elif isinstance(language_value, str):
        # Validate it's a valid language
        try:
            language_value = Language(language_value.lower()).value
        except ValueError:
            language_value = Language.SANSKRIT.value
    
    template.name = template_data.name
    template.description = template_data.description
    template.template_text = template_data.template_text
    template.language = language_value
    template.variables = json.dumps(identify_variables(template_data.template_text))
    
    db.commit()
    db.refresh(template)
    
    return template

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a template"""
    template = db.query(SankalpamTemplate).filter(SankalpamTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail="Template not found"
        )
    
    # Delete template record
    db.delete(template)
    db.commit()
    
    return None

