"""
통합 마케팅 도구 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import logging

from app.services.marketing_tools import get_marketing_tools_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketing-tools", tags=["marketing-tools"])

class BacklinkRequest(BaseModel):
    keywords: List[str]
    limit: int = Field(default=10, ge=1, le=20)

class OutreachEmailRequest(BaseModel):
    target_domain: str
    our_site: str
    topic: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None

class CampaignRequest(BaseModel):
    goal: str
    budget: Optional[int] = None
    timeline: str

@router.post("/backlink-opportunities")
async def find_backlink_opportunities(request: BacklinkRequest):
    """백링크 기회 발견"""
    try:
        service = get_marketing_tools_service()
        opportunities = await service.find_backlink_opportunities(
            request.keywords, request.limit
        )
        return {
            "success": True,
            "total": len(opportunities),
            "opportunities": [
                {
                    "domain": opp.domain,
                    "page_authority": opp.page_authority,
                    "opportunity_type": opp.opportunity_type,
                    "contact_email": opp.contact_email,
                    "outreach_template": opp.outreach_template
                }
                for opp in opportunities
            ]
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-outreach-email")
async def generate_outreach_email(request: OutreachEmailRequest):
    """아웃리치 이메일 생성"""
    try:
        service = get_marketing_tools_service()
        email = await service.generate_outreach_email(
            request.target_domain, request.our_site, request.topic
        )
        return {"success": True, "email": email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-assistant/chat")
async def chat_with_ai(request: ChatRequest):
    """AI 마케팅 어시스턴트 채팅"""
    try:
        service = get_marketing_tools_service()
        response = await service.chat_with_ai_assistant(
            request.message, request.history
        )
        return {"success": True, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest-campaign")
async def suggest_campaign(request: CampaignRequest):
    """마케팅 캠페인 제안"""
    try:
        service = get_marketing_tools_service()
        campaign = await service.suggest_marketing_campaign(
            request.goal, request.budget, request.timeline
        )
        return {"success": True, "campaign": campaign}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/features")
async def get_features():
    """기능 목록"""
    return {
        "backlink_building": {
            "name": "백링크 자동 구축",
            "description": "키워드 기반 백링크 기회 발견 및 아웃리치",
            "endpoints": ["/backlink-opportunities", "/generate-outreach-email"]
        },
        "ai_assistant": {
            "name": "AI 마케팅 어시스턴트",
            "description": "자연어로 마케팅 조언 받기",
            "endpoints": ["/ai-assistant/chat", "/suggest-campaign"]
        }
    }
