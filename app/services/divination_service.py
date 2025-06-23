from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, Tuple
import uuid
from datetime import datetime, timedelta

from ..models import Divination, User, UsageLog
from ..schemas import DivinationCreate, DivinationHistory
from ..config import settings
from .openrouter_service import openrouter_service


class DivinationService:
    """占卜业务逻辑服务"""
    
    def __init__(self):
        self.free_limit = settings.free_usage_limit
    
    async def check_usage_limit(
        self, 
        db: Session, 
        user_id: Optional[int] = None, 
        session_id: Optional[str] = None
    ) -> Tuple[bool, int]:
        """
        检查使用限制
        返回: (是否可以使用, 剩余次数)
        """
        if user_id:
            # 注册用户检查
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, 0
            
            if user.is_premium:
                return True, -1  # 无限次数
            
            remaining = max(0, self.free_limit - user.usage_count)
            return remaining > 0, remaining
        
        elif session_id:
            # 匿名用户检查（基于session_id）
            usage_count = db.query(func.count(Divination.id)).filter(
                Divination.session_id == session_id
            ).scalar()
            
            remaining = max(0, self.free_limit - usage_count)
            return remaining > 0, remaining
        
        return False, 0
    
    async def create_divination(
        self,
        db: Session,
        question: str,
        language: str = "en",
        divination_type: str = "tarot",
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Divination:
        """创建占卜记录"""
        
        print(f"🎯 [调试] 创建占卜记录: question='{question}', language='{language}', divination_type='{divination_type}'")
        
        # 1. 检查使用限制
        can_use, remaining = await self.check_usage_limit(db, user_id, session_id)
        if not can_use:
            raise ValueError("已达到免费使用次数限制，请升级为高级用户")
        
        # 2. 调用占卜API获取结果 - 使用传入的divination_type
        try:
            print(f"📞 [调试] 调用OpenRouter服务获取占卜结果...")
            answer, prompt_info = await openrouter_service.get_divination_response(
                db=db,
                question=question,
                language=language,
                divination_type=divination_type
            )
            
            print(f"📋 [调试] 提示词信息: {prompt_info}")
            
            if not answer:
                # 如果API调用失败，使用备用回答
                answer = f"根据您的问题「{question}」，我为您解读如下：\n\n当前的情况需要您保持耐心和信心。虽然前路可能充满不确定性，但正是这种不确定性为您带来了无限的可能性。\n\n建议您：\n1. 保持积极的心态\n2. 相信自己的直觉\n3. 适时寻求他人的建议\n4. 把握当下的机会\n\n请记住，命运掌握在您自己的手中。"
                print(f"⚠️ [调试] API调用失败，使用备用回答")
                
        except Exception as e:
            print(f"💥 [调试] OpenRouter API调用异常: {e}")
            # 使用备用回答
            answer = f"根据您的问题「{question}」，我为您解读如下：\n\n当前的情况需要您保持耐心和信心。虽然前路可能充满不确定性，但正是这种不确定性为您带来了无限的可能性。\n\n建议您：\n1. 保持积极的心态\n2. 相信自己的直觉\n3. 适时寻求他人的建议\n4. 把握当下的机会\n\n请记住，命运掌握在您自己的手中。"
        
        # 3. 创建占卜记录
        divination = Divination(
            user_id=user_id,
            session_id=session_id,
            question=question,
            answer=answer,
            language=language,
            user_ip=user_ip,
            user_agent=user_agent
        )
        
        db.add(divination)
        
        # 4. 更新用户使用次数
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.usage_count += 1
                db.add(user)
        
        # 5. 记录使用日志
        usage_log = UsageLog(
            user_id=user_id,
            session_id=session_id,
            endpoint="/api/divination",
            method="POST",
            status_code=200,
            user_ip=user_ip,
            user_agent=user_agent
        )
        db.add(usage_log)
        
        try:
            db.commit()
            db.refresh(divination)
            return divination
        except Exception as e:
            db.rollback()
            print(f"数据库提交失败: {e}")
            raise ValueError(f"保存占卜记录失败: {str(e)}")
    
    def get_user_divination_history(
        self,
        db: Session,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> DivinationHistory:
        """获取用户占卜历史"""
        
        query = db.query(Divination)
        
        if user_id:
            query = query.filter(Divination.user_id == user_id)
        elif session_id:
            query = query.filter(Divination.session_id == session_id)
        else:
            # 没有用户标识，返回空结果
            return DivinationHistory(
                divinations=[],
                total=0,
                page=page,
                size=size,
                has_next=False
            )
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        divinations = query.order_by(desc(Divination.created_at))\
                          .offset((page - 1) * size)\
                          .limit(size)\
                          .all()
        
        has_next = total > page * size
        
        return DivinationHistory(
            divinations=divinations,
            total=total,
            page=page,
            size=size,
            has_next=has_next
        )
    
    def get_usage_stats(
        self,
        db: Session,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> dict:
        """获取使用统计"""
        
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "usage_count": 0,
                    "remaining_count": 0,
                    "is_premium": False
                }
            
            remaining = max(0, self.free_limit - user.usage_count) if not user.is_premium else -1
            
            return {
                "user_id": user_id,
                "usage_count": user.usage_count,
                "remaining_count": remaining,
                "is_premium": user.is_premium
            }
        
        elif session_id:
            usage_count = db.query(func.count(Divination.id)).filter(
                Divination.session_id == session_id
            ).scalar()
            
            remaining = max(0, self.free_limit - usage_count)
            
            return {
                "session_id": session_id,
                "usage_count": usage_count,
                "remaining_count": remaining,
                "is_premium": False
            }
        
        return {
            "usage_count": 0,
            "remaining_count": 0,
            "is_premium": False
        }
    
    def get_daily_stats(self, db: Session, days: int = 7) -> list:
        """获取每日统计数据"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        stats = db.query(
            func.date(Divination.created_at).label('date'),
            func.count(Divination.id).label('count')
        ).filter(
            Divination.created_at >= start_date
        ).group_by(
            func.date(Divination.created_at)
        ).order_by('date').all()
        
        return [
            {
                "date": stat.date.strftime('%Y-%m-%d'),
                "count": stat.count
            }
            for stat in stats
        ]
    
    @staticmethod
    def generate_session_id() -> str:
        """生成会话ID"""
        return str(uuid.uuid4())


# 全局服务实例
divination_service = DivinationService() 