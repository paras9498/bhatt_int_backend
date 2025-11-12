from app.database import Base
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Boolean, func
from datetime import datetime
from decimal import Decimal

class InbondMaster(Base):
    __tablename__ = "inbond_master"

    id = Column(Integer, primary_key=True, index=True)
    bi_number = Column(String(50), unique=True)
    be_number = Column(String(50))
    be_date = Column(Date)
    inbond_date = Column(Date)
    total_duty_inbond_amount_inr = Column(Numeric(18, 2), default=Decimal('0.00'))
    total_weight = Column(Numeric(18, 2), default=Decimal('0.00'))
    total_assessment_amount_inr = Column(Numeric(18, 2), default=Decimal('0.00'))
    total_material_amount_usd = Column(Numeric(18, 2), default=Decimal('0.00'))
    is_settled = Column(Boolean, default=False)
    is_delete = Column(Boolean, default=False)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)


class InbondChild(Base):
    __tablename__ = "inbond_child"

    id = Column(Integer, primary_key=True, index=True)
    inbond_master_id = Column(Integer)
    material_master_id = Column(Integer)
    duty_inbond_amount_inr = Column(Numeric(18, 2), default=Decimal('0.00'))
    weight = Column(Numeric(18, 2), default=Decimal('0.00'))
    invoice_amount_usd = Column(Numeric(18, 2), default=Decimal('0.00'))
    assessment_amount_inr = Column(Numeric(18, 2), default=Decimal('0.00'))
    dollar_inr = Column(Numeric(18, 2), default=Decimal('0.00'))
    price = Column(Numeric(18, 2), default=Decimal('0.00'))
    material_amount_usd = Column(Numeric(18, 2), default=Decimal('0.00'))
    is_delete = Column(Boolean, default=False)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)