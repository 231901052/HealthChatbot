from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from .db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    preferred_language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, index=True)
    direction = Column(String)  # inbound / outbound
    text = Column(Text)
    intent = Column(String, nullable=True)
    confidence = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Escalation(Base):
    __tablename__ = "escalations"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, index=True)
    payload = Column(Text)
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
