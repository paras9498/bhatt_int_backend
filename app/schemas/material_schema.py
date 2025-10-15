from pydantic import BaseModel

class CreateMaterial(BaseModel):
    name: str
    short_code: str
    hsn_code: str
    basic_duty_pr: float
    social_duty_pr: float
    igst_pr: float
    