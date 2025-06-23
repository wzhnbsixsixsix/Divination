from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..schemas import DivinationRequest, DivinationResponse, APIResponse, UserUsage, DivinationHistory
from ..services.divination_service import divination_service

router = APIRouter(prefix="/api", tags=["占卜"])


def get_client_info(request: Request):
    """获取客户端信息"""
    return {
        "user_ip": request.client.host,
        "user_agent": request.headers.get("user-agent", "")
    }


@router.post("/divination", response_model=APIResponse)
async def create_divination(
    request_data: DivinationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    创建占卜请求
    
    - **question**: 用户问题（必填）
    - **language**: 语言代码，默认zh-CN
    - **session_id**: 会话ID，用于匿名用户识别
    """
    try:
        client_info = get_client_info(request)
        
        # 如果没有session_id，生成一个新的
        session_id = request_data.session_id
        if not session_id:
            session_id = divination_service.generate_session_id()
        
        # 创建占卜记录
        divination = await divination_service.create_divination(
            db=db,
            question=request_data.question,
            language=request_data.language,
            session_id=session_id,
            user_ip=client_info["user_ip"],
            user_agent=client_info["user_agent"]
        )
        
        return APIResponse(
            success=True,
            message="占卜完成",
            data={
                "id": divination.id,
                "question": divination.question,
                "answer": divination.answer,
                "session_id": session_id,
                "created_at": divination.created_at.isoformat()
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/divination/usage", response_model=APIResponse)
async def get_usage_stats(
    session_id: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取使用统计
    
    - **session_id**: 会话ID（匿名用户）
    - **user_id**: 用户ID（注册用户）
    """
    try:
        stats = divination_service.get_usage_stats(
            db=db,
            user_id=user_id,
            session_id=session_id
        )
        
        return APIResponse(
            success=True,
            message="获取成功",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/divination/history", response_model=APIResponse)
async def get_divination_history(
    session_id: Optional[str] = None,
    user_id: Optional[int] = None,
    page: int = 1,
    size: int = 10,  
    db: Session = Depends(get_db)
):
    """
    获取占卜历史记录
    
    - **session_id**: 会话ID（匿名用户）
    - **user_id**: 用户ID（注册用户）
    - **page**: 页码，从1开始
    - **size**: 每页数量，默认10
    """
    try:
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = 10
            
        history = divination_service.get_user_divination_history(
            db=db,
            user_id=user_id,
            session_id=session_id,
            page=page,
            size=size
        )
        
        return APIResponse(
            success=True,
            message="获取成功",
            data={
                "divinations": [
                    {
                        "id": d.id,
                        "question": d.question,
                        "answer": d.answer,
                        "created_at": d.created_at.isoformat()
                    }
                    for d in history.divinations
                ],
                "total": history.total,
                "page": history.page,
                "size": history.size,
                "has_next": history.has_next
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.post("/divination/session", response_model=APIResponse)
async def create_session():
    """
    创建新的会话ID
    用于前端匿名用户标识
    """
    try:
        session_id = divination_service.generate_session_id()
        
        return APIResponse(
            success=True,
            message="会话创建成功",
            data={
                "session_id": session_id
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}") 