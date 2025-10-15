from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from sqlalchemy.orm import Session
from ..models.section_model import SectionMaster
from ..schemas.section_schema import CreateSection

router = APIRouter(prefix = "/api/section", tags = ["Section"])

@router.post("/create")
def create_section(data: CreateSection, db:Session = Depends(get_db)):
    try:
        section_master = SectionMaster(
            section_name = data.section_name,
            section_desc = data.section_desc
        )

        db.add(section_master)
        db.commit()
        db.refresh(section_master)

        return {
            "status": status.HTTP_201_CREATED,
            "message": "Section created successfully",
            "data": {
                "name": section_master.section_name,
                "desc": section_master.section_desc 
            }
        }

    except HTTPException as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }
    
@router.get("/get_all")
def get_all_details(db:Session = Depends(get_db)):
    try:
        sections = db.query(SectionMaster).order_by(SectionMaster.created_at.desc()).all()
        return{
            "status": status.HTTP_200_OK,
            "message": "Found all sections",
            "data": sections
        }
    
    except HTTPException as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }
    