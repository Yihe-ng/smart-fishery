from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


PageId = Literal[
    "global-chat", "fishery-dashboard", "feeding", "water-quality", "growth"
]
EnvironmentMode = Literal["mock", "real"]
Severity = Literal["info", "warning", "critical"]
RiskLevel = Literal["low", "warning", "critical"]
Role = Literal["system", "user", "assistant", "tool"]


class SessionPolicy(BaseModel):
    persistent: bool = False
    resumable: bool = False
    persistenceReserved: bool = True


class UICapabilities(BaseModel):
    canExecute: bool = False
    canPreview: bool = True
    showAutomationTab: bool = True
    showSuggestionPanel: bool = False


class PageContextRequest(BaseModel):
    pageId: PageId
    routePath: str
    pondId: Optional[str] = None
    currentIndex: Optional[int] = None
    selection: Optional[Dict[str, Any]] = None


class CurrentPageSummary(BaseModel):
    pageId: PageId
    routePath: str
    selection: Dict[str, Any] = Field(default_factory=dict)


class PondSummary(BaseModel):
    pondId: str
    name: str
    sourceMode: EnvironmentMode


class MetricSummary(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    status: Literal["normal", "warning", "critical"]


class AlertSummary(BaseModel):
    total: int
    critical: int
    warning: int
    latestTitles: List[str]


class DeviceStatusSummary(BaseModel):
    onlineCount: int
    offlineCount: int
    feederStatus: str
    cameraStatus: str


class PageContextSummary(BaseModel):
    contextVersion: str
    sourceMode: EnvironmentMode
    currentIndex: Optional[int] = None
    currentPage: CurrentPageSummary
    pond: PondSummary
    keyMetrics: List[MetricSummary]
    alertDigest: AlertSummary
    deviceStatus: DeviceStatusSummary
    updatedAt: str


class BootstrapResponse(BaseModel):
    environmentMode: EnvironmentMode
    systemInstructions: str
    pageInstructions: str
    pageContextSummary: PageContextSummary
    allowedTools: List[str]
    toolSchemas: List[Dict[str, Any]]
    uiCapabilities: UICapabilities
    sessionPolicy: SessionPolicy


class ChatMessage(BaseModel):
    role: Role
    content: str


class InvokeRequest(BaseModel):
    pageId: PageId
    messages: List[ChatMessage]
    contextVersion: str
    pageContextSummary: Dict[str, Any]
    allowedTools: List[str]
    sessionId: Optional[str] = None


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ConfirmPreview(BaseModel):
    actionType: str
    previewText: str
    riskLevel: RiskLevel
    confirmToken: str
    pondId: Optional[str] = None
    feederId: str
    amount: float
    duration: int
    expiresAt: str
    mode: EnvironmentMode


class InvokeResponse(BaseModel):
    status: str = "completed"
    assistantMessage: str
    toolCalls: List[ToolCall] = Field(default_factory=list)
    toolResults: Optional[List[Dict[str, Any]]] = None
    confirmPreview: Optional[ConfirmPreview] = None
    warnings: List[str] = Field(default_factory=list)
    messageId: Optional[str] = None


class SuggestionCard(BaseModel):
    id: str
    title: str
    summary: str
    rationale: List[str]
    confidence: float
    severity: Severity
    sourceMode: EnvironmentMode
    updatedAt: str
    suggestedAction: str
    confirmRequired: bool
    suggestionId: Optional[str] = None
    suggestedAmount: Optional[float] = None  # 建议投喂量（克）


class SuggestionPanelState(BaseModel):
    hasNewRisk: bool
    hasNewSuggestion: bool


class SuggestionResponse(BaseModel):
    cards: List[SuggestionCard]
    panelState: SuggestionPanelState


class ManualFeedingPreviewRequest(BaseModel):
    pondId: Optional[str] = None
    amount: float
    sessionId: Optional[str] = None


class ManualFeedingPreviewResponse(BaseModel):
    actionType: str
    previewText: str
    riskLevel: RiskLevel
    confirmToken: str
    pondId: Optional[str] = None
    feederId: str
    amount: float
    duration: int
    expiresAt: str
    mode: EnvironmentMode
    sessionId: Optional[str] = None


class ManualFeedingExecuteRequest(BaseModel):
    confirmToken: str
    feederId: str
    amount: float
    duration: int = 10
    pondId: Optional[str] = None


class ToolExecuteRequest(BaseModel):
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolExecuteResponse(BaseModel):
    result: str


class AgentInvokeResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]
