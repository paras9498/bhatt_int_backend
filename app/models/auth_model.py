from app.database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func
from datetime import datetime

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    user_type = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    # role = Column(String(200), nullable=True)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

class Tokens(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    u_id = Column(Integer, nullable=False)
    access_token = Column(Text)
    refresh_token = Column(Text)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate=func.now())
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)   