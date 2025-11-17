from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import date
from app.database import get_db
from sqlalchemy.orm import Session
from ..schemas.inbond_schema import CreateInbond, UpdateInbond, UpdateInbondChild
from ..auth_utils import get_current_user
from ..models.inbond_model import InbondMaster, InbondChild
from ..models.material_model import MaterialMaster
from ..models.exbond_model import ExbondChild
from ..routers.exbond import get_total_weight_by_material
from sqlalchemy import or_
import re

router = APIRouter(prefix = "/api/inbond", tags = ["Inbond"])

"""
Sample for authorization
- only user with role as admin will be allowed to access this api
"""
@router.get("/hii")
def greetings(current_user: dict=Depends(get_current_user)):
    if current_user.get("user_type") == "user":
        return(current_user)
    else:
        return("not admin")


'''
Create entry in the "inbond_master" and "inbond_child" table
'''    
@router.post("/create")
def create_inbond(data: CreateInbond, db:Session=Depends(get_db)):
    try:
        if data.be_date > data.inbond_date:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Invalid date entry. Inbond date should be greater than be date"
            )
        
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
    
    except HTTPException as e:
        raise e

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
def get_all_details(
    db:Session = Depends(get_db),
    number: Optional[str] = Query(None, description="Filter by BI number (partial match allowed)"),
    inbond_start_date: Optional[date] = Query(None, description="Filter start date"),
    inbond_end_date: Optional[date] = Query(None, description="Filter end date")
):
    try:
        # 🧩 Base query
        query = db.query(InbondMaster).filter(InbondMaster.is_delete == 0)

        # ✅ Apply filters dynamically
        if number:
            num = number.strip().upper()

            if num.startswith("BI"):
                query = query.filter(InbondMaster.bi_number == num)

            elif num.startswith("BE"):
                stripped_number = re.sub(r"\D", "", num)
                query = query.filter(InbondMaster.be_number == stripped_number)

            else:
                # Search in both BI and BE (partial allowed)
                query = query.filter(
                    or_(
                        InbondMaster.bi_number.like(f"%{num}%"),
                        InbondMaster.be_number.like(f"%{num}%")
                    )
                )

        if inbond_start_date and inbond_end_date:
            query = query.filter(InbondMaster.inbond_date.between(inbond_start_date, inbond_end_date))
        elif inbond_start_date:
            query = query.filter(InbondMaster.inbond_date >= inbond_start_date)
        elif inbond_end_date:
            query = query.filter(InbondMaster.inbond_date <= inbond_end_date)
            
        inbonds_master = query.order_by(InbondMaster.created_at.desc()).all()

        master_list = []
        
        for inbond_master in inbonds_master:
            master_id = inbond_master.id
            child_list = []
            inbonds_child = db.query(InbondChild).filter(InbondChild.inbond_master_id == master_id, InbondChild.is_delete == 0).all()
            for inbond_child in inbonds_child:
                material = db.query(MaterialMaster).filter(MaterialMaster.id == inbond_child.material_master_id, MaterialMaster.is_delete == 0).first()
                material = db.query(MaterialMaster).filter(MaterialMaster.id == inbond_child.material_master_id).first()
                child_obj = {
                    "id": inbond_child.id,
                    "material_master_id": inbond_child.material_master_id,
                    "material_name": material.name,
                    "material_short_code": material.short_code,
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


@router.get("/get_all_binumber")
def get_all_binumber(db:Session = Depends(get_db)):
    inbonds = db.query(InbondMaster).filter(InbondMaster.is_delete == 0).order_by(InbondMaster.created_at.desc()).all()
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


'''
Get all the bi_numbers from the "inbond_master" table
'''
@router.get("/get_binumber")
def get_all_binumber(db:Session = Depends(get_db)):
    inbonds = db.query(InbondMaster).filter(InbondMaster.is_settled == 0, InbondMaster.is_delete == 0).order_by(InbondMaster.created_at.desc()).all()
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


@router.put("/soft_delete_partial/{inbond_child_id}")
def soft_delete_partial_entry(inbond_child_id: int, db:Session = Depends(get_db)):
    try:
        inbond_child = db.query(InbondChild).filter(InbondChild.id == inbond_child_id, InbondChild.is_delete == 0).first()
        exbond_child = db.query(ExbondChild).filter(ExbondChild.inbond_child_id == inbond_child_id, ExbondChild.is_delete == 0).first()
        inbond_master = db.query(InbondMaster).filter(InbondMaster.id == inbond_child.inbond_master_id, InbondMaster.is_delete == 0).first()

        if not inbond_child:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Inbond child entry not found"
            )
        
        if inbond_child.is_delete == 1:
            return {
                "status": status.HTTP_204_NO_CONTENT,
                "message": "Inbond child already deleted"
            }
        
        if exbond_child:
            return {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"Exbond entry for the {inbond_child_id} exists"
            }
        
        duty_inbond_amount = inbond_child.duty_inbond_amount_inr
        inbond_weight = inbond_child.weight
        assessment_amount = inbond_child.assessment_amount_inr
        material_amount = inbond_child.material_amount_usd

        total_duty_inbond_amount = inbond_master.total_duty_inbond_amount_inr
        total_inbond_weight = inbond_master.total_weight
        total_assessment_amount = inbond_master.total_assessment_amount_inr
        total_material_amount = inbond_master.total_material_amount_usd

        total_duty_inbond_amount -= duty_inbond_amount
        total_inbond_weight -= inbond_weight
        total_assessment_amount -= assessment_amount
        total_material_amount -= material_amount


        if total_duty_inbond_amount == 0.00 and total_inbond_weight == 0.00 and total_assessment_amount == 0.00 and total_material_amount == 0.00:
            inbond_master.is_delete = 1

        inbond_master.total_duty_inbond_amount_inr = total_duty_inbond_amount
        inbond_master.total_weight = total_inbond_weight
        inbond_master.total_assessment_amount_inr = total_assessment_amount
        inbond_master.total_material_amount_usd = total_material_amount

        inbond_child.is_delete = 1
        db.commit()

        return {
            "status": status.HTTP_200_OK,
            "message": "Inbond deleted successfully and inbond master adjusted successfully"
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
    

@router.put("/soft_delete_complete/{inbond_master_id}")
def soft_delete_complete_entry(inbond_master_id: int, db:Session = Depends(get_db)):
    try:
        inbond_master = db.query(InbondMaster).filter(InbondMaster.id == inbond_master_id, InbondMaster.is_delete == 0).first()
        inbonds_child = db.query(InbondChild).filter(InbondChild.inbond_master_id == inbond_master_id, InbondChild.is_delete == 0).all()
        exbonds_child = db.query(ExbondChild).filter(ExbondChild.inbond_master_id == inbond_master_id, ExbondChild.is_delete == 0).all()

        if not inbond_master:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Inbond master entry not found"
            )
        
        if inbond_master.is_delete == 1:
            return {
                "status": status.HTTP_204_NO_CONTENT,
                "message": "Inbond master already deleted"
            }
        
        for exbond_child in exbonds_child:
            if exbond_child:
                return {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": f"Exbond entry for the {inbond_master_id} exists"
                }
        
        for inbond_child in inbonds_child:
            inbond_child.is_delete = 1
        inbond_master.is_delete = 1

        db.commit()

        return {
            "status": status.HTTP_200_OK,
            "message": "Inbond deleted successfully and inbond child adjusted successfully"
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
    

# @router.put("/update_partial/{inbond_child_id}")
# def update_partial_entry(inbond_child_id: int, data: UpdateInbondChild, db: Session = Depends(get_db)):
#     try:
#         # Fetch the inbond child entry
#         inbond_child = db.query(InbondChild).filter(InbondChild.id == inbond_child_id, InbondChild.is_delete == 0).first()

#         if not inbond_child:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Inbond child entry not found or has been deleted"
#             )

#         inbond_master_id_list = []
#         # Fetch related master entry
#         inbond_master = db.query(InbondMaster).filter(InbondMaster.id == inbond_child.inbond_master_id, InbondMaster.is_delete == 0).first()
#         exbonds_child = db.query(ExbondChild).filter(ExbondChild.inbond_child_id == inbond_child_id, ExbondChild.is_delete == 0).all()

#         total_weight_exbond = 0
#         inbond_master_id_list.append(inbond_master.id)
#         for exbond_child in exbonds_child:
#             total_weight_exbond += exbond_child.weight

#         if data.weight < total_weight_exbond:
#             return {
#                 "status": status.HTTP_406_NOT_ACCEPTABLE,
#                 "message": "Weight cannot be decreased as exbond entry for same weight exists"
#             }
        
#         # Store old values before update for total recalculation
#         old_duty_inbond_amount = inbond_child.duty_inbond_amount_inr or 0
#         old_weight = inbond_child.weight or 0
#         old_assessment_amount = inbond_child.assessment_amount_inr or 0
#         old_material_amount = inbond_child.material_amount_usd or 0

#         # Update child fields only if provided
#         if data.material_master_id is not None:
#             inbond_child.material_master_id = data.material_master_id

#         if data.duty_inbond_amount_inr is not None:
#             inbond_child.duty_inbond_amount_inr = data.duty_inbond_amount_inr
#             inbond_master.total_duty_inbond_amount_inr += (inbond_child.duty_inbond_amount_inr - old_duty_inbond_amount)

#         if data.weight is not None:
#             inbond_child.weight = data.weight
#             inbond_master.total_weight += (inbond_child.weight - old_weight)

#         if data.invoice_amount_usd is not None:
#             inbond_child.invoice_amount_usd = data.invoice_amount_usd

#         if data.assessment_amount_inr is not None:
#             inbond_child.assessment_amount_inr = data.assessment_amount_inr
#             inbond_master.total_assessment_amount_inr += (inbond_child.assessment_amount_inr - old_assessment_amount)

#         if data.dollar_inr is not None:
#             inbond_child.dollar_inr = data.dollar_inr

#         if data.price is not None:
#             inbond_child.price = data.price

#         if data.material_amount_usd is not None:
#             inbond_child.material_amount_usd = data.material_amount_usd
#             inbond_master.total_material_amount_usd += (inbond_child.material_amount_usd - old_material_amount)

#         if inbond_child.weight > total_weight_exbond:
#             if inbond_master.is_settled == 1:
#                 inbond_master.is_settled = 0
    
#         db.commit()
#         db.refresh(inbond_child)
#         get_total_weight_by_material(inbond_master_id_list, db)

#         return {
#             "status": status.HTTP_200_OK,
#             "message": "Inbond child entry updated successfully and totals recalculated"
#         }

#     except HTTPException as e:
#         raise e

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal server error: {str(e)}"
#         )


@router.get("/get_edit_details")
def get_details_for_edit(
    db: Session = Depends(get_db),
    inbond_master_id: int = Query(..., description="Filter by inbond master id"),
    inbond_child_id: Optional[int] = Query(None, description="Filter by inbond child id")
):
    try:
        # 1️⃣ Get parent/master record
        master_data = db.query(InbondMaster).filter(InbondMaster.id == inbond_master_id, InbondMaster.is_delete == 0).first()

        if not master_data:
            raise HTTPException(status_code=404, detail="Inbond master not found")

        master_data_dict = {
            "id": master_data.id,
            "bi_number": master_data.bi_number,
            "be_number": master_data.be_number,
            "inbond_date": master_data.inbond_date,
            "total_duty_inbond_amount_inr": master_data.total_duty_inbond_amount_inr,
            "total_weight": master_data.total_weight,
            "total_assessment_amount_inr": master_data.total_assessment_amount_inr,
            "total_material_amount_usd": master_data.total_material_amount_usd  
        }

        # 2️⃣ If child ID is provided — get that specific child
        if inbond_child_id:
            child_data = db.query(InbondChild).filter(InbondChild.id == inbond_child_id,InbondChild.inbond_master_id == inbond_master_id,InbondChild.is_delete == 0).first()

            if not child_data:
                raise HTTPException(status_code=404, detail="Inbond child not found")

            material = db.query(MaterialMaster).filter(MaterialMaster.id == child_data.material_master_id, MaterialMaster.is_delete == 0).first()
            
            child_data_dict = {
                "id": child_data.id,
                "material_master_id": child_data.material_master_id,
                "material_name": material.name,
                "material_short_code": material.short_code,
                "duty_inbond_amount_inr": child_data.duty_inbond_amount_inr,
                "weight": child_data.weight,
                "invoice_amount_usd": child_data.invoice_amount_usd,
                "assessment_amount_inr": child_data.assessment_amount_inr,
                "dollar_inr": child_data.dollar_inr,
                "price": child_data.price,
                "material_amount_usd": child_data.material_amount_usd,
            }
            
            return {
                "status": status.HTTP_200_OK,
                "message": "Master and child data found",
                "data": {
                    "master_data": master_data_dict,
                    "child_data": child_data_dict
                }
            }

        # 3️⃣ Else, get all children under this master
        child_data_list = []
        children_data = db.query(InbondChild).filter(InbondChild.inbond_master_id == inbond_master_id, InbondChild.is_delete == 0).all()
        for c in children_data:
            material_data = db.query(MaterialMaster).filter(MaterialMaster.id == c.material_master_id, MaterialMaster.is_delete == 0).first()
            
            child_data_list_dict = {
                "id": c.id,
                "material_master_id": c.material_master_id,
                "material_name": material_data.name,
                "material_short_code": material_data.short_code,
                "duty_inbond_amount_inr": c.duty_inbond_amount_inr,
                "weight": c.weight,
                "invoice_amount_usd": c.invoice_amount_usd,
                "assessment_amount_inr": c.assessment_amount_inr,
                "dollar_inr": c.dollar_inr,
                "price": c.price,
                "material_amount_usd": c.material_amount_usd,
            }
            child_data_list.append(child_data_list_dict)

        return {
            "status": status.HTTP_200_OK,
            "message": "Master and child data found",
            "data": {
                "master_data": master_data_dict,
                "child_data": child_data_list
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.put("/update_complete/{inbond_master_id}")
def update_inbond_entry(inbond_master_id: int, data: UpdateInbond, db: Session = Depends(get_db)):
    try:
        inbond_master = db.query(InbondMaster).filter(InbondMaster.id == inbond_master_id, InbondMaster.is_delete == 0).first()

        inbond_master_id_list = []
        if not inbond_master:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Inbond master record not found."
            )
        inbond_master_id_list.append(inbond_master.id)

        # Update master-level fields
        for key, value in data.dict(exclude_unset=True, exclude={"inbondchild"}).items():
            setattr(inbond_master, key, value)

        # Update child records if provided
        if data.inbondchild:
            for inbond_child_data in data.inbondchild:
                # Make sure each child has an ID
                if not hasattr(inbond_child_data, "id"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Each child record must include an 'id' for update."
                    )

                inbond_child = db.query(InbondChild).filter(InbondChild.id == inbond_child_data.id, InbondChild.inbond_master_id == inbond_master_id, InbondChild.is_delete == 0).first()
                if not inbond_child:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Inbond child with ID {inbond_child_data.id} not found."
                    )
                
                exbonds_child = db.query(ExbondChild).filter(ExbondChild.inbond_child_id == inbond_child.id, ExbondChild.is_delete == 0).all()
                total_weight_exbond = 0
                for exbond_child in exbonds_child:
                    total_weight_exbond += exbond_child.weight

                if inbond_child_data.weight is not None:
                    if total_weight_exbond > inbond_child_data.weight:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=(
                                f"Cannot update InbondChild ID {inbond_child_data.id}: "
                                f"Total Exbond weight ({total_weight_exbond}) exceeds updated Inbond weight ({inbond_child_data.weight})."
                            )
                        )
                    if total_weight_exbond < inbond_child_data.weight:
                        if inbond_master.is_settled == 1:
                            inbond_master.is_settled = 0

                for key, value in inbond_child_data.dict(exclude_unset=True).items():
                    setattr(inbond_child, key, value)

        # Commit changes
        db.commit()
        db.refresh(inbond_master)
        get_total_weight_by_material(inbond_master_id_list , db)

        return {
            "status": status.HTTP_200_OK,
            "message": "Inbond master entry updated successfully and totals recalculated"
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )