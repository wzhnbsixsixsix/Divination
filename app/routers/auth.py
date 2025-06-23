# DivinationBackend/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from ..database import get_db
from ..schemas import APIResponse
from ..models import User
from ..services.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer(auto_error=False)

# 请求模型
class UserRegister(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选）"""
    if not credentials:
        return None
        
    token = credentials.credentials
    token_data = auth_service.verify_access_token(token)
    
    if not token_data:
        return None
    
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user or not user.is_active:
        return None
    
    return user

@router.post("/register", response_model=APIResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        # 检查邮箱是否已存在
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="邮箱已被注册")
        
        # 创建新用户
        new_user = User(
            email=user_data.email,
            name=user_data.name,
            password_hash=user_data.password,  # 简化版，实际应该加密
            is_active=True,
            is_verified=True,
            usage_count=0,
            is_premium=False
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return APIResponse(
            success=True,
            message="注册成功",
            data={
                "user_id": new_user.id,
                "email": new_user.email,
                "name": new_user.name,
                "usage_count": new_user.usage_count
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"注册错误: {e}")
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

@router.post("/login", response_model=APIResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        user = db.query(User).filter(User.email == user_data.email).first()
        if not user or user.password_hash != user_data.password:
            raise HTTPException(status_code=400, detail="邮箱或密码错误")
        
        return APIResponse(
            success=True,
            message="登录成功",
            data={
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "usage_count": user.usage_count,
                "is_premium": user.is_premium
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"登录错误: {e}")
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")

@router.post("/session", response_model=APIResponse)
async def create_session():
    """创建匿名会话"""
    try:
        import uuid
        session_id = str(uuid.uuid4())
        return APIResponse(
            success=True,
            message="会话创建成功",
            data={"session_id": session_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")

@router.post("/refresh", response_model=APIResponse)
async def refresh_token(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    refresh_token = request_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="缺少刷新令牌")
    
    token_data = auth_service.refresh_access_token(db, refresh_token)
    if not token_data:
        raise HTTPException(status_code=401, detail="无效的刷新令牌")
    
    return APIResponse(
        success=True,
        message="令牌刷新成功",
        data=token_data
    )

@router.get("/me", response_model=APIResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")
        
    return APIResponse(
        success=True,
        message="获取成功",
        data={
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "avatar_url": current_user.avatar_url,
            "is_premium": current_user.is_premium,
            "is_verified": current_user.is_verified,
            "usage_count": current_user.usage_count,
            "created_at": current_user.created_at.isoformat()
        }
    )

@router.post("/logout", response_model=APIResponse)
async def logout(
    request_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户登出"""
    refresh_token = request_data.get("refresh_token")
    if refresh_token:
        auth_service.revoke_refresh_token(db, refresh_token)
    
    return APIResponse(
        success=True,
        message="登出成功"
    )