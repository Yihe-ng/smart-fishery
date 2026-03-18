from fastapi import APIRouter

from app.ai.context_builder import build_bootstrap_payload, build_page_context
from app.ai.llm_service import build_manual_feeding_preview, invoke_llm
from app.ai.schemas import (
    BootstrapResponse,
    InvokeRequest,
    InvokeResponse,
    ManualFeedingPreviewRequest,
    ManualFeedingPreviewResponse,
    PageContextRequest,
    PageContextSummary,
    SuggestionResponse,
)
from app.ai.suggestion_service import build_feeding_suggestions
from app.ai.tool_registry import get_tool_schemas
from app.schemas.base import BaseResponse

router = APIRouter()


@router.post("/agent/bootstrap", response_model=BaseResponse[BootstrapResponse])
async def bootstrap_agent(request: PageContextRequest):
    payload = build_bootstrap_payload(request)
    payload["toolSchemas"] = get_tool_schemas(request.pageId)
    return BaseResponse[BootstrapResponse](
        code=200,
        msg="AI bootstrap success",
        data=BootstrapResponse(**payload),
    )


@router.post("/agent/context", response_model=BaseResponse[PageContextSummary])
async def refresh_page_context(request: PageContextRequest):
    context = build_page_context(request)
    return BaseResponse[PageContextSummary](
        code=200,
        msg="AI context success",
        data=context,
    )


@router.post("/agent/invoke", response_model=BaseResponse[InvokeResponse])
async def invoke_agent(request: InvokeRequest):
    response = invoke_llm(request)
    return BaseResponse[InvokeResponse](
        code=200,
        msg="AI invoke success",
        data=response,
    )


@router.post("/suggestions/feeding", response_model=BaseResponse[SuggestionResponse])
async def get_feeding_suggestions(request: PageContextRequest):
    response = build_feeding_suggestions(request.pondId)
    return BaseResponse[SuggestionResponse](
        code=200,
        msg="AI suggestions success",
        data=response,
    )


@router.post(
    "/actions/manual-feeding/preview",
    response_model=BaseResponse[ManualFeedingPreviewResponse],
)
async def preview_manual_feeding(request: ManualFeedingPreviewRequest):
    preview = build_manual_feeding_preview(request.pondId, request.amount)
    preview.sessionId = request.sessionId
    return BaseResponse[ManualFeedingPreviewResponse](
        code=200,
        msg="AI preview success",
        data=preview,
    )
