from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database import get_db
from sqlalchemy.orm import Session
from ..models.customer_model import CustomerMaster
from ..schemas.customer_schema import CreateCustomer

router = APIRouter(prefix = "/api/customer", tags = ['Customer'])


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
    

@router.get("/get_all")
def get_all_details(db:Session = Depends(get_db)):
    try:
        customers = db.query(CustomerMaster).order_by(CustomerMaster.created_at.desc()).all()

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