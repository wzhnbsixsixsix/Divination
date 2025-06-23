from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    divinations = relationship("Divination", back_populates="user")


class Divination(Base):
    """占卜记录模型"""
    __tablename__ = "divinations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 占卜内容
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    
    # API调用信息
    model_used = Column(String(100), default="deepseek/deepseek-chat-v3-0324")
    language = Column(String(10), default="zh-CN")
    
    # 用户信息(用于匿名用户)
    session_id = Column(String(100), nullable=True, index=True)
    user_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="divinations")


class UsageLog(Base):
    """使用日志模型"""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    # 请求信息
    endpoint = Column(String(100), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    
    # 用户信息
    user_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 