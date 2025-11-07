from pydantic import BaseModel
from typing import Optional

class CreateSection(BaseModel):
    section_name: str
    section_desc: str

class UpdateSection(BaseModel):
    section_name: Optional[str] = None
    section_desc: Optional[str] = None