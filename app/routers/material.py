from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from sqlalchemy.orm import Session
from ..models.material_model import MaterialMaster
from ..schemas.material_schema import CreateMaterial, UpdateMaterial
from datetime import datetime

router = APIRouter(prefix = "/api/material", tags = ["Material"])


'''
Create material entry in "material_master" table
'''
@router.post("/create")
def create_material(data: CreateMaterial, db:Session = Depends(get_db)):
    try:
        material_master = MaterialMaster(
            name = data.name,
            short_code = data.short_code,
            hsn_code = data.hsn_code,
            basic_duty_pr = data.basic_duty_pr,
            social_duty_pr = data.social_duty_pr,
            igst_pr = data.igst_pr
        )

        db.add(material_master)
        db.commit()
        db.refresh(material_master)

        return{
            "status": status.HTTP_201_CREATED,
            "message": "Material created successfully",
            "data": {
                "name": material_master.name,
                "short_code": material_master.short_code,
                "hsn_code": material_master.hsn_code,
                "basic_duty_pr": material_master.basic_duty_pr,
                "social_duty_pr": material_master.social_duty_pr,
                "igst_pr": material_master.igst_pr
            }
        }
    except HTTPException as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }
    

'''
Get all the details of the "material_master" table
'''
@router.get("/get_all")
def get_all_details(db:Session = Depends(get_db)):
    try:
        materials = db.query(MaterialMaster).filter(MaterialMaster.is_delete == 0).order_by(MaterialMaster.created_at.desc()).all()
        return {
            "status": status.HTTP_200_OK,
            "message": "Found all materials",
            "data": materials
        }
    
    except HTTPException as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }
    

'''
to fetch the material name from "material_master" table
'''
@router.get("/name")
def get_section_name(db:Session = Depends(get_db)):
    try:
        materials = db.query(MaterialMaster).filter(MaterialMaster.is_delete == 0).order_by(MaterialMaster.created_at.desc()).all()
        material_list = []
        for material in materials:
            obj = {
                "material_id": material.id,
                "material_name": material.name
            }
            material_list.append(obj)
        
        return{
            "status": status.HTTP_200_OK,
            "message": "material name found",
            "data": material_list
        }
    
    except HTTPException as e:
        db.rollback()
        return{
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }
    

@router.put("/soft_delete/{material_id}")
def soft_delete_entry(material_id: int, db:Session = Depends(get_db)):
    try:
        material = db.query(MaterialMaster).filter(MaterialMaster.id == material_id).first()

        if not material:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Material not found"
            )
        
        if material.is_delete == True:
            return {
                "status": status.HTTP_204_NO_CONTENT,
                "message": "Material already deleted"
            }
        
        material.is_delete = True
        db.commit()

        return {
            "status": status.HTTP_200_OK,
            "message": "Material deleted succesfully"
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
    

@router.put("/update/{material_master_id}")
def update_material_entry(material_master_id: int, data: UpdateMaterial, db:Session = Depends(get_db)):
    try:
        material = db.query(MaterialMaster).filter(MaterialMaster.id == material_master_id, MaterialMaster.is_delete == 0).first()

        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found or has been deleted"
            )
        
        if data.name is not None:
            material.name = data.name
        if data.short_code is not None:
            material.short_code = data.short_code
        if data.hsn_code is not None:
            material.hsn_code = data.hsn_code
        if data.basic_duty_pr is not None:
            material.basic_duty_pr = data.basic_duty_pr
        if data.social_duty_pr is not None:
            material.social_duty_pr = data.social_duty_pr
        if data.igst_pr is not None:
            material.igst_pr = data.igst_pr
        
        material.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(material)

        return {
            "status": status.HTTP_200_OK,
            "message": "Material updated successfully",
            "data": material
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