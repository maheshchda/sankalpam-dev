from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, FamilyMember
from app.schemas import FamilyMemberCreate, FamilyMemberResponse
from app.dependencies import get_current_user

router = APIRouter()

@router.post("/members", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_family_member(
    member_data: FamilyMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_member = FamilyMember(
        user_id=current_user.id,
        name=member_data.name,
        relation=member_data.relation,
        gender=member_data.gender,
        date_of_birth=member_data.date_of_birth,
        birth_time=member_data.birth_time,
        birth_city=member_data.birth_city,
        birth_state=member_data.birth_state,
        birth_country=member_data.birth_country
    )
    
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    
    return db_member

@router.get("/members", response_model=List[FamilyMemberResponse])
async def get_family_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    members = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).all()
    return members

@router.get("/members/{member_id}", response_model=FamilyMemberResponse)
async def get_family_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=404,
            detail="Family member not found"
        )
    
    return member

@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=404,
            detail="Family member not found"
        )
    
    db.delete(member)
    db.commit()
    
    return None

