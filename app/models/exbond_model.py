from app.database import Base
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Boolean, func
from datetime import datetime
from decimal import Decimal

class ExbondMaster(Base):
    __tablename__ = "exbond_master"

    id = Column(Integer, primary_key=True, index=True)
    exbond_id = Column(Integer, unique=True, index=True)
    total_duty_exbond_amount_inr = Column(Numeric(18,2), default=Decimal('0.00'))
    total_weight = Column(Numeric(18,2), default=Decimal('0.00'))
    total_invoice_amount_inr = Column(Numeric(18,2), default=Decimal('0.00'))
    is_delete = Column(Boolean, default=False)
    #total_dispatch_weight = Column(Numeric(18,2), default=Decimal('0.00'))
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)


class ExbondChild(Base):
    __tablename__ = "exbond_child"

    id = Column(Integer, primary_key=True, index=True)
    exbond_master_id = Column(Integer)
    section_master_id = Column(Integer)
    material_master_id = Column(Integer)
    inbond_master_id = Column(Integer)
    inbond_child_id = Column(Integer)
    customer_master_id = Column(Integer)
    be_number = Column(String(50))
    be_date = Column(Date)
    type = Column(String(50))
    resultant = Column(String(50))
    duty_exbond_amount_inr = Column(Numeric(18,2), default=Decimal('0.00'))
    dollar_inr = Column(Numeric(18,2), default=Decimal('0.00'))
    rate = Column(Numeric(18,2), default=Decimal('0.00'))
    weight = Column(Numeric(18,2), default=Decimal('0.00'))
    invoice_amount_inr = Column(Numeric(18,2), default=Decimal('0.00'))
    is_duty_paid = Column(Boolean, default=False)
    is_dispatched = Column(Boolean, default=False)
    is_delete = Column(Boolean, default=False)
    #dispatch_date = Column(Date)
    #dispatch_weight = Column(Numeric(18,2), default=Decimal('0.00'))
    #truck_number = Column(String(50))
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)


class ExbondAdjustment(Base):
    __tablename__ = "exbond_adjustment"

    id = Column(Integer, primary_key=True, index=True)
    inbond_master_id = Column(Integer, nullable=False)
    adjustment_amount_inr = Column(Numeric(18,2), default=Decimal('0.00'))
    date_of_adjustment = Column(Date)
    type = Column(String(50))
    is_delete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)