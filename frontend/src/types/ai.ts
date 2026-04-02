export type AIPageId = 'global-chat' | 'fishery-dashboard' | 'feeding' | 'water-quality' | 'growth'

export type AIEnvironmentMode = 'mock' | 'real'
export type AISeverity = 'info' | 'warning' | 'critical'
export type AIRiskLevel = 'low' | 'warning' | 'critical'
export type AIRole = 'user' | 'assistant'
export type AITabKey = 'chat' | 'automation'
export type AIIntentType = 'qa' | 'automation'
export type AIUIState = 'idle' | 'chatting' | 'previewing' | 'confirming' | 'executing' | 'failed'

export interface AIContextRequest {
  pageId: AIPageId
  routePath: string
  pondId?: string
  selection?: Record<string, unknown>
}

export interface AIContextSummary {
  contextVersion: string
  sourceMode: AIEnvironmentMode
  currentPage: {
    pageId: AIPageId
    routePath: string
    selection: Record<string, unknown>
  }
  pond: {
    pondId: string
    name: string
    sourceMode: AIEnvironmentMode
  }
  keyMetrics: Array<{
    key: string
    label: string
    value: number
    unit: string
    status: 'normal' | 'warning' | 'critical'
  }>
  alertDigest: {
    total: number
    critical: number
    warning: number
    latestTitles: string[]
  }
  deviceStatus: {
    onlineCount: number
    offlineCount: number
    feederStatus: string
    cameraStatus: string
  }
  updatedAt: string
}

export interface AIBootstrapPayload {
  environmentMode: AIEnvironmentMode
  systemInstructions: string
  pageInstructions: string
  pageContextSummary: AIContextSummary
  allowedTools: string[]
  toolSchemas: Array<Record<string, unknown>>
  uiCapabilities: {
    canExecute: boolean
    canPreview: boolean
    showAutomationTab: boolean
    showSuggestionPanel: boolean
  }
  sessionPolicy: {
    persistent: false
    resumable: false
    persistenceReserved: true
  }
}

export interface AIConfirmPreview {
  actionType: string
  previewText: string
  riskLevel: AIRiskLevel
  confirmToken: string
  expiresAt: string
  mode: AIEnvironmentMode
  sessionId?: string
}

export interface AIAgentInvokeResponse {
  id: string
  object: string
  created: number
  model: string
  choices: Array<Record<string, unknown>>
  usage: Record<string, number>
}

export interface AIToolExecuteRequest {
  arguments: Record<string, unknown>
}

export interface AIToolExecuteResponse {
  result: string
}

export interface AISuggestionCard {
  id: string
  title: string
  summary: string
  rationale: string[]
  confidence: number
  severity: AISeverity
  sourceMode: AIEnvironmentMode
  updatedAt: string
  suggestedAction: string
  confirmRequired: boolean
  suggestionId?: string | null
  /** 建议投喂量（克） */
  suggestedAmount?: number
}

export interface AISuggestionResponse {
  cards: AISuggestionCard[]
  panelState: {
    hasNewRisk: boolean
    hasNewSuggestion: boolean
  }
}

export interface AIChatMessage {
  id: string
  role: AIRole
  content: string
  createdAt: string
  intent?: AIIntentType
  warnings?: string[]
  confirmPreview?: AIConfirmPreview | null
}

export interface AIAutomationPreset {
  key: string
  title: string
  prompt: string
}
