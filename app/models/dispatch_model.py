from app.database import Base
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Boolean, func
from datetime import datetime
from decimal import Decimal

class DispatchMaster(Base):
    __tablename__ = "dispatch_master"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_id = Column(Integer, unique=True, index=True)
    total_dispatch_weight = Column(Numeric(18,2), default=Decimal("0.00"))
    is_delete = Column(Boolean, default=False)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

class DispatchChild(Base):
    __tablename__ = "dispatch_child"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_master_id = Column(Integer)
    exbond_child_id = Column(Integer, index=True)
    dispatch_date = Column(Date)
    dispatch_weight = Column(Numeric(18,2), default=Decimal('0.00'))
    truck_no = Column(String(100))
    is_delete = Column(Boolean, default=False)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)