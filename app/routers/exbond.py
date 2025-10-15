from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database import get_db
from sqlalchemy.orm import Session
from ..models.exbond_model import ExbondChild, ExbondMaster
from ..schemas.exbond_schema import CreateExbondMaster
from ..models.section_model import SectionMaster
from ..models.material_model import MaterialMaster
from ..models.inbond_model import InbondMaster, InbondChild
from ..models.customer_model import CustomerMaster

router = APIRouter(prefix = "/api/exbond", tags = ["Exbond"])

'''
Create entry in the "exbond_master" and "exbond_child" table
'''
@router.post("/create")
def create_exbond(data: CreateExbondMaster, db:Session = Depends(get_db)):
    try:
        latest = db.query(ExbondMaster).order_by(ExbondMaster.exbond_id.desc()).first()
        next_exbond_id = 1001 if not latest or not latest.exbond_id else latest.exbond_id + 1

        exbond_master = ExbondMaster(
            exbond_id = next_exbond_id,
            total_duty_exbond_amount_inr = data.total_duty_exbond_amount_inr,
            total_weight = data.total_weight,
            total_invoice_amount_inr = data.total_invoice_amount_inr,
            total_dispatch_weight = data.total_dispatch_weight
        )
        db.add(exbond_master)
        db.commit()
        db.refresh(exbond_master)

        for exbondchild in data.exbondchild:
            exbond_child = ExbondChild(
                exbond_master_id = exbond_master.id,
                inbond_master_id = exbondchild.inbond_master_id,
                section_master_id = exbondchild.section_master_id,
                material_master_id = exbondchild.material_master_id,
                customer_master_id = exbondchild.customer_master_id,
                be_number = exbondchild.be_number,
                be_date = exbondchild.be_date,
                type = exbondchild.type,
                resultant = exbondchild.resultant,
                duty_exbond_amount_inr = exbondchild.duty_exbond_amount_inr,
                dollar_inr = exbondchild.dollar_inr,
                rate = exbondchild.rate,
                weight = exbondchild.weight,
                invoice_amount_inr = exbondchild.invoice_amount_inr,
                dispatch_date = exbondchild.dispatch_date,
                dispatch_weight = exbondchild.dipspatch_weight,
                truck_number = exbondchild.truck_number
            )
            db.add(exbond_child)
        db.commit()
        return{
            "status": status.HTTP_201_CREATED,
            "message": "Exbond entry created successfully",
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
To get all the details from the "exbond_master" and "exbond_child"
'''
@router.get("/get_all")
def get_all_details(db:Session = Depends(get_db)):
    try:
        exbonds_master = db.query(ExbondMaster).order_by(ExbondMaster.created_at.desc()).all()

        master_list = []
        
        for exbond_master in exbonds_master:
            master_id = exbond_master.id
            child_list = []
            exbonds_child = db.query(ExbondChild).filter(ExbondChild.exbond_master_id == master_id).all()
            for exbond_child in exbonds_child:
                section = db.query(SectionMaster).filter(SectionMaster.id == exbond_child.section_master_id).first()
                material = db.query(MaterialMaster).filter(MaterialMaster.id == exbond_child.material_master_id).first()
                inbond = db.query(InbondMaster).filter(InbondMaster.id == exbond_child.inbond_master_id).first()
                customer = db.query(CustomerMaster).filter(CustomerMaster.id == exbond_child.customer_master_id).first()

                child_obj = {
                    "id": exbond_child.id,
                    "bi_number": inbond.bi_number,
                    "be_number": exbond_child.be_number,
                    "be_date": exbond_child.be_date,
                    "section_master_id": exbond_child.section_master_id,
                    "section_name": section.section_name,
                    "type": exbond_child.type,
                    "resultant": exbond_child.resultant,
                    "material_master_id": exbond_child.material_master_id,
                    "material_name": material.name,
                    "duty_exbond_amount_inr": exbond_child.duty_exbond_amount_inr,
                    "dollar_inr": exbond_child.dollar_inr,
                    "rate": exbond_child.rate,
                    "weight": exbond_child.weight,
                    "invoice_amount_inr": exbond_child.invoice_amount_inr,
                    "customer_name": customer.name,
                    "dispatch_date": exbond_child.dispatch_date,
                    "dispatch_weight": exbond_child.dispatch_weight,
                    "truck_number": exbond_child.truck_number
                }
                child_list.append(child_obj)
            
            master_obj = {
                "id": master_id,
                "exbond_id": exbond_master.exbond_id,
                "child": child_list,
                "total_duty_exbond_amount_inr": exbond_master.total_duty_exbond_amount_inr,
                "total_weight": exbond_master.total_weight,
                "total_invoice_amount_inr": exbond_master.total_invoice_amount_inr,
                "total_dispatch_weight": exbond_master.total_dispatch_weight,
                "created_at": exbond_master.created_at
            }
            master_list.append(master_obj)
        
        return {
            "status": status.HTTP_200_OK,
            "message": "All exbond details found",
            "data": master_list
        }
            
    except HTTPException as e:
        db.rollback()
        return{
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }
    

@router.get("/get_material_inbond_bedate")
def get_material_inbond_bedate_by_id(
    inbond_master_id: int = Query(..., description = "Inbond Master ID"), 
    db:Session = Depends(get_db)
):
    try:
        inbonds_child = db.query(InbondChild).filter(InbondChild.inbond_master_id == inbond_master_id).all()
        inbond_master = db.query(InbondMaster).filter(InbondMaster.id == inbond_master_id).first()

        list = []
        for inbond_child in inbonds_child:
            material = db.query(MaterialMaster).filter(MaterialMaster.id == inbond_child.material_master_id).first()
            obj = {
                "id": inbond_child.id,
                "material_master_id": inbond_child.material_master_id,
                "material_name": material.name,
                "inbond_be_date": inbond_master.be_date
            }

            list.append(obj)

        return {
            "status": status.HTTP_200_OK,
            "message": "All material name and inbond be date found",
            "data": list
        }

    
    except HTTPException as e:
        db.rollback()
        return{
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }


@router.get("/get_weight_duty")
def get_weight_and_duty(
    material_master_id: int = Query(..., description="Material Master ID"),
    inbond_master_id: int = Query(..., description="Inbond Master ID"),
    db: Session = Depends(get_db)
):
    try:
        inbond_child = db.query(InbondChild).filter(InbondChild.material_master_id == material_master_id, InbondChild.inbond_master_id == inbond_master_id).first()

        inbond_obj = {
            "inbond_weight": inbond_child.weight,
            "duty_inbond_amount_inr": inbond_child.duty_inbond_amount_inr
        }

        exbonds_child = db.query(ExbondChild).filter(ExbondChild.material_master_id == material_master_id, ExbondChild.inbond_master_id == inbond_master_id).all()

        exbond_weight_total = 0
        duty_exbond_amount_inr_total = 0
        for exbond_child in exbonds_child:
            exbond_weight_total += exbond_child.weight
            duty_exbond_amount_inr_total += exbond_child.duty_exbond_amount_inr

        exbond_obj = {
            "exbond_weight": exbond_weight_total,
            "duty_exbond_amount_inr": duty_exbond_amount_inr_total
        }

        data = {
            "material_master_id": material_master_id,
            "inbond_master_id": inbond_master_id,
            "inbond": inbond_obj,
            "exbond": exbond_obj
        }

        return {
            "status": status.HTTP_200_OK,
            "message": "Total weight and duty details from inbond and exbond found",
            "data": data
        }

    except HTTPException as e:
        db.rollback()
        return{
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }