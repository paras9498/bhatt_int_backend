from pydantic import BaseModel
from datetime import date
from typing import List
from decimal import Decimal

class CreateInbondChild(BaseModel):
    material_master_id: int
    duty_inbond_amount_inr: Decimal
    weight: Decimal
    invoice_amount_usd: Decimal
    assessment_amount_inr: Decimal
    dollar_inr: Decimal
    price: Decimal
    material_amount_usd: Decimal

class CreateInbond(BaseModel):
    bi_number: str
    be_number: str
    be_date: date
    inbond_date: date
    total_duty_inbond_amount_inr: Decimal
    total_weight: Decimal
    total_assessment_amount_inr: Decimal
    total_material_amount_usd: Decimal
    inbondchild: List[CreateInbondChild]