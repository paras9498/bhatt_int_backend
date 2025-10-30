from pydantic import BaseModel
from datetime import date
from typing import List
from decimal import Decimal

class CreateExbondChild(BaseModel):
    inbond_master_id: int
    material_master_id: int
    section_master_id: int
    customer_master_id: int
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