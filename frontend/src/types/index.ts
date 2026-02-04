/**
 * Axon by NeuroVexon - TypeScript Type Definitions
 */

// Chat Types
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  timestamp: Date
  toolInfo?: ToolInfo
}

export interface ToolInfo {
  name: string
  status: 'pending' | 'approved' | 'rejected' | 'executed' | 'failed'
  result?: string
  error?: string
  executionTimeMs?: number
}

export interface Conversation {
  id: string
  title: string | null
  systemPrompt: string | null
  createdAt: string
  updatedAt: string
  messages?: Message[]
}

// Tool Types
export interface ToolCall {
  id: string
  name: string
  parameters: Record<string, unknown>
}

export interface ToolApprovalRequest {
  tool: string
  params: Record<string, unknown>
  description: string
  riskLevel: RiskLevel
}

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

export type ApprovalDecision = 'once' | 'session' | 'never'

// Audit Types
export interface AuditEntry {
  id: string
  sessionId: string
  timestamp: string
  eventType: AuditEventType
  toolName: string | null
  toolParams: Record<string, unknown> | null
  result: string | null
  error: string | null
  userDecision: string | null
  executionTimeMs: number | null
}

export type AuditEventType =
  | 'tool_requested'
  | 'tool_approved'
  | 'tool_rejected'
  | 'tool_executed'
  | 'tool_failed'

export interface AuditStats {
  total: number
  byEventType: Record<string, number>
  byTool: Record<string, number>
  avgExecutionTimeMs: number | null
}

// Settings Types
export interface Settings {
  appName: string
  appVersion: string
  llmProvider: LLMProvider
  theme: Theme
  systemPrompt: string
  availableProviders: LLMProvider[]
}

export type LLMProvider = 'ollama' | 'claude' | 'openai'

export type Theme = 'dark' | 'light'

// API Response Types
export interface ChatResponse {
  sessionId: string
  message: string
  toolCalls?: ToolCall[]
}

export interface StreamChunk {
  type: 'text' | 'tool_request' | 'tool_result' | 'done' | 'error'
  content?: string
  tool?: string
  params?: Record<string, unknown>
  result?: unknown
  sessionId?: string
  error?: string
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  appName: string
  version: string
  providers: Record<LLMProvider, boolean>
}

// UI State Types
export interface ChatState {
  messages: Message[]
  isLoading: boolean
  currentSessionId: string | null
  pendingApproval: ToolApprovalRequest | null
}

export interface AppState {
  currentView: View
  settings: Settings | null
  isInitialized: boolean
}

export type View = 'chat' | 'audit' | 'settings'
