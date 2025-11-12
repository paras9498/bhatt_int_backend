from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, func
from datetime import datetime
from decimal import Decimal

class MaterialMaster(Base):
    __tablename__ = "material_master"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    short_code = Column(String(50))
    hsn_code = Column(String(50))
    basic_duty_pr = Column(Numeric(18, 2), default=Decimal('0.00'))
    social_duty_pr = Column(Numeric(18, 2), default=Decimal('0.00'))
    igst_pr = Column(Numeric(18, 2), default=Decimal('0.00'))
    is_delete = Column(Boolean, default=False)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)