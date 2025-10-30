from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime

class SectionMaster(Base):
    __tablename__ = "section_master"

    id = Column(Integer, primary_key=True, index=True)
    section_name = Column(String(50))
    section_desc = Column(String(225))
    is_delete = Column(Boolean, default=False)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)