from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from decimal import Decimal

class CreateDispatchChild(BaseModel):
    exbond_child_id: int
    dispatch_date: date
    dispatch_weight: Decimal
    truck_no: str

class CreateDispatchMaster(BaseModel):
    total_dispatch_weight: Decimal
    dispatchchild: List[CreateDispatchChild]

class UpdateDispatchChild(BaseModel):
    dispatch_child_id: Optional[int] = None
    dispatch_date: Optional[date] = None
    dispatch_weight: Optional[Decimal] = None
    truck_no: Optional[str] = None

class UpdateDispatchMaster(BaseModel):
    total_dispatch_weight: Optional[Decimal] = None
    dispatchchild: Optional[List[UpdateDispatchChild]] = None