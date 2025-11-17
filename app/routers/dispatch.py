from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database import get_db
from sqlalchemy.orm import Session
from ..models.exbond_model import ExbondChild, ExbondMaster
from ..models.customer_model import CustomerMaster
from ..models.material_model import MaterialMaster
from ..schemas.dispatch_schema import CreateDispatchMaster, UpdateDispatchChild, UpdateDispatchMaster
from ..models.dispatch_model import DispatchMaster, DispatchChild

router = APIRouter(prefix = "/api/dispatch", tags = ["Dispatch"])


def get_weight_total_dispatch(exbond_child_id_list, db: Session):
    for exbond_child_id in exbond_child_id_list:
        exbond_child = db.query(ExbondChild).filter(ExbondChild.id == exbond_child_id, ExbondChild.is_delete == 0).first()
        total_weight_exbond = exbond_child.weight

        dispatchs_child = db.query(DispatchChild).filter(DispatchChild.exbond_child_id == exbond_child_id, DispatchChild.is_delete == 0).all()
        
        total_weight_dispatch = 0
        for dispatch_child in dispatchs_child:
            total_weight_dispatch += dispatch_child.dispatch_weight

        if total_weight_exbond <= total_weight_dispatch:
            exbond_child.is_dispatched = 1
        
        else:
            exbond_child.is_dispatched = 0
        
    db.commit()


'''
Get the list of be numbers from the 'exbond_child' table
'''
@router.get("/benumber")
def get_all_be_number(db:Session = Depends(get_db)):
    try:
        exbonds_child = db.query(ExbondChild).filter(ExbondChild.is_dispatched == 0, ExbondChild.is_delete == 0).all()

        be_number_list = []
        for exbond_child in exbonds_child:
            obj = {
                "id": exbond_child.id,
                "be_number": exbond_child.be_number
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
    exbond_child_id: int = Query(..., description="Exbond Master ID"),
    db: Session = Depends(get_db)
):
    try:
        # Get all ExbondChild linked to this Inbond Master
        exbonds_child = db.query(ExbondChild).filter(ExbondChild.id == exbond_child_id, ExbondChild.is_delete == 0).all()
        
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
            exbond_master = db.query(ExbondMaster).filter(ExbondMaster.id == exbond_master_id, ExbondMaster.is_delete == 0).first()
            if not exbond_master:
                continue

            # Get all child entries for this exbond_master
            exbonds_details_child = db.query(ExbondChild).filter(ExbondChild.exbond_master_id == exbond_master.id, ExbondChild.is_dispatched == 0, ExbondChild.is_delete == 0).all()

            exbond_child_list = []
            for exbond_detail_child in exbonds_details_child:
                #customer = db.query(CustomerMaster).filter(CustomerMaster.id == exbond_detail_child.customer_master_id, CustomerMaster.is_delete == 0).first()
                #material = db.query(MaterialMaster).filter(MaterialMaster.id == exbond_detail_child.material_master_id, MaterialMaster.is_delete == 0).first()

                customer = db.query(CustomerMaster).filter(CustomerMaster.id == exbond_detail_child.customer_master_id).first()
                material = db.query(MaterialMaster).filter(MaterialMaster.id == exbond_detail_child.material_master_id).first()

                dispatchs_child = db.query(DispatchChild).filter(DispatchChild.exbond_child_id == exbond_detail_child.id, DispatchChild.is_delete == 0).all()
                dispatch_weight_total = 0
                for dispatch_child in dispatchs_child:
                    dispatch_weight_total += dispatch_child.dispatch_weight

                exbond_child_detail_obj = {
                    "exbond_child_id": exbond_detail_child.id,
                    "material_master_id": exbond_detail_child.material_master_id,
                    "material_name": material.name if material else None,
                    "material_short_code": material.short_code if material else None,
                    "customer_master_id": exbond_detail_child.customer_master_id,
                    "customer_name": customer.name if customer else None,
                    "weight": exbond_detail_child.weight,
                    "dispatch_weight": dispatch_weight_total
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

        exbond_child_id_list = []
        for dispatchchild in data.dispatchchild:
            dispatch_child = DispatchChild(
                dispatch_master_id = dispatch_master.id,
                exbond_child_id = dispatchchild.exbond_child_id,
                dispatch_date = dispatchchild.dispatch_date,
                dispatch_weight = dispatchchild.dispatch_weight,
                truck_no = dispatchchild.truck_no
            )
            db.add(dispatch_child)
            exbond_child_id_list.append(dispatchchild.exbond_child_id)

            exbond_child_update = db.query(ExbondChild).filter(ExbondChild.id == dispatchchild.exbond_child_id, ExbondChild.is_delete == 0).first()

            # if exbond_child_update:
            #     exbond_child_update.is_dispatched = True
            #     db.add(exbond_child_update)
        db.commit()
        get_weight_total_dispatch(exbond_child_id_list, db)

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
                exbond_child = db.query(ExbondChild).filter(ExbondChild.id == dispatch_child.exbond_child_id, ExbondChild.is_delete == 0).first()
                exbond_master = db.query(ExbondMaster).filter(ExbondMaster.id == exbond_child.exbond_master_id, ExbondMaster.is_delete == 0).first()
                #material = db.query(MaterialMaster).filter(MaterialMaster.id == exbond_child.material_master_id, MaterialMaster.is_delete == 0).first()
                #customer = db.query(CustomerMaster).filter(CustomerMaster.id == exbond_child.customer_master_id, CustomerMaster.is_delete == 0).first()

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
                    "material_short_code": material.short_code,
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
        exbond_child_id_list = [] 
        dispatch_child = db.query(DispatchChild).filter(DispatchChild.id == dispatch_child_id, DispatchChild.is_delete == 0).first()
        dispatch_master = db.query(DispatchMaster).filter(DispatchMaster.id == dispatch_child.dispatch_master_id, DispatchMaster.is_delete == 0).first()

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
        exbond_child_id_list.append(dispatch_child.exbond_child_id)

        dispatch_weight = dispatch_child.dispatch_weight
        total_dispatch_weight = dispatch_master.total_dispatch_weight

        total_dispatch_weight -= dispatch_weight

        dispatch_master.total_dispatch_weight = total_dispatch_weight
        if dispatch_master.total_dispatch_weight == 0.00:
            dispatch_master.is_delete = 1

        dispatch_child.is_delete = 1
        db.commit()
        get_weight_total_dispatch(exbond_child_id_list, db)

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
        dispatch_master = db.query(DispatchMaster).filter(DispatchMaster.id == dispatch_master_id, DispatchMaster.is_delete == 0).first()
        dispatchs_child = db.query(DispatchChild).filter(DispatchChild.dispatch_master_id == dispatch_master.id, DispatchChild.is_delete == 0).all()

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
        exbond_child_id_list = []
        for dispatch_child in dispatchs_child:
            dispatch_child.is_delete = 1
            exbond_child_id_list.append(dispatch_child.exbond_child_id)

        dispatch_master.is_delete = 1
        db.commit()
        get_weight_total_dispatch(exbond_child_id_list, db)

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


# @router.put("/update_partial/{dispatch_child_id}")
# def partial_update_entry(dispatch_child_id: int, data: UpdateDispatchChild, db:Session = Depends(get_db)):
#     try:
#         dispatch_child = db.query(DispatchChild).filter(DispatchChild.id == dispatch_child_id, DispatchChild.is_delete == 0).first()

#         if not dispatch_child:
#             raise HTTPException(
#                 status_code = status.HTTP_404_NOT_FOUND,
#                 detail = "Dispatch child entry not found or already deleted"
#             )
#         old_weight_dispatch_child = dispatch_child.dispatch_weight

#         dispatch_master = db.query(DispatchMaster).filter(DispatchMaster.id == dispatch_child.dispatch_master_id, DispatchMaster.is_delete == 0).first()
#         total_weight_dispatch_master = dispatch_master.total_dispatch_weight
        
#         if data.exbond_child_id is not None:
#             dispatch_child.exbond_child_id = data.exbond_child_id
#         if data.dispatch_date is not None:
#             dispatch_child.dispatch_date = data.dispatch_date
#         if data.dispatch_weight is not None:
#             dispatch_child.dispatch_weight = data.dispatch_weight
#             difference = old_weight_dispatch_child - data.dispatch_weight
#             dispatch_master.total_dispatch_weight = total_weight_dispatch_master - difference

#         if data.truck_no is not None:
#             dispatch_child.truck_no = data.truck_no

#         dispatchs_child = db.query(DispatchChild).filter(DispatchChild.exbond_child_id == dispatch_child.exbond_child_id, DispatchChild.is_delete == 0).all()
#         new_total_weight = 0
#         for child in dispatchs_child:
#             new_total_weight += child.dispatch_weight
        
#         exbond_child = db.query(ExbondChild).filter(ExbondChild.id == dispatch_child.exbond_child_id, ExbondChild.is_delete == 0).first()
#         exbond_weight = exbond_child.weight
        
#         if exbond_weight > new_total_weight:
#             exbond_child.is_dispatched = 0
        
#         db.commit()
#         db.refresh(dispatch_child)
#         return {
#             "status": status.HTTP_200_OK,
#             "message": "Dispatch child entry updated successfully and totals recalculated"
#         } 

#     except HTTPException as e:
#         raise e
    
#     except Exception as e:
#         db.rollback()
#         return {
#             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
#             "message": "Internal server error",
#             "detail": str(e)
#         }     
    

@router.put("/update_complete/{dispatch_master_id}")
def update_dispatch_entry(dispatch_master_id: int, data: UpdateDispatchMaster, db: Session = Depends(get_db)):
    try:
        # 1️⃣ Fetch master record
        dispatch_master = db.query(DispatchMaster).filter(DispatchMaster.id == dispatch_master_id, DispatchMaster.is_delete == 0).first()

        if not dispatch_master:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dispatch master record not found."
            )

        # 2️⃣ Update master fields (excluding children)
        for key, value in data.dict(exclude_unset=True, exclude={"dispatchchild"}).items():
            setattr(dispatch_master, key, value)

        exbond_child_id_list = []
        # 3️⃣ Update child entries if provided
        if data.dispatchchild:
            for dispatch_child_data in data.dispatchchild:
                # Must include child id
                if not dispatch_child_data.dispatch_child_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Each dispatch child record must include an 'id' for update."
                    )

                # Fetch the existing dispatch child
                dispatch_child = db.query(DispatchChild).filter(DispatchChild.id == dispatch_child_data.dispatch_child_id, DispatchChild.dispatch_master_id == dispatch_master_id, DispatchChild.is_delete == 0).first()

                if not dispatch_child:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Dispatch child with ID {dispatch_child_data.dispatch_child_id} not found."
                    )
                exbond_child_id_list.append(dispatch_child.exbond_child_id)

                # ⚙️ Validation: Dispatch vs Exbond weight
                if dispatch_child.exbond_child_id:
                    # Get all dispatch entries linked to same exbond child
                    all_dispatch_for_same_exbond = db.query(DispatchChild).filter(DispatchChild.exbond_child_id == dispatch_child.exbond_child_id, DispatchChild.is_delete == 0).all()

                    # Calculate total dispatch weight including updated value
                    total_dispatch_weight = 0
                    for d in all_dispatch_for_same_exbond:
                        if d.id == dispatch_child_data.dispatch_child_id and dispatch_child_data.dispatch_weight is not None:
                            total_dispatch_weight += dispatch_child_data.dispatch_weight
                        else:
                            total_dispatch_weight += d.dispatch_weight or 0

                    # Fetch corresponding exbond_child for weight comparison
                    exbond_child = db.query(ExbondChild).filter(ExbondChild.id == dispatch_child.exbond_child_id, ExbondChild.is_delete == 0).first()

                    if not exbond_child:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Exbond child with ID {dispatch_child.exbond_child_id} not found."
                        )

                    # Compare total dispatch vs exbond weight
                    if total_dispatch_weight > exbond_child.weight or 0:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=(
                                f"Cannot update DispatchChild ID {dispatch_child_data.dispatch_child_id}: "
                                f"Total Dispatch weight ({total_dispatch_weight}) for ExbondChild ID {dispatch_child.exbond_child_id} "
                                f"exceeds Exbond weight ({exbond_child.weight})."
                            )
                        )
                    
                    # if total_dispatch_weight < exbond_child.weight:
                    #     exbond_child.is_dispatched = 0

                # 4️⃣ Apply updates if validation passes
                for key, value in dispatch_child_data.dict(exclude_unset=True).items():
                    setattr(dispatch_child, key, value)

        # 5️⃣ Commit and refresh
        db.commit()
        db.refresh(dispatch_master)
        get_weight_total_dispatch(exbond_child_id_list, db)

        return {
            "status": status.HTTP_200_OK,
            "message": "Dispatch master entry updated successfully and totals recalculated"
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )