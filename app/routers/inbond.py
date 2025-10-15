from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from sqlalchemy.orm import Session
from ..schemas.inbond_schema import CreateInbond
from ..auth_utils import get_current_user
from ..models.inbond_model import InbondMaster, InbondChild
from ..models.material_model import MaterialMaster

router = APIRouter(prefix = "/api/inbond", tags = ["Inbond"])

"""
Sample for authorization
- only user with role as admin will be allowed to access this api
"""
@router.get("/hii")
def greetings(current_user: dict=Depends(get_current_user)):
    if current_user.get("user_type") == "admin":
        return("hiii")
    else:
        return("not admin")


'''
Create entry in the "inbond_master" and "inbond_child" table
'''    
@router.post("/create")
def create_inbond(data: CreateInbond, db:Session=Depends(get_db)):
    try:
        inbond_master = InbondMaster(
            bi_number = data.bi_number,
            be_number = data.be_number,
            be_date = data.be_date,
            inbond_date = data.inbond_date,
            total_duty_inbond_amount_inr = data.total_duty_inbond_amount_inr,
            total_weight = data.total_weight,
            total_assessment_amount_inr = data.total_assessment_amount_inr,
            total_material_amount_usd = data.total_material_amount_usd
        )
        db.add(inbond_master)
        db.commit()
        db.refresh(inbond_master)

        for inbondchild in data.inbondchild:
            inbond_child = InbondChild(
                inbond_master_id = inbond_master.id,
                material_master_id = inbondchild.material_master_id,
                duty_inbond_amount_inr = inbondchild.duty_inbond_amount_inr,
                weight = inbondchild.weight,
                invoice_amount_usd = inbondchild.invoice_amount_usd,
                assessment_amount_inr = inbondchild.assessment_amount_inr,
                dollar_inr = inbondchild.dollar_inr,
                price = inbondchild.price,
                material_amount_usd = inbondchild.material_amount_usd
            )
            db.add(inbond_child)
        db.commit()
        return{
            "status": status.HTTP_201_CREATED,
            "message": "Inbond entry created successfully",
            "data":{}
        }

    except Exception as e:
        db.rollback()
        return{
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }


'''
To get all the details from the "inbond_master" and "inbond_child"
'''
@router.get("/get_all")
def get_all_details(db:Session = Depends(get_db)):
    try:
        inbonds_master = db.query(InbondMaster).order_by(InbondMaster.created_at.desc()).all()

        master_list = []
        
        for inbond_master in inbonds_master:
            master_id = inbond_master.id
            child_list = []
            inbonds_child = db.query(InbondChild).filter(InbondChild.inbond_master_id == master_id).all()
            for inbond_child in inbonds_child:
                material = db.query(MaterialMaster).filter(MaterialMaster.id == inbond_child.material_master_id).first()
                child_obj = {
                    "id": inbond_child.id,
                    "material_master_id": inbond_child.material_master_id,
                    "material_name": material.name,
                    "duty_inbond_amount_inr": inbond_child.duty_inbond_amount_inr,
                    "weight": inbond_child.weight,
                    "invoice_amount_usd": inbond_child.invoice_amount_usd,
                    "assessment_amount_inr": inbond_child.assessment_amount_inr,
                    "dollar_inr": inbond_child.dollar_inr,
                    "price": inbond_child.price,
                    "material_amount_usd": inbond_child.material_amount_usd 
                }
                child_list.append(child_obj)
            
            master_obj = {
                "id": master_id,
                "bi_number": inbond_master.bi_number,
                "be_number": inbond_master.be_number,
                "be_date": inbond_master.be_date,
                "inbond_date": inbond_master.inbond_date,
                "child": child_list,
                "total_duty_inbond_amount_inr": inbond_master.total_duty_inbond_amount_inr,
                "total_weight": inbond_master.total_weight,
                "total_assessment_amount_inr": inbond_master.total_assessment_amount_inr,
                "total_material_amount_usd": inbond_master.total_material_amount_usd
            }
            master_list.append(master_obj)
        
        return {
            "status": status.HTTP_200_OK,
            "message": "All inbond details found",
            "data": master_list
        }
            
    except HTTPException as e:
        db.rollback()
        return{
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }


'''
Get all the bi_numbers from the "inbond_master" table
'''
@router.get("/get_binumber")
def get_all_binumber(db:Session = Depends(get_db)):
    inbonds = db.query(InbondMaster).order_by(InbondMaster.created_at.desc()).all()
    binumber_list = []

    for inbond in inbonds:
        obj = {
            "id": inbond.id,
            "binumber": inbond.bi_number
        }
        binumber_list.append(obj)
    
    return {
        "status": status.HTTP_200_OK,
        "message": "All binumbers found",
        "data": binumber_list
    }