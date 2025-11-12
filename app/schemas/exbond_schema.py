from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from decimal import Decimal

class CreateExbondChild(BaseModel):
    inbond_master_id: int
    material_master_id: int
    section_master_id: int
    customer_master_id: int
    inbond_child_id:int
    be_number: str
    be_date: date
    type: str
    resultant: str
    duty_exbond_amount_inr: Decimal
    dollar_inr: Decimal
    rate: Decimal
    weight: Decimal
    invoice_amount_inr: Decimal
    #dispatch_date: date
    #dipspatch_weight: float
    #truck_number: str

class CreateExbondMaster(BaseModel):
    total_duty_exbond_amount_inr: Decimal
    total_weight: Decimal
    total_invoice_amount_inr: Decimal
    #total_dispatch_weight: float
    exbondchild: List[CreateExbondChild]

class UpdateExbondChild(BaseModel):
    id: Optional[int] = None
    inbond_master_id: Optional[int] = None
    material_master_id: Optional[int] = None
    section_master_id: Optional[int] = None
    customer_master_id: Optional[int] = None
    be_number: Optional[str] = None
    be_date: Optional[date] = None
    type: Optional[str] = None
    resultant: Optional[str] = None
    duty_exbond_amount_inr: Optional[Decimal] = None
    dollar_inr: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    invoice_amount_inr: Optional[Decimal] = None

class UpdateExbondMaster(BaseModel):
    total_duty_exbond_amount_inr: Optional[Decimal] = None
    total_weight: Optional[Decimal] = None
    total_invoice_amount_inr: Optional[Decimal] = None
    exbondchild: Optional[List[UpdateExbondChild]] = None