from datetime import datetime, timedelta
from typing import Optional, Dict
import secrets
import hashlib
import uuid
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..config import settings
from ..models import User

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """认证服务类"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    def hash_password(self, password: str) -> str:
        """加密密码"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_user(self, db: Session, email: str, password: str, name: str = None) -> User:
        """创建新用户"""
        hashed_password = self.hash_password(password)
        
        db_user = User(
            email=email,
            name=name or email.split('@')[0],
            password_hash=hashed_password,
            is_active=True,
            is_verified=False
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """验证用户登录"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user or not user.is_active:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建JWT访问令牌（存储在前端）"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # 添加JWT标准声明
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4()),  # JWT ID，用于黑名单功能
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(
        self, 
        db: Session, 
        user_id: int, 
        device_id: str = None,
        device_name: str = None,
        ip_address: str = None, 
        user_agent: str = None
    ) -> str:
        """创建刷新令牌（存储在数据库）"""
        from ..models import RefreshToken
        
        # 生成随机令牌
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # 限制每个用户的活跃会话数量
        active_sessions = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_active == True,
            RefreshToken.expires_at > datetime.utcnow()
        ).count()
        
        if active_sessions >= 5:  # 最多5个活跃会话
            # 删除最旧的会话
            oldest_session = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_active == True
            ).order_by(RefreshToken.last_used_at).first()
            
            if oldest_session:
                oldest_session.is_active = False
                db.commit()
        
        # 保存新的刷新令牌
        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=30),  # 30天有效期
            device_id=device_id or str(uuid.uuid4()),
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(db_token)
        db.commit()
        
        return token
    
    def verify_access_token(self, token: str) -> Optional[Dict]:
        """验证JWT访问令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get("type") != "access":
                return None
            
            # 检查是否在黑名单中
            jti = payload.get("jti")
            if jti and self.is_token_blacklisted(jti):
                return None
            
            user_id: int = payload.get("sub")
            if user_id is None:
                return None
                
            return {"user_id": int(user_id), "payload": payload}
            
        except JWTError:
            return None
    
    def verify_refresh_token(self, db: Session, token: str) -> Optional[int]:
        """验证刷新令牌"""
        from ..models import RefreshToken
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_active == True,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
        
        if db_token:
            # 更新最后使用时间
            db_token.last_used_at = datetime.utcnow()
            db.commit()
            return db_token.user_id
        
        return None
    
    def refresh_access_token(self, db: Session, refresh_token: str) -> Optional[Dict]:
        """使用刷新令牌生成新的访问令牌"""
        user_id = self.verify_refresh_token(db, refresh_token)
        if not user_id:
            return None
        
        # 获取用户信息
        user = db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
        
        if not user:
            return None
        
        # 生成新的访问令牌
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }
    
    def revoke_refresh_token(self, db: Session, token: str):
        """撤销刷新令牌"""
        from ..models import RefreshToken
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        
        if db_token:
            db_token.is_active = False
            db.commit()
    
    def revoke_all_user_tokens(self, db: Session, user_id: int):
        """撤销用户的所有刷新令牌"""
        from ..models import RefreshToken
        
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id
        ).update({"is_active": False})
        db.commit()
    
    def blacklist_jwt(self, db: Session, jti: str, user_id: int, reason: str = "logout"):
        """将JWT加入黑名单"""
        from ..models import JWTBlacklist
        
        # 解析JWT获取过期时间
        try:
            payload = jwt.decode(jti, options={"verify_signature": False})
            expires_at = datetime.fromtimestamp(payload.get("exp", 0))
        except:
            expires_at = datetime.utcnow() + timedelta(hours=1)
        
        blacklist_entry = JWTBlacklist(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at,
            revoke_reason=reason
        )
        db.add(blacklist_entry)
        db.commit()
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """检查JWT是否在黑名单中"""
        # 这里可以使用Redis等缓存来提高性能
        # 现在先返回False，实际应该查询数据库
        return False


# 创建服务实例
auth_service = AuthService()