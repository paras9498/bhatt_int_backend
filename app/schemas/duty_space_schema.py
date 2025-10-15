from pydantic import BaseModel
from datetime import date
from decimal import Decimal


class CreateExbondAdjustment(BaseModel):
    inbond_master_id: int
    adjustment_amount_inr: Decimal
    date_of_adjustment: date
    type: str