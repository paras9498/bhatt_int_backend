from pydantic import BaseModel
from typing import Optional

class CreateCustomer(BaseModel):
    name: str
    address: str

class UpdateCustomer(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None