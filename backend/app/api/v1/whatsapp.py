"""API Endpoints for WhatsApp Morning Market Briefing & Subscription Service."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.whatsapp_service import (
    get_live_market_briefing_data,
    format_whatsapp_message,
    generate_whatsapp_urls,
    subscribe_phone,
    get_all_subscribers,
    send_test_briefing,
)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


class SubscribeRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number with or without country code", min_length=7, max_length=20)
    name: Optional[str] = Field(default="Trader", description="User display name")
    country_code: Optional[str] = Field(default="+91", description="Country dial code (e.g. +91, +1, +44)")
    notify_time: Optional[str] = Field(default="07:00", description="Daily notification time in 24h format")


class SendTestRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to send preview test to", min_length=7, max_length=20)
    name: Optional[str] = Field(default="Trader", description="User display name")


@router.get("/preview")
def preview_morning_briefing(
    phone: Optional[str] = Query(default=None, description="Optional phone number to generate personal WhatsApp links")
):
    """Compile and return the live 7:00 AM market update with live prices, trends, and top 5 news."""
    try:
        briefing_data = get_live_market_briefing_data()
        formatted_message = format_whatsapp_message(briefing_data)
        
        sample_phone = phone if phone else "919876543210"
        urls = generate_whatsapp_urls(sample_phone, formatted_message)

        return {
            "success": True,
            "data": {
                "briefing": briefing_data,
                "message_text": formatted_message,
                "sample_dispatch_urls": urls,
                "schedule_time": "07:00 AM IST / UTC+05:30 Daily",
                "asset_count": len(briefing_data.get("assets", [])),
                "news_count": len(briefing_data.get("news", [])),
            },
            "meta": {
                "status": "live_realtime",
                "source": "yahoo_finance_and_financial_wire"
            },
            "error": None,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to compile morning briefing: {str(exc)}")


@router.post("/subscribe")
def register_whatsapp_subscriber(req: SubscribeRequest):
    """Register a user's phone number to receive the daily 7:00 AM market update."""
    try:
        subscriber = subscribe_phone(
            phone_number=req.phone_number,
            name=req.name,
            notify_time=req.notify_time or "07:00",
            country_code=req.country_code or "+91"
        )
        briefing_data = get_live_market_briefing_data()
        formatted_message = format_whatsapp_message(briefing_data)
        urls = generate_whatsapp_urls(subscriber["clean_phone"], formatted_message)

        return {
            "success": True,
            "data": {
                "message": f"Successfully subscribed {subscriber['phone']} for daily 07:00 AM market updates!",
                "subscriber": subscriber,
                "dispatch_urls": urls,
                "preview_message": formatted_message,
            },
            "error": None,
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to subscribe phone: {str(exc)}")


@router.post("/send-test")
def send_instant_test(req: SendTestRequest):
    """Send an immediate test market briefing to the provided phone number."""
    try:
        result = send_test_briefing(phone_number=req.phone_number, name=req.name)
        return {
            "success": True,
            "data": result,
            "error": None,
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to dispatch test briefing: {str(exc)}")


@router.get("/subscribers")
def list_subscribers():
    """Retrieve subscriber count and anonymized subscriber list."""
    try:
        subs = get_all_subscribers()
        sanitized = []
        for s in subs:
            phone = s.get("clean_phone", "")
            masked_phone = f"+{phone[:3]}•••••{phone[-3:]}" if len(phone) >= 6 else phone
            sanitized.append({
                "id": s.get("id"),
                "name": s.get("name"),
                "masked_phone": masked_phone,
                "notify_time": s.get("notify_time"),
                "is_active": s.get("is_active", True),
                "subscribed_at": s.get("subscribed_at"),
                "last_sent_at": s.get("last_sent_at"),
            })

        return {
            "success": True,
            "data": {
                "total_subscribers": len(subs),
                "subscribers": sanitized,
            },
            "error": None,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve subscribers: {str(exc)}")
