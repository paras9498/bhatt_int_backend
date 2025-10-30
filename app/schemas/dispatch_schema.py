from pydantic import BaseModel
from datetime import date
from typing import List
from decimal import Decimal

class CreateDispatchChild(BaseModel):
    exbond_child_id: int
    dispatch_date: date
    dispatch_weight: Decimal
    truck_no: str

class CreateDispatchMaster(BaseModel):
    total_dispatch_weight: Decimal
    dispatchchild: List[CreateDispatchChild]