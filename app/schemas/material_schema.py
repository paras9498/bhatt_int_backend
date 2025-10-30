from pydantic import BaseModel
from decimal import Decimal

class CreateMaterial(BaseModel):
    name: str
    short_code: str
    hsn_code: str
    basic_duty_pr: Decimal
    social_duty_pr: Decimal
    igst_pr: Decimal
    