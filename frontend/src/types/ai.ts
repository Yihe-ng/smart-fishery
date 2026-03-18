export type AIPageId =
  | 'global-chat'
  | 'fishery-dashboard'
  | 'feeding'
  | 'water-quality'
  | 'growth'

export type AIEnvironmentMode = 'mock' | 'real'
export type AISeverity = 'info' | 'warning' | 'critical'
export type AIRole = 'user' | 'assistant'
export type AITabKey = 'chat' | 'automation'

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
  riskLevel: AISeverity
  confirmToken: string
  expiresAt: string
  mode: AIEnvironmentMode
  sessionId?: string
}

export interface AIInvokeResponse {
  assistantMessage: string
  toolCalls?: Array<{ name: string; arguments: Record<string, unknown> }>
  toolResults?: Array<Record<string, unknown>> | null
  confirmPreview?: AIConfirmPreview | null
  warnings?: string[]
  messageId?: string | null
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
  warnings?: string[]
  confirmPreview?: AIConfirmPreview | null
}

export interface AIAutomationPreset {
  key: string
  title: string
  prompt: string
}
