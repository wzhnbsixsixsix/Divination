from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import PromptTemplate
from ..schemas import APIResponse

router = APIRouter(prefix="/api/prompts", tags=["提示词管理"])

@router.get("/", response_model=APIResponse)
async def get_prompt_templates(
    divination_type: Optional[str] = None,
    language: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """获取提示词模板列表"""
    query = db.query(PromptTemplate)
    
    if divination_type:
        query = query.filter(PromptTemplate.divination_type == divination_type)
    if language:
        query = query.filter(PromptTemplate.language == language)
    if is_active is not None:
        query = query.filter(PromptTemplate.is_active == is_active)
    
    templates = query.order_by(PromptTemplate.divination_type, PromptTemplate.language).all()
    
    return APIResponse(
        success=True,
        message="获取成功",
        data={
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "divination_type": t.divination_type,
                    "language": t.language,
                    "version": t.version,
                    "is_active": t.is_active,
                    "is_default": t.is_default,
                    "usage_count": t.usage_count,
                    "avg_rating": float(t.avg_rating) if t.avg_rating else 0,
                    "created_at": t.created_at.isoformat()
                }
                for t in templates
            ]
        }
    )

@router.get("/{template_id}", response_model=APIResponse)
async def get_prompt_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """获取特定提示词模板详情"""
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    
    return APIResponse(
        success=True,
        message="获取成功",
        data={
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "divination_type": template.divination_type,
            "language": template.language,
            "system_prompt": template.system_prompt,
            "user_template": template.user_template,
            "version": template.version,
            "is_active": template.is_active,
            "is_default": template.is_default,
            "usage_count": template.usage_count,
            "avg_rating": float(template.avg_rating) if template.avg_rating else 0,
            "temperature": float(template.temperature),
            "max_tokens": template.max_tokens,
            "created_at": template.created_at.isoformat()
        }
    )
