from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from sqlalchemy.orm import Session
from ..models.section_model import SectionMaster
from ..schemas.section_schema import CreateSection, UpdateSection
from datetime import datetime

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
        sections = db.query(SectionMaster).filter(SectionMaster.is_delete == 0).order_by(SectionMaster.created_at.desc()).all()
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
    

@router.put("/soft_delete/{section_id}")
def soft_delete_entry(section_id: int, db:Session = Depends(get_db)):
    try:
        section = db.query(SectionMaster).filter(SectionMaster.id == section_id).first()

        if not section:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Section not found"
            )
        
        if section.is_delete == True:
            return {
                "status": status.HTTP_204_NO_CONTENT,
                "message": "Section already deleted"
            }
        
        section.is_delete = True
        db.commit()

        return {
            "status": status.HTTP_200_OK,
            "message": "Section deleted succesfully"
        }
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }
    
@router.put("/update/{section_master_id}")
def update_section_entry(section_master_id: int, data: UpdateSection ,db:Session = Depends(get_db)):
    try:
        section = db.query(SectionMaster).filter(SectionMaster.id == section_master_id, SectionMaster.is_delete == 0).first()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found or has been deleted"
            )

        # Update only the provided fields
        if data.section_name is not None:
            section.section_name = data.section_name
        if data.section_desc is not None:
            section.section_desc = data.section_desc
        
        section.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(section)

        return {
            "status": status.HTTP_200_OK,
            "message": "Section updated successfully",
            "data": section
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }