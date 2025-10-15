from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from sqlalchemy.orm import Session
from ..models.material_model import MaterialMaster
from ..schemas.material_schema import CreateMaterial

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
        materials = db.query(MaterialMaster).order_by(MaterialMaster.created_at.desc()).all()
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
        materials = db.query(MaterialMaster).order_by(MaterialMaster.created_at.desc()).all()
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