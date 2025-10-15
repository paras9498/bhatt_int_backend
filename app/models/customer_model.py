from app.database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

class CustomerMaster(Base):
    __tablename__ = "customer_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
