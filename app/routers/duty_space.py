from fastapi import APIRouter, HTTPException, status, Depends
from ..database import get_db
from sqlalchemy.orm import Session
from ..models.inbond_model import InbondMaster
from ..models.exbond_model import ExbondChild, ExbondAdjustment
from ..schemas.duty_space_schema import CreateExbondAdjustment

router = APIRouter(prefix = "/api/duty_space", tags = ["DutySpace"])

# To get the total of inbond duty from "inbond_master" table and exbond duty from "exbond_child" table on the basis of "bi_number"
@router.get("/get_duty_total")
def get_duty_total(db:Session = Depends(get_db)):
    try:
        inbonds_master = db.query(InbondMaster).filter(InbondMaster.is_delete == 0).all()

        duty_list = []
        for inbond_master in inbonds_master:

            inbond_obj = {
                "type": "inbond",
                "total_duty_inbond": inbond_master.total_duty_inbond_amount_inr
            }

            exbonds_child = db.query(ExbondChild).filter(ExbondChild.inbond_master_id == inbond_master.id, ExbondChild.is_delete == 0).all()
            total_duty_exbond = 0
            for exbond_child in exbonds_child:
                total_duty_exbond += exbond_child.duty_exbond_amount_inr

            exbond_obj = {
                "type": "exbond",
                "total_duty_exbond": total_duty_exbond
            }

            obj = {
                "id": inbond_master.id,
                "bi_number": inbond_master.bi_number,
                "inbond": inbond_obj,
                "exbond": exbond_obj
            }
            duty_list.append(obj)

        return{
            "status": status.HTTP_200_OK,
            "message": "All inbond duty totals found",
            "data": duty_list
        }
    
    except HTTPException as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }
    

@router.post("/create_adjustment")
def create_adjustment(data: CreateExbondAdjustment, db:Session = Depends(get_db)):
    try:
        adjustment = ExbondAdjustment(
            inbond_master_id = data.inbond_master_id,
            adjustment_amount_inr = data.adjustment_amount_inr,
            date_of_adjustment = data.date_of_adjustment,
            type = data.type
        )

        db.add(adjustment)
        db.commit()
        db.refresh(adjustment)

        return {
            "status": status.HTTP_201_CREATED,
            "message": "Adjustment entry created successfully",
            "data": {
                "adjustment_amount": adjustment.adjustment_amount_inr,
                "date": adjustment.date_of_adjustment,
                "type": adjustment.type
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
        exbond_adjustments = db.query(ExbondAdjustment).all()

        adjustment_list = []
        for adjustment in exbond_adjustments:
            inbond = db.query(InbondMaster).filter(InbondMaster.id == adjustment.inbond_master_id).first()
            obj = {
                "inbond_master_id": adjustment.inbond_master_id,
                "inbond_bi_number": inbond.bi_number,
                "adjustment_amount": adjustment.adjustment_amount_inr,
                "date_of_adjustment": adjustment.date_of_adjustment 
            }
            adjustment_list.append(obj)

        return {
            "status": status.HTTP_200_OK,
            "message": "All exbond adjustment found",
            "data": adjustment_list
        }
    except HTTPException as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal Server Error",
            "detail": e
        }