from pydantic import BaseModel
from datetime import date
from typing import List

class CreateCustomer(BaseModel):
    name: str
    address: str