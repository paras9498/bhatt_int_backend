from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date
from ..models.inbond_model import InbondMaster, InbondChild
from ..models.exbond_model import ExbondMaster, ExbondChild
from ..models.material_model import MaterialMaster
from ..models.dispatch_model import DispatchChild

router = APIRouter(prefix = "/api/reports", tags = ["Reports"])

@router.get("/total_quantity_inbond_exbond")
def get_total_quantity_inbond_exbond(
    db:Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="Start date for filtering be_date"),
    end_date: Optional[date] = Query(None, description="End date for filtering be_date")
):
    try:
        inbond_query = db.query(InbondMaster).filter(InbondMaster.is_delete == 0)

        if start_date and end_date:
            inbond_query = inbond_query.filter(InbondMaster.be_date.between(start_date, end_date))
        elif start_date:
            inbond_query = inbond_query.filter(InbondMaster.be_date >= start_date)
        elif end_date:
            inbond_query = inbond_query.filter(InbondMaster.be_date <= end_date)

        inbonds_master = inbond_query.all()

        exbond_query = db.query(ExbondChild).filter(ExbondChild.is_delete == 0)

        if start_date and end_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date.between(start_date, end_date))
        elif start_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date >= start_date)
        elif end_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date <= end_date)

        exbonds_child = exbond_query.all()

        total_weight_inbond = 0
        total_duty_inbond = 0
        for inbond_master in inbonds_master:
            total_weight_inbond += inbond_master.total_weight
            total_duty_inbond += inbond_master.total_duty_inbond_amount_inr

        total_weight_exbond = 0
        total_duty_exbond = 0
        for exbond_child in exbonds_child:
            total_weight_exbond += exbond_child.weight
            total_duty_exbond += exbond_child.duty_exbond_amount_inr

        return {
            "status": status.HTTP_200_OK,
            "message": "Total quantities found",
            "data": {
                "inbond_data": {
                    "total_weight_inbond": total_weight_inbond,
                    "total_duty_inbond": total_duty_inbond
                },
                "exbond_data": {
                    "total_weight_exbond": total_weight_exbond,
                    "total_duty_exbond": total_duty_exbond
                },
                "difference": {
                    "difference_weight": total_weight_inbond - total_weight_exbond,
                    "difference_duty": total_duty_inbond - total_duty_exbond
                }
            }
        }

    except Exception as e:
        db.rollback()
        return{
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": str(e)
        }


@router.get("/total_quantity_inbond_exbond_materialwise")
def get_total_quantity_inbond_exbond_materialwise(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="Start date for filtering be_date"),
    end_date: Optional[date] = Query(None, description="End date for filtering be_date")
):
    try:
        # ---------------------------------------------------------
        # 1️⃣ INBOND QUERY (Filter using InbondMaster.be_date)
        # ---------------------------------------------------------
        inbond_query = (
            db.query(
                InbondChild.material_master_id.label("material_master_id"),
                func.sum(InbondChild.weight).label("total_weight_inbond"),
                func.sum(InbondChild.duty_inbond_amount_inr).label("total_duty_inbond")
            )
            .join(InbondMaster, InbondMaster.id == InbondChild.inbond_master_id)
            .filter(InbondChild.is_delete == 0, InbondMaster.is_delete == 0)
        )

        # Apply date filter
        if start_date and end_date:
            inbond_query = inbond_query.filter(InbondMaster.be_date.between(start_date, end_date))
        elif start_date:
            inbond_query = inbond_query.filter(InbondMaster.be_date >= start_date)
        elif end_date:
            inbond_query = inbond_query.filter(InbondMaster.be_date <= end_date)

        inbonds_child = inbond_query.group_by(InbondChild.material_master_id).all()

        # ---------------------------------------------------------
        # 2️⃣ EXBOND QUERY (Filter using ExbondChild.be_date)
        # ---------------------------------------------------------
        exbond_query = (
            db.query(
                ExbondChild.material_master_id.label("material_master_id"),
                func.sum(ExbondChild.weight).label("total_weight_exbond"),
                func.sum(ExbondChild.duty_exbond_amount_inr).label("total_duty_exbond")
            )
            .filter(ExbondChild.is_delete == 0)
        )

        # Apply date filter (ExbondChild has be_date directly)
        if start_date and end_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date.between(start_date, end_date))
        elif start_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date >= start_date)
        elif end_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date <= end_date)

        exbonds_child = exbond_query.group_by(ExbondChild.material_master_id).all()

        # ✅ Create dicts keyed by material_master_id
        inbond_dict = {
            item.material_master_id: {
                "total_weight_inbond": item.total_weight_inbond or 0,
                "total_duty_inbond": item.total_duty_inbond or 0,
            }
            for item in inbonds_child
        }

        exbond_dict = {
            item.material_master_id: {
                "total_weight_exbond": item.total_weight_exbond or 0,
                "total_duty_exbond": item.total_duty_exbond or 0,
            }
            for item in exbonds_child
        }

        # ✅ Get all unique material IDs
        all_material_ids = set(inbond_dict.keys()) | set(exbond_dict.keys())

        # ✅ Combine data
        data = []
        for material_id in all_material_ids:
            material = db.query(MaterialMaster).filter(MaterialMaster.id == material_id, MaterialMaster.is_delete == 0).first()

            inbond_data = inbond_dict.get(material_id, {"total_weight_inbond": 0, "total_duty_inbond": 0})
            exbond_data = exbond_dict.get(material_id, {"total_weight_exbond": 0, "total_duty_exbond": 0})

            material_obj = {
                "material_master_id": material_id,
                "material_name": material.name,
                "material_short_code": material.short_code,
                "data":{
                    "inbond_data": inbond_data,
                    "exbond_data": exbond_data,
                    "difference": {
                        "difference_weight": inbond_data["total_weight_inbond"] - exbond_data["total_weight_exbond"],
                        "difference_duty": inbond_data["total_duty_inbond"] - exbond_data["total_duty_exbond"],
                    },
                }
            }
            data.append(material_obj)

        return {
            "status": status.HTTP_200_OK,
            "message": "Material-wise totals found",
            "data": data,
        }

    except Exception as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": str(e),
        }
    

@router.get("/balance_duty_exbond")
def get_total_quantity_inbond_exbond_binumberwise(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="Start date for filtering be_date"),
    end_date: Optional[date] = Query(None, description="End date for filtering be_date")
):
    try:
        # -----------------------------
        # 1️⃣ INBOND CHILD TOTALS (Filtered by InbondMaster.be_date)
        # -----------------------------
        inbond_query = (
            db.query(
                InbondChild.inbond_master_id.label("inbond_master_id"),
                func.sum(InbondChild.weight).label("total_weight_inbond"),
                func.sum(InbondChild.duty_inbond_amount_inr).label("total_duty_inbond_amount")
            )
            .join(InbondMaster, InbondMaster.id == InbondChild.inbond_master_id)
            .filter(InbondChild.is_delete == 0, InbondMaster.is_delete == 0)
        )

        # Apply date filter
        if start_date and end_date:
            inbond_query = inbond_query.filter(InbondMaster.be_date.between(start_date, end_date))
        elif start_date:
            inbond_query = inbond_query.filter(InbondMaster.be_date >= start_date)
        elif end_date:
            inbond_query = inbond_query.filter(InbondMaster.be_date <= end_date)

        inbonds_child = inbond_query.group_by(InbondChild.inbond_master_id).all()

        # -----------------------------
        # 2️⃣ EXBOND CHILD TOTALS (Filtered by ExbondChild.be_date)
        # -----------------------------
        exbond_query = (
            db.query(
                ExbondChild.inbond_master_id.label("inbond_master_id"),
                func.sum(ExbondChild.weight).label("total_weight_exbond"),
                func.sum(ExbondChild.duty_exbond_amount_inr).label("total_duty_exbond_amount")
            )
            .filter(ExbondChild.is_delete == 0)
        )

        # Apply date filter
        if start_date and end_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date.between(start_date, end_date))
        elif start_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date >= start_date)
        elif end_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date <= end_date)

        exbonds_child = exbond_query.group_by(ExbondChild.inbond_master_id).all()

        # ✅ Create dicts keyed by material_master_id
        inbond_dict = {
            item.inbond_master_id: {
                "total_weight_inbond": item.total_weight_inbond or 0,
                "total_duty_inbond": item.total_duty_inbond_amount or 0
            }
            for item in inbonds_child
        }

        exbond_dict = {
            item.inbond_master_id: {
                "total_weight_exbond": item.total_weight_exbond or 0,
                "total_duty_exbond": item.total_duty_exbond_amount or 0
            }
            for item in exbonds_child
        }

        # ✅ Get all unique material IDs
        all_inbond_master_ids = set(inbond_dict.keys()) | set(exbond_dict.keys())

        # ✅ Combine data
        data = []
        for inbond_master_id in all_inbond_master_ids:
            inbond = db.query(InbondMaster).filter(InbondMaster.id == inbond_master_id, InbondMaster.is_delete == 0).first()
            
            inbond_data = inbond_dict.get(inbond_master_id, {"total_weight_inbond": 0, "total_duty_inbond": 0})
            exbond_data = exbond_dict.get(inbond_master_id, {"total_weight_exbond": 0, "total_duty_exbond": 0})

            material_obj = {
                "inbond_master_id": inbond_master_id,
                "inbond_bi_number": inbond.bi_number,
                "data":{
                    "inbond_data": inbond_data,
                    "exbond_data": exbond_data,
                    "difference": {
                        "difference_weight": inbond_data["total_weight_inbond"] - exbond_data["total_weight_exbond"],
                        "difference_duty": inbond_data["total_duty_inbond"] - exbond_data["total_duty_exbond"]
                    },
                }
            }
            data.append(material_obj)

        return {
            "status": status.HTTP_200_OK,
            "message": "Binumber-wise totals found",
            "data": data,
        }

    except Exception as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": str(e),
        }
    

@router.get("/balance_duty_dispatch")
def get_total_quantity_inbond_exbond_benumberwise(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="Start date for filtering be_date"),
    end_date: Optional[date] = Query(None, description="End date for filtering be_date")
):
    try:
         # ------------------------------------------------------------
        # 1️⃣ TOTAL EXBOND WEIGHT FILTERED BY ExbondChild.be_date
        # ------------------------------------------------------------
        exbond_query = (
            db.query(
                ExbondChild.inbond_master_id.label("inbond_master_id"),
                func.sum(ExbondChild.weight).label("total_exbond_weight")
            )
            .filter(ExbondChild.is_delete == 0)
        )

        # Apply date filter on EXBOND
        if start_date and end_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date.between(start_date, end_date))
        if start_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date >= start_date)
        if end_date:
            exbond_query = exbond_query.filter(ExbondChild.be_date <= end_date)

        exbond_data = exbond_query.group_by(ExbondChild.inbond_master_id).all()

        exbond_dict = {
            row.inbond_master_id: row.total_exbond_weight or 0
            for row in exbond_data
        }

        # ------------------------------------------------------------
        # 2️⃣ TOTAL DISPATCH WEIGHT FILTERED BY DispatchChild.dispatch_date
        # JOIN dispatch_child → exbond_child → inbond_master_id
        # ------------------------------------------------------------
        dispatch_query = (
            db.query(
                ExbondChild.inbond_master_id.label("inbond_master_id"),
                func.sum(DispatchChild.dispatch_weight).label("total_dispatch_weight")
            )
            .join(ExbondChild, ExbondChild.id == DispatchChild.exbond_child_id)
            .filter(DispatchChild.is_delete == 0, ExbondChild.is_delete == 0)
        )

        # Apply date filter on DISPATCH
        if start_date and end_date:
            exbond_query = exbond_query.filter(DispatchChild.dispatch_date.between(start_date, end_date))
        if start_date:
            dispatch_query = dispatch_query.filter(DispatchChild.dispatch_date >= start_date)
        if end_date:
            dispatch_query = dispatch_query.filter(DispatchChild.dispatch_date <= end_date)

        dispatch_data = dispatch_query.group_by(ExbondChild.inbond_master_id).all()


        dispatch_dict = {
            row.inbond_master_id: row.total_dispatch_weight or 0
            for row in dispatch_data
        }

        # ------------------------------------------------------------
        # 3️⃣ MERGE BOTH BY UNIQUE INBOND_MASTER_IDS
        # ------------------------------------------------------------
        all_ids = set(exbond_dict.keys()) | set(dispatch_dict.keys())
        data = []

        for inbond_id in all_ids:
            inbond_master = db.query(InbondMaster).filter(InbondMaster.id == inbond_id, InbondMaster.is_delete == 0).first()
            exbond_data = exbond_dict.get(inbond_id, 0)
            dispatch_data = dispatch_dict.get(inbond_id, 0)

            master_obj = {
                "inbond_master_id": inbond_id,
                "inbond_be_number": inbond_master.be_number,
                "data": {
                    "total_exbond_weight": exbond_data,
                    "total_dispatch_weight": dispatch_data,
                    "balance_weight": exbond_data - dispatch_data
                }   
            }
            data.append(master_obj)

        return {
            "status": status.HTTP_200_OK,
            "message": "Exbond vs Dispatch totals fetched successfully",
            "data": data
        }

    except Exception as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": str(e)
        }


# @router.get("/duty_pending_exbond")
# def get_total_duty_pending_to_pay_exbond(db:Session = Depends(get_db)):
    