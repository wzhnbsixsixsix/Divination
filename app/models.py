from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # 认证相关字段
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    divinations = relationship("Divination", back_populates="user")


class RefreshToken(Base):
    """刷新令牌模型"""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    
    # 设备信息
    device_id = Column(String(255))
    device_name = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # 状态
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JWTBlacklist(Base):
    """JWT黑名单模型"""
    __tablename__ = "jwt_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(255), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 撤销信息
    revoke_reason = Column(String(100), default="logout")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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

class PromptTemplate(Base):
    """提示词模板模型"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(100), nullable=False)
    description = Column(Text)
    divination_type = Column(String(50), default="general")
    language = Column(String(10), nullable=False)
    
    # 提示词内容
    system_prompt = Column(Text, nullable=False)
    user_template = Column(Text, nullable=False)
    
    # 版本控制
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # 性能统计
    usage_count = Column(Integer, default=0)
    avg_rating = Column(Numeric(3, 2), default=0.00)
    success_rate = Column(Numeric(5, 2), default=0.00)
    
    # 配置参数
    temperature = Column(Numeric(3, 2), default=0.80)
    max_tokens = Column(Integer, default=1000)
    model_preference = Column(String(100))
    
    # 元数据
    created_by = Column(String(100))
    tags = Column(String(200))
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PromptUsageHistory(Base):
    """提示词使用历史模型"""
    __tablename__ = "prompt_usage_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联信息
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"))
    divination_id = Column(Integer, ForeignKey("divinations.id"))
    
    # 使用信息
    language = Column(String(10), nullable=False)
    divination_type = Column(String(50))
    
    # 实际使用的提示词内容
    actual_system_prompt = Column(Text)
    actual_user_prompt = Column(Text)
    
    # 性能指标
    response_time_ms = Column(Integer)
    token_count = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # 用户反馈
    user_rating = Column(Integer)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 