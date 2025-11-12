from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import date
from app.database import get_db
from sqlalchemy.orm import Session
from ..models.exbond_model import ExbondChild, ExbondMaster
from ..schemas.exbond_schema import CreateExbondMaster, UpdateExbondChild, UpdateExbondMaster
from ..models.section_model import SectionMaster
from ..models.material_model import MaterialMaster
from ..models.inbond_model import InbondMaster, InbondChild
from ..models.customer_model import CustomerMaster
from ..models.dispatch_model import DispatchChild
from sqlalchemy import func

router = APIRouter(prefix = "/api/exbond", tags = ["Exbond"])


def get_total_weight_by_material(inbond_master_id_list, db: Session):
    # Fetch total inbond weights grouped by inbond_master_id and material_master_id
    inbond_weights = (
        db.query(
            InbondChild.inbond_master_id,
            InbondChild.material_master_id,
            func.sum(InbondChild.weight).label("total_inbond_weight")
        )
        .filter(InbondChild.inbond_master_id.in_(inbond_master_id_list),InbondChild.is_delete == 0)
        .group_by(InbondChild.inbond_master_id, InbondChild.material_master_id)
        .all()
    )

    # Fetch total exbond weights grouped by inbond_master_id and material_master_id
    exbond_weights = (
        db.query(
            ExbondChild.inbond_master_id,
            ExbondChild.material_master_id,
            func.sum(ExbondChild.weight).label("total_exbond_weight")
        )
        .filter(ExbondChild.inbond_master_id.in_(inbond_master_id_list),ExbondChild.is_delete == 0)
        .group_by(ExbondChild.inbond_master_id, ExbondChild.material_master_id)
        .all()
    )

    # Combine data
    master_data = {}

    # Add inbond data
    for item in inbond_weights:
        master_id = item.inbond_master_id
        material_id = item.material_master_id

        if master_id not in master_data:
            master_data[master_id] = {}

        if material_id not in master_data[master_id]:
            master_data[master_id][material_id] = {
                "total_inbond_weight": 0,
                "total_exbond_weight": 0
            }

        master_data[master_id][material_id]["total_inbond_weight"] = item.total_inbond_weight

    # Add exbond data
    for item in exbond_weights:
        master_id = item.inbond_master_id
        material_id = item.material_master_id

        if master_id not in master_data:
            master_data[master_id] = {}

        if material_id not in master_data[master_id]:
            master_data[master_id][material_id] = {
                "total_inbond_weight": 0,
                "total_exbond_weight": 0
            }

        master_data[master_id][material_id]["total_exbond_weight"] = item.total_exbond_weight

    # Prepare result list and update settlement status
    #result = []
    for master_id, materials in master_data.items():
        all_settled = True
        material_list = []

        for material_id, weights in materials.items():
            inbond_wt = weights["total_inbond_weight"] or 0
            exbond_wt = weights["total_exbond_weight"] or 0

            # If any material not fully exbonded → not settled
            if exbond_wt < inbond_wt:
                all_settled = False

            # material_list.append({
            #     "material_master_id": material_id,
            #     "total_inbond_weight": inbond_wt,
            #     "total_exbond_weight": exbond_wt
            # })

        # Update only if all materials are settled
        inbond_master = db.query(InbondMaster).filter(InbondMaster.id == master_id).first()
        if inbond_master:
            inbond_master.is_settled = all_settled

        # Prepare result
        # result.append({
        #     "inbond_master_id": master_id,
        #     "is_settled": all_settled,
        #     "materials": material_list
        # })

    db.commit()
    #return result


'''
Create entry in the "exbond_master" and "exbond_child" table
'''
@router.post("/create")
def create_exbond(data: CreateExbondMaster, db:Session = Depends(get_db)):
    try:
        #inbond_master_id_array = []
        latest = db.query(ExbondMaster).order_by(ExbondMaster.exbond_id.desc()).first()
        next_exbond_id = 1001 if not latest or not latest.exbond_id else latest.exbond_id + 1

        exbond_master = ExbondMaster(
            exbond_id = next_exbond_id,
            total_duty_exbond_amount_inr = data.total_duty_exbond_amount_inr,
            total_weight = data.total_weight,
            total_invoice_amount_inr = data.total_invoice_amount_inr,
            #total_dispatch_weight = data.total_dispatch_weight
        )
        db.add(exbond_master)
        db.commit()
        db.refresh(exbond_master)

        inbond_master_id_list = []
        for exbondchild in data.exbondchild:
            exbond_child = ExbondChild(
                exbond_master_id = exbond_master.id,
                inbond_master_id = exbondchild.inbond_master_id,
                section_master_id = exbondchild.section_master_id,
                material_master_id = exbondchild.material_master_id,
                customer_master_id = exbondchild.customer_master_id,
                inbond_child_id = exbondchild.inbond_child_id,
                be_number = exbondchild.be_number,
                be_date = exbondchild.be_date,
                type = exbondchild.type,
                resultant = exbondchild.resultant,
                duty_exbond_amount_inr = exbondchild.duty_exbond_amount_inr,
                dollar_inr = exbondchild.dollar_inr,
                rate = exbondchild.rate,
                weight = exbondchild.weight,
                invoice_amount_inr = exbondchild.invoice_amount_inr,
                #dispatch_date = exbondchild.dispatch_date,
                #dispatch_weight = exbondchild.dipspatch_weight,
                #truck_number = exbondchild.truck_number
            )
            db.add(exbond_child)
            inbond_master_id_list.append(exbond_child.inbond_master_id)
        db.commit()

        result = get_total_weight_by_material(inbond_master_id_list,db)
        print(result)

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
def get_all_details(
    db:Session = Depends(get_db),
    bi_number: Optional[str] = Query(None, description="Filter by Inbond BI Number"),
    start_date: Optional[date] = Query(None, description="Start BE date for filter"),
    end_date: Optional[date] = Query(None, description="End BE date for filter")
):
    try:
        exbonds_master = db.query(ExbondMaster).filter(ExbondMaster.is_delete == 0).order_by(ExbondMaster.created_at.desc()).all()
        master_list = []
        
        for exbond_master in exbonds_master:
            master_id = exbond_master.id
            child_list = []

            child_query = db.query(ExbondChild).filter(ExbondChild.exbond_master_id == master_id, ExbondChild.is_delete == 0)

            # Filter by BE date range
            if start_date and end_date:
                child_query = child_query.filter(ExbondChild.be_date.between(start_date, end_date))
            elif start_date:
                child_query = child_query.filter(ExbondChild.be_date >= start_date)
            elif end_date:
                child_query = child_query.filter(ExbondChild.be_date <= end_date)

            exbonds_child = child_query.all()
            
            for exbond_child in exbonds_child:
                section = db.query(SectionMaster).filter(SectionMaster.id == exbond_child.section_master_id, SectionMaster.is_delete == 0).first()
                material = db.query(MaterialMaster).filter(MaterialMaster.id == exbond_child.material_master_id, MaterialMaster.is_delete == 0).first()
                inbond = db.query(InbondMaster).filter(InbondMaster.id == exbond_child.inbond_master_id, InbondChild.is_delete == 0).first()
                customer = db.query(CustomerMaster).filter(CustomerMaster.id == exbond_child.customer_master_id, CustomerMaster.is_delete == 0).first()

                if bi_number and (not inbond or inbond.bi_number != bi_number):
                    continue

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
                    "material_short_code": material.short_code,
                    "duty_exbond_amount_inr": exbond_child.duty_exbond_amount_inr,
                    "dollar_inr": exbond_child.dollar_inr,
                    "rate": exbond_child.rate,
                    "weight": exbond_child.weight,
                    "invoice_amount_inr": exbond_child.invoice_amount_inr,
                    "customer_name": customer.name,
                    #"dispatch_date": exbond_child.dispatch_date,
                    #"dispatch_weight": exbond_child.dispatch_weight,
                    #"truck_number": exbond_child.truck_number
                }
                child_list.append(child_obj)
            
            master_obj = {
                "id": master_id,
                "exbond_id": exbond_master.exbond_id,
                "child": child_list,
                "total_duty_exbond_amount_inr": exbond_master.total_duty_exbond_amount_inr,
                "total_weight": exbond_master.total_weight,
                "total_invoice_amount_inr": exbond_master.total_invoice_amount_inr,
                #"total_dispatch_weight": exbond_master.total_dispatch_weight,
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
        inbonds_child = db.query(InbondChild).filter(InbondChild.inbond_master_id == inbond_master_id, InbondChild.is_delete == 0).all()
        inbond_master = db.query(InbondMaster).filter(InbondMaster.id == inbond_master_id, InbondMaster.is_delete == 0).first()

        list = []
        for inbond_child in inbonds_child:
            material = db.query(MaterialMaster).filter(MaterialMaster.id == inbond_child.material_master_id, MaterialMaster.is_delete == 0).first()
            obj = {
                "inbond_master_id": inbond_master.id,
                "inbond_child_id": inbond_child.id,
                "material_master_id": inbond_child.material_master_id,
                "material_name": material.name,
                "material_short_code": material.short_code,
                "material_weight": inbond_child.weight,
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
        inbond_child = db.query(InbondChild).filter(InbondChild.material_master_id == material_master_id, InbondChild.inbond_master_id == inbond_master_id, InbondChild.is_delete == 0).first()

        inbond_obj = {
            "inbond_weight": inbond_child.weight,
            "duty_inbond_amount_inr": inbond_child.duty_inbond_amount_inr
        }

        exbonds_child = db.query(ExbondChild).filter(ExbondChild.material_master_id == material_master_id, ExbondChild.inbond_master_id == inbond_master_id, ExbondChild.is_delete == 0).all()

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
    


@router.get("/get_weight_duty_test")
def get_weight_and_duty(
    inbond_child_id: int = Query(..., description = "Inbond Child ID"),
    db: Session = Depends(get_db)
):
    try:
        inbond_child = db.query(InbondChild).filter(InbondChild.id == inbond_child_id, InbondChild.is_delete == 0).first()

        inbond_obj = {
            "inbond_weight": inbond_child.weight,
            "duty_inbond_amount_inr": inbond_child.duty_inbond_amount_inr
        }

        exbonds_child = db.query(ExbondChild).filter(ExbondChild.inbond_child_id == inbond_child_id, ExbondChild.is_delete == 0).all()

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
            #"material_master_id": material_master_id,
            #"inbond_master_id": inbond_master_id,
            "material_master_id": inbond_child.material_master_id,
            "inbond_child_id": inbond_child_id,
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
    

@router.put("/soft_delete_partial/{exbond_child_id}")
def soft_delete_partial_entry(exbond_child_id: int, db:Session = Depends(get_db)):
    try:
        inbond_master_id_list = []
        exbond_child = db.query(ExbondChild).filter(ExbondChild.id == exbond_child_id, ExbondChild.is_delete == 0).first()
        dispatch_child = db.query(DispatchChild).filter(DispatchChild.exbond_child_id == exbond_child_id, DispatchChild.is_delete == 0).first()
        exbond_master = db.query(ExbondMaster).filter(ExbondMaster.id == exbond_child.exbond_master_id, ExbondMaster.is_delete == 0).first()

        if not exbond_child:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Exbond child entry not found"
            )
        
        if exbond_child.is_delete == 1:
            return {
                "status": status.HTTP_204_NO_CONTENT,
                "message": "Exbond child already deleted"
            }
        
        if dispatch_child:
            return {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"Dispatch entry for the {exbond_child_id} exists"
            }
        
        inbond_master_id_list.append(exbond_child.inbond_master_id)
        
        duty_exbond_amount = exbond_child.duty_exbond_amount_inr
        exbond_weight = exbond_child.weight
        invoice_amount = exbond_child.invoice_amount_inr

        total_duty_exbond_amount = exbond_master.total_duty_exbond_amount_inr
        total_exbond_weight = exbond_master.total_weight
        total_invoice_amount = exbond_master.total_invoice_amount_inr

        total_duty_exbond_amount -= duty_exbond_amount
        total_exbond_weight -= exbond_weight
        total_invoice_amount -= invoice_amount

        if total_duty_exbond_amount == 0.00 and total_exbond_weight == 0.00 and total_invoice_amount == 0.00:
            exbond_master.is_delete = 1
        
        exbond_master.total_duty_exbond_amount_inr = total_duty_exbond_amount
        exbond_master.total_weight = total_exbond_weight
        exbond_master.total_invoice_amount_inr = total_invoice_amount

        exbond_child.is_delete = 1
        db.commit()
        get_total_weight_by_material(inbond_master_id_list, db)

        return {
            "status": status.HTTP_200_OK,
            "message": "Exbond deleted successfully and exbond master adjusted successfully"
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
    

@router.put("/soft_delete_complete/{exbond_master_id}")
def soft_delete_complete_entry(exbond_master_id: int, db:Session = Depends(get_db)):
    try:
        exbond_master = db.query(ExbondMaster).filter(ExbondMaster.id == exbond_master_id, ExbondMaster.is_delete == 0).first()

        if not exbond_master:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Exbond master entry not found"
            )
        
        if exbond_master.is_delete == 1:
            return {
                "status": status.HTTP_204_NO_CONTENT,
                "message": "Exbond master already deleted"
            }
        
        exbonds_child = db.query(ExbondChild).filter(ExbondChild.exbond_master_id == exbond_master.id, ExbondChild.is_delete == 0).all()

        inbond_master_id_list = []
        for exbond_child in exbonds_child:
            dispatch_child = db.query(DispatchChild).filter(DispatchChild.exbond_child_id == exbond_child.id, DispatchChild.is_delete == 0).first()

            if dispatch_child:
                return {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": f"Dispatch entry for the {exbond_master_id} exists"
                }
            inbond_master_id_list.append(exbond_child.inbond_master_id)
            exbond_child.is_delete = 1

        exbond_master.is_delete = 1
        db.commit()
        get_total_weight_by_material(inbond_master_id_list, db)

        return {
            "status": status.HTTP_200_OK,
            "message": "Exbond deleted successfully and exbond child adjusted successfully"
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
    

# @router.put("/update_partial/{exbond_child_id}")
# def partial_update_entry(exbond_child_id: int, data: UpdateExbondChild, db:Session = Depends(get_db)):
#     try:
#         exbond_child = db.query(ExbondChild).filter(ExbondChild.id == exbond_child_id, ExbondChild.is_delete == 0).first()
#         if not exbond_child:
#             raise HTTPException(
#                 status_code = status.HTTP_404_NOT_FOUND,
#                 detail = "Exbond child entry not found"
#             )
        
#         dispatchs_child = db.query(DispatchChild).filter(DispatchChild.exbond_child_id == exbond_child_id, DispatchChild.is_delete == 0).all()
#         for dispatch_child in dispatchs_child:
#             total_weight_dispatch += dispatch_child.dispatch_weight
        
#         inbond_child = db.query(InbondChild).filter(InbondChild.id == exbond_child.inbond_child_id, InbondChild.is_delete == 0).first()
#         total_weight_inbond = inbond_child.weight

#         if total_weight_inbond < data.weight or data.weight < total_weight_dispatch:
#             return {
#                 "status": status.HTTP_406_NOT_ACCEPTABLE,
#                 "message": 'Weight is either greater than inbond weight or it is less than dispatch weight'
#             }
        
#         exbond_master = db.query(ExbondMaster).filter(ExbondMaster.id == exbond_child.exbond_master_id, ExbondMaster.is_delete == 0).first()
        
#         old_duty_exbond_amount_inr = exbond_child.duty_exbond_amount_inr or 0.00
#         old_weight = exbond_child.weight or 0.00
#         old_invoice_amount_inr = exbond_child.invoice_amount_inr or 0.00
        
#         inbond_master_id_list = []
#         if data.inbond_master_id is not None:
#             exbond_child.inbond_master_id = data.inbond_master_id
#             inbond_master_id_list.append(exbond_child.inbond_master_id)

#         if data.material_master_id is not None:
#             exbond_child.material_master_id = data.material_master_id

#         if data.section_master_id is not None:
#             exbond_child.section_master_id = data.section_master_id

#         if data.customer_master_id is not None:
#             exbond_child.customer_master_id = data.customer_master_id

#         if data.be_number is not None:
#             exbond_child.be_number = data.be_number

#         if data.be_date is not None:
#             exbond_child.be_date = data.be_date

#         if data.type is not None:
#             exbond_child.type = data.type

#         if data.resultant is not None:
#             exbond_child.resultant = data.resultant

#         if data.duty_exbond_amount_inr is not None:
#             exbond_child.duty_exbond_amount_inr = data.duty_exbond_amount_inr
#             exbond_master.total_duty_exbond_amount_inr += (exbond_child.duty_exbond_amount_inr - old_duty_exbond_amount_inr)
        
#         if data.dollar_inr is not None:
#             exbond_child.dollar_inr = data.dollar_inr
        
#         if data.rate is not None:
#             exbond_child.rate = data.rate
        
#         if data.weight is not None:
#             exbond_child.weight = data.weight
#             exbond_master.total_weight += (exbond_child.weight - old_weight)
        
#         if data.invoice_amount_inr is not None:
#             exbond_child.invoice_amount_inr = data.invoice_amount_inr
#             exbond_master.total_invoice_amount_inr += (exbond_child.invoice_amount_inr - old_invoice_amount_inr)

#         if exbond_child.weight > total_weight_dispatch:
#             exbond_child.is_dispatched = 0

#         if exbond_child.weight < total_weight_inbond:
#             inbond_master = db.query(InbondMaster).filter(InbondMaster.id == exbond_child.inbond_master_id, InbondMaster.is_delete == 0).first()
#             if inbond_master.is_settled == 1:
#                 inbond_master.is_settled = 0
        
#         db.commit()
#         db.refresh(exbond_child)
#         get_total_weight_by_material(inbond_master_id_list, db)

#         return {
#             "status": status.HTTP_200_OK,
#             "message": "Exbond child entry updated successfully and totals recalculated"
#         }

#     except HTTPException as e:
#         raise e
    
#     except Exception as e:
#         db.rollback()
#         return {
#             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
#             "message": "Internal server error",
#             "detail": e
#         }
    
    
@router.put("/update_complete/{exbond_master_id}")
def update_exbond_entry(exbond_master_id: int, data: UpdateExbondMaster, db: Session = Depends(get_db)):
    try:
        # Fetch Exbond master
        exbond_master = db.query(ExbondMaster).filter(ExbondMaster.id == exbond_master_id, ExbondMaster.is_delete == 0).first()

        if not exbond_master:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exbond master record not found."
            )

        # Update master-level fields
        for key, value in data.dict(exclude_unset=True, exclude={"exbondchild"}).items():
            setattr(exbond_master, key, value)

        inbond_master_id_list = []
        # Process child updates
        if data.exbondchild:
            for exbond_child_data in data.exbondchild:
                if not exbond_child_data.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Each exbond child record must include an 'id' for update."
                    )

                # Fetch the ExbondChild
                exbond_child = db.query(ExbondChild).filter(ExbondChild.id == exbond_child_data.id, ExbondChild.exbond_master_id == exbond_master_id, ExbondChild.is_delete == 0).first()

                if not exbond_child:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Exbond child with ID {exbond_child_data.id} not found."
                    )

                # Get related DispatchChild total weight
                dispatch_children = db.query(DispatchChild).filter(DispatchChild.exbond_child_id == exbond_child.id, DispatchChild.is_delete == 0).all()

                total_dispatch_weight = sum(
                    (dispatch_child.dispatch_weight or 0) for dispatch_child in dispatch_children
                )

                # Get total Exbond weight for this inbond_child_id
                all_exbond_for_same_inbond = db.query(ExbondChild).filter(ExbondChild.inbond_child_id == exbond_child.inbond_child_id, ExbondChild.is_delete == 0).all()

                total_exbond_weight = 0
                for ex in all_exbond_for_same_inbond:
                    # If this is the same record being updated, use the *new* weight (if provided)
                    if ex.id == exbond_child_data.id and exbond_child_data.weight is not None:
                        total_exbond_weight += exbond_child_data.weight
                    else:
                        total_exbond_weight += ex.weight or 0

                # Fetch InbondChild for validation
                inbond_child = db.query(InbondChild).filter(InbondChild.id == exbond_child.inbond_child_id, InbondChild.is_delete == 0).first()
                inbond_master = db.query(InbondMaster).filter(InbondMaster.id == inbond_child.inbond_master_id, InbondMaster.is_delete == 0).first()
                
                inbond_master_id_list.append(inbond_master.id)
                if not inbond_child:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Inbond child with ID {exbond_child.inbond_child_id} not found."
                    )

                # Compare both validations
                # (a) Dispatch ≤ Exbond
                if total_dispatch_weight > exbond_child_data.weight:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Cannot update ExbondChild ID {exbond_child_data.id}: "
                            f"Total Dispatch weight ({total_dispatch_weight}) exceeds updated Exbond weight ({exbond_child_data.weight})."
                        )
                    )

                # (b) Sum of Exbond ≤ Inbond
                if total_exbond_weight > inbond_child.weight or 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Cannot update ExbondChild ID {exbond_child_data.id}: "
                            f"Total Exbond weight for this Inbond ({total_exbond_weight}) exceeds Inbond weight ({inbond_child.weight})."
                        )
                    )

                if total_exbond_weight < inbond_child.weight:
                    inbond_master.is_settled = 0

                # Apply valid updates
                for key, value in exbond_child_data.dict(exclude_unset=True).items():
                    setattr(exbond_child, key, value)

        # Commit and refresh
        db.commit()
        db.refresh(exbond_master)
        get_total_weight_by_material(inbond_master_id_list, db)

        return {
            "status": status.HTTP_200_OK,
            "message": "Exbond master entry updated successfully and totals recalculated"
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )