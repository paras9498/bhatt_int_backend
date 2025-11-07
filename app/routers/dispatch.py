from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database import get_db
from sqlalchemy.orm import Session
from ..models.exbond_model import ExbondChild, ExbondMaster
from ..models.customer_model import CustomerMaster
from ..models.material_model import MaterialMaster
from ..schemas.dispatch_schema import CreateDispatchMaster, UpdateDispatchChild
from ..models.dispatch_model import DispatchMaster, DispatchChild

router = APIRouter(prefix = "/api/dispatch", tags = ["Dispatch"])

'''
Get the list of be numbers from the 'exbond_child' table
'''
@router.get("/benumber")
def get_all_be_number(db:Session = Depends(get_db)):
    try:
        exbonds_master = db.query(ExbondChild).filter(ExbondChild.is_dispatched == 0).all()

        be_number_list = []
        for exbond_master in exbonds_master:
            obj = {
                "id": exbond_master.id,
                "be_number": exbond_master.be_number
            }
            be_number_list.append(obj)

        return {
            "status": status.HTTP_200_OK,
            "message": "All be numbers from exbond child found",
            "data": be_number_list
        }
    
    except HTTPException as e:
        db.rollback()
        return{
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }


@router.get("/get_exbond")
def get_exbonds(
    exbond_master_id: int = Query(..., description="Exbond Master ID"),
    db: Session = Depends(get_db)
):
    try:
        # Get all ExbondChild linked to this Inbond Master
        exbonds_child = db.query(ExbondChild).filter(ExbondChild.exbond_master_id == exbond_master_id).all()
        
        if not exbonds_child:
            return {
                "status": status.HTTP_204_NO_CONTENT,
                "message": "No exbond details found for this exbond_master_id",
                "data": []
            }

        # Collect all distinct exbond_master_ids
        exbond_master_ids = list({child.exbond_master_id for child in exbonds_child if child.exbond_master_id})
        data = []

        # loop through each exbond_master_id
        for exbond_master_id in exbond_master_ids:
            exbond_master = db.query(ExbondMaster).filter(ExbondMaster.id == exbond_master_id).first()
            if not exbond_master:
                continue

            # Get all child entries for this exbond_master
            exbonds_details_child = db.query(ExbondChild).filter(ExbondChild.exbond_master_id == exbond_master.id, ExbondChild.is_dispatched == 0).all()

            exbond_child_list = []
            for exbond_detail_child in exbonds_details_child:
                customer = db.query(CustomerMaster).filter(CustomerMaster.id == exbond_detail_child.customer_master_id).first()
                material = db.query(MaterialMaster).filter(MaterialMaster.id == exbond_detail_child.material_master_id).first()

                exbond_child_detail_obj = {
                    "exbond_child_id": exbond_detail_child.id,
                    "material_master_id": exbond_detail_child.material_master_id,
                    "material_name": material.name if material else None,
                    "customer_master_id": exbond_detail_child.customer_master_id,
                    "customer_name": customer.name if customer else None,
                    "weight": exbond_detail_child.weight
                }
                exbond_child_list.append(exbond_child_detail_obj)

            # Create one object per exbond_master
            exbond_master_obj = {
                "id": exbond_master.id,
                "exbond_id": exbond_master.exbond_id,
                "exbond_child": exbond_child_list
            }

            # Append INSIDE the loop
            data.append(exbond_master_obj)

        return {
            "status": status.HTTP_200_OK,
            "message": "All exbond details found",
            "data": data
        }

    except Exception as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": str(e)
        }


@router.post("/create")
def create_dispatch(data: CreateDispatchMaster, db:Session = Depends(get_db)):
    try:
        latest = db.query(DispatchMaster).order_by(DispatchMaster.dispatch_id.desc()).first()
        next_dispatch_id = 1001 if not latest or not latest.dispatch_id else latest.dispatch_id + 1

        dispatch_master = DispatchMaster(
            dispatch_id = next_dispatch_id,
            total_dispatch_weight = data.total_dispatch_weight
        )

        db.add(dispatch_master)
        db.commit()
        db.refresh(dispatch_master)

        for dispatchchild in data.dispatchchild:
            dispatch_child = DispatchChild(
                dispatch_master_id = dispatch_master.id,
                exbond_child_id = dispatchchild.exbond_child_id,
                dispatch_date = dispatchchild.dispatch_date,
                dispatch_weight = dispatchchild.dispatch_weight,
                truck_no = dispatchchild.truck_no
            )
            db.add(dispatch_child)

            exbond_child_update = db.query(ExbondChild).filter(ExbondChild.id == dispatchchild.exbond_child_id).first()

            if exbond_child_update:
                exbond_child_update.is_dispatched = True
                db.add(exbond_child_update)
        db.commit()

        return {
            "status": status.HTTP_201_CREATED,
            "message": "Dispatch entry created successfully",
            "data": {}
        }
    
    except Exception as e:
        db.rollback()
        return{
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }
    

@router.get("/get_all")
def get_all_details(db:Session = Depends(get_db)):
    try:
        dispatchs_master = db.query(DispatchMaster).filter(DispatchMaster.is_delete == 0).order_by(DispatchMaster.created_at.desc()).all()
        master_list = []

        for dispatch_master in dispatchs_master:

            child_list = []
            dispatchs_child = db.query(DispatchChild).filter(DispatchChild.dispatch_master_id == dispatch_master.id, DispatchChild.is_delete == 0).all()
            
            for dispatch_child in dispatchs_child:
                exbond_child = db.query(ExbondChild).filter(ExbondChild.id == dispatch_child.exbond_child_id).first()
                exbond_master = db.query(ExbondMaster).filter(ExbondMaster.id == exbond_child.exbond_master_id).first()
                material = db.query(MaterialMaster).filter(MaterialMaster.id == exbond_child.material_master_id).first()
                customer = db.query(CustomerMaster).filter(CustomerMaster.id == exbond_child.customer_master_id).first()
                child_obj = {
                    "id": dispatch_child.id,
                    "exbond_id": exbond_master.exbond_id,
                    "be_number": exbond_child.be_number,
                    'exbond_child_id': dispatch_child.exbond_child_id,
                    "dispatch_date": dispatch_child.dispatch_date,
                    "dispatch_weight": dispatch_child.dispatch_weight,
                    "truck_no": dispatch_child.truck_no,
                    "material": material.name,
                    "exbond_weight": exbond_child.weight,
                    "customer": customer.name
                }

                child_list.append(child_obj)
            
            master_obj = {
                "id": dispatch_master.id,
                "dispatch_id": dispatch_master.dispatch_id,
                "created_at": dispatch_master.created_at,
                "child": child_list,
                "total_dispatch_weight": dispatch_master.total_dispatch_weight
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
    

@router.put("/soft_delete_partial/{dispatch_child_id}")
def soft_delete_partial_entry(dispatch_child_id: int, db:Session = Depends(get_db)):
    try:
        dispatch_child = db.query(DispatchChild).filter(DispatchChild.id == dispatch_child_id).first()
        dispatch_master = db.query(DispatchMaster).filter(DispatchMaster.id == dispatch_child.dispatch_master_id).first()

        if not dispatch_child:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Dispatch child entry not found"
            )
        
        if dispatch_child.is_delete == 1:
            return {
                "status": status.HTTP_204_NO_CONTENT,
                "message": "Dispatch child already deleted"
            }
        
        dispatch_weight = dispatch_child.dispatch_weight
        total_dispatch_weight = dispatch_master.total_dispatch_weight

        total_dispatch_weight -= dispatch_weight

        dispatch_master.total_dispatch_weight = total_dispatch_weight
        if dispatch_master.total_dispatch_weight == 0.00:
            dispatch_master.is_delete = 1

        dispatch_child.is_delete = 1
        db.commit()

        return {
            "status": status.HTTP_200_OK,
            "message": "Dispatch child deleted successfully and dispatch master adjusted successfully"
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
    

@router.put("/soft_delete_complete/{dispatch_master_id}")
def soft_delete_complete_entry(dispatch_master_id: int, db:Session = Depends(get_db)):
    try:
        dispatch_master = db.query(DispatchMaster).filter(DispatchMaster.id == dispatch_master_id).first()
        dispatchs_child = db.query(DispatchChild).filter(DispatchChild.dispatch_master_id == dispatch_master.id).all()

        if not dispatch_master:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Dispatch master entry not found"
            )
        
        if dispatch_master.is_delete == 1:
            return {
                "status": status.HTTP_204_NO_CONTENT,
                "message": "Dispatch master already deleted"
            }
        
        for dispatch_child in dispatchs_child:
            dispatch_child.is_delete = 1

        dispatch_master.is_delete = 1
        db.commit()

        return {
            "status": status.HTTP_200_OK,
            "message": "Dispatch deleted successfully and dispatch child adjusted successfully"
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