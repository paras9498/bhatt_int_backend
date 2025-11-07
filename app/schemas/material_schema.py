from pydantic import BaseModel
from decimal import Decimal
from typing import Optional

class CreateMaterial(BaseModel):
    name: str
    short_code: str
    hsn_code: str
    basic_duty_pr: Decimal
    social_duty_pr: Decimal
    igst_pr: Decimal
    

class UpdateMaterial(BaseModel):
    name: Optional[str] = None
    short_code: Optional[str] = None
    hsn_code: Optional[str] = None
    basic_duty_pr: Optional[Decimal] = None
    social_duty_pr: Optional[Decimal] = None
    igst_pr: Optional[Decimal] = None 