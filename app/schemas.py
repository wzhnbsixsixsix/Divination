from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


# ============ 基础模型 ============

class DivinationRequest(BaseModel):
    """占卜请求模型"""
    question: str = Field(..., min_length=1, max_length=1000, description="用户问题")
    language: Optional[str] = Field("zh-CN", description="语言代码")
    session_id: Optional[str] = Field(None, description="会话ID")


class DivinationResponse(BaseModel):
    """占卜响应模型"""
    id: int
    question: str
    answer: str
    model_used: str
    created_at: datetime
    
    class Config:
        orm_mode = True


# ============ 用户相关模型 ============

class UserBase(BaseModel):
    """用户基础模型"""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """创建用户模型"""
    pass


class UserUpdate(UserBase):
    """更新用户模型"""
    pass


class User(UserBase):
    """用户响应模型"""
    id: int
    usage_count: int
    is_premium: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class UserUsage(BaseModel):
    """用户使用统计模型"""
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    usage_count: int
    remaining_count: int
    is_premium: bool = False
    

# ============ 占卜记录相关模型 ============

class DivinationBase(BaseModel):
    """占卜记录基础模型"""
    question: str
    answer: str
    model_used: str = "deepseek/deepseek-chat-v3-0324"
    language: str = "zh-CN"


class DivinationCreate(DivinationBase):
    """创建占卜记录模型"""
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    user_ip: Optional[str] = None
    user_agent: Optional[str] = None


class Divination(DivinationBase):
    """占卜记录响应模型"""
    id: int
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


class DivinationHistory(BaseModel):
    """占卜历史列表模型"""
    divinations: List[Divination]
    total: int
    page: int
    size: int
    has_next: bool


# ============ API响应模型 ============

class APIResponse(BaseModel):
    """通用API响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None


# ============ 健康检查模型 ============

class HealthCheck(BaseModel):
    """健康检查响应模型"""
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"
    database: str = "connected" 