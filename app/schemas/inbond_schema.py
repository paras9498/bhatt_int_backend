from pydantic import BaseModel
from datetime import date
from typing import List, Optional
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

class UpdateInbondChild(BaseModel):
    id: Optional[int] = None
    material_master_id: Optional[int] = None
    duty_inbond_amount_inr: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    invoice_amount_usd: Optional[Decimal] = None
    assessment_amount_inr: Optional[Decimal] = None
    dollar_inr: Optional[Decimal] = None
    price: Optional[Decimal] = None
    material_amount_usd: Optional[Decimal] = None

class UpdateInbond(BaseModel):
    bi_number: Optional[str] = None
    be_number: Optional[str] = None
    be_date: Optional[date] = None
    inbond_date: Optional[date] = None
    total_duty_inbond_amount_inr: Optional[Decimal] = None
    total_weight: Optional[Decimal] = None
    total_assessment_amount_inr: Optional[Decimal] = None
    total_material_amount_usd: Optional[Decimal] = None
    inbondchild: List[UpdateInbondChild]