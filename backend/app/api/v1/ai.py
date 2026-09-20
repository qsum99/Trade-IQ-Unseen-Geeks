"""
AI Research API Routes
=======================
POST /ai/research
POST /ai/explain
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.schemas.common import APIResponse, make_request_id
from app.ai.assistant import research_query, explain_backtest

router = APIRouter(prefix="/ai", tags=["AI Research"])


class AIResearchRequest(BaseModel):
    message: str
    conversation_history: list[dict] | None = None


class AIExplainRequest(BaseModel):
    backtest_result: dict


@router.post("/research", response_model=APIResponse)
async def ai_research(request: AIResearchRequest):
    """Natural-language research query via AI assistant."""
    result = await research_query(
        user_message=request.message,
        conversation_history=request.conversation_history,
    )

    return APIResponse(
        success=True,
        data=result,
        meta={"request_id": make_request_id()},
    )


@router.post("/research/stream")
async def ai_research_stream(request: AIResearchRequest):
    """
    Streaming endpoint providing real-time background progress events (SSE)
    followed by the complete research response and live prices.
    """
    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    async def event_generator():
        try:
            # Emit Step 1: Query Understanding
            yield f"data: {json.dumps({'type': 'step', 'step': {'name': 'Query Understanding & Intent Extraction', 'status': 'running', 'details': f'Parsing user inquiry: {request.message[:60]}...'}})}\n\n"
            await asyncio.sleep(0.1)

            # Emit Step 2: API & Tool Resolution
            yield f"data: {json.dumps({'type': 'step', 'step': {'name': 'Market Data Routing & Live API Fetch', 'status': 'running', 'details': 'Executing real-time API queries via CoinGecko / Market Gateway...'}})}\n\n"

            # Execute research query
            result = await research_query(
                user_message=request.message,
                conversation_history=request.conversation_history,
            )

            # Emit Live Prices if available
            if result.get("live_prices"):
                yield f"data: {json.dumps({'type': 'live_prices', 'prices': result['live_prices']})}\n\n"

            # Emit final completed result
            yield f"data: {json.dumps({'type': 'complete', 'data': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/explain", response_model=APIResponse)
async def ai_explain(request: AIExplainRequest):
    """AI-generated explanation of backtest results."""
    explanation = await explain_backtest(request.backtest_result)

    return APIResponse(
        success=True,
        data={"explanation": explanation},
        meta={"request_id": make_request_id()},
    )

