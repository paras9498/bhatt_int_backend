from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database import get_db
from sqlalchemy.orm import Session
from ..models.customer_model import CustomerMaster
from ..schemas.customer_schema import CreateCustomer, UpdateCustomer
from datetime import datetime

router = APIRouter(prefix = "/api/customer", tags = ['Customer'])

'''
Create customer entry in 'customer_master' table
'''
@router.post("/create")
def create_customer(data: CreateCustomer, db:Session = Depends(get_db)):
    try:
        customer = CustomerMaster(
            name = data.name,
            address = data.address
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        return {
            "status": status.HTTP_201_CREATED,
            "message": "Section created successfully",
            "data": {
                "name": customer.name,
                "desc": customer.address 
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
Get all the details from "customer_master" table
'''
@router.get("/get_all")
def get_all_details(db:Session = Depends(get_db)):
    try:
        customers = db.query(CustomerMaster).filter(CustomerMaster.is_delete == 0).order_by(CustomerMaster.created_at.desc()).all()

        customer_list = []
        for customer in customers:
            customer_obj = {
                "id": customer.id,
                "name": customer.name,
                "address": customer.address,
                "created_at": customer.created_at
            }
            customer_list.append(customer_obj)
        
        return{
            "status": status.HTTP_200_OK,
            "message": "All details found",
            "data": customer_list
        }
    
    except HTTPException as e:
        db.rollback()
        return{
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }
    

@router.put("/soft_delete/{customer_id}")
def soft_delete_entry(customer_id: int, db:Session = Depends(get_db)):
    try:
        customer = db.query(CustomerMaster).filter(CustomerMaster.id == customer_id).first()

        if not customer:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Customer not found"
            )
        
        if customer.is_delete == True:
            return {
                "status": status.HTTP_204_NO_CONTENT,
                "message": "Customer already deleted"
            }
        
        customer.is_delete = True
        db.commit()

        return {
            "status": status.HTTP_200_OK,
            "message": "Customer deleted succesfully"
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
    

@router.put("/update/{customer_master_id}")
def update_customer_entry(customer_master_id: int, data:UpdateCustomer, db:Session = Depends(get_db)):
    try:
        customer = db.query(CustomerMaster).filter(CustomerMaster.id == customer_master_id, CustomerMaster.is_delete == 0).first()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found or has been deleted"
            )

        if data.name is not None:
            customer.name = data.name
        if data.address is not None:
            customer.address = data.address
        
        customer.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(customer)

        return {
            "status": status.HTTP_200_OK,
            "message": "Customer updated successfully",
            "data": customer
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