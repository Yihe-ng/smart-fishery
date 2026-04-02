import json

from fastapi import APIRouter, HTTPException

from app.agent.context_builder import build_bootstrap_payload, build_page_context
from app.agent.llm_service import build_manual_feeding_preview, invoke_llm
from app.agent.schemas import (
    AgentInvokeResponse,
    BootstrapResponse,
    InvokeRequest,
    ManualFeedingPreviewRequest,
    ManualFeedingPreviewResponse,
    PageContextRequest,
    PageContextSummary,
    SuggestionResponse,
    ToolExecuteRequest,
    ToolExecuteResponse,
)
from app.agent.suggestion_service import build_feeding_suggestions
from app.agent.tool_registry import run_tool
from app.schemas.base import BaseResponse

router = APIRouter()


@router.post("/agent/bootstrap", response_model=BaseResponse[BootstrapResponse])
async def bootstrap_agent(request: PageContextRequest):
    data = build_bootstrap_payload(request)
    return BaseResponse[BootstrapResponse](
        code=200,
        msg="AI bootstrap success",
        data=data,
    )


@router.post("/agent/context", response_model=BaseResponse[PageContextSummary])
async def refresh_page_context(request: PageContextRequest):
    context = build_page_context(request)
    return BaseResponse[PageContextSummary](
        code=200,
        msg="AI context success",
        data=context,
    )


@router.post("/agent/invoke", response_model=BaseResponse[AgentInvokeResponse])
async def invoke_agent(request: InvokeRequest):
    return BaseResponse[AgentInvokeResponse](
        code=200,
        msg="AI invoke success",
        data=invoke_llm(request),
    )


@router.post("/tools/{tool_name}", response_model=BaseResponse[ToolExecuteResponse])
async def execute_tool(tool_name: str, request: ToolExecuteRequest):
    try:
        result = run_tool(tool_name, **request.arguments)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Tool execution failed")
    return BaseResponse[ToolExecuteResponse](
        code=200,
        msg="Tool executed",
        data=ToolExecuteResponse(result=json.dumps(result, ensure_ascii=False)),
    )


@router.post("/suggestions/feeding", response_model=BaseResponse[SuggestionResponse])
async def get_feeding_suggestions(request: PageContextRequest):
    response = await build_feeding_suggestions(request.pondId)
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
