from pydantic import BaseModel

class CreateSection(BaseModel):
    section_name: str
    section_desc: str