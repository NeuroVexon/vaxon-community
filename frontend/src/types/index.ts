/**
 * Axon by NeuroVexon - TypeScript Type Definitions
 * Single source of truth for all shared types.
 * Field names use snake_case to match the backend API.
 */

// ============================================================
// View / Navigation
// ============================================================

export type View =
  | 'dashboard'
  | 'chat'
  | 'audit'
  | 'memory'
  | 'skills'
  | 'agents'
  | 'scheduler'
  | 'workflows'
  | 'settings'

// ============================================================
// LLM Providers
// ============================================================

export type LLMProvider = 'ollama' | 'claude' | 'openai' | 'gemini' | 'groq' | 'openrouter'

export type Theme = 'dark' | 'light'

// ============================================================
// Chat Types
// ============================================================

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
  created_at: string
  updated_at: string
}

export interface ChatResponse {
  session_id: string
  message: string
  tool_calls?: Array<{
    id: string
    name: string
    parameters: Record<string, unknown>
  }>
}

// ============================================================
// Tool Types
// ============================================================

export interface ToolCall {
  id: string
  name: string
  parameters: Record<string, unknown>
}

export interface ToolApprovalRequest {
  tool: string
  params: Record<string, unknown>
  description: string
  risk_level: RiskLevel
}

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

export type ApprovalDecision = 'once' | 'session' | 'never'

// ============================================================
// Audit Types
// ============================================================

export interface AuditEntry {
  id: string
  session_id: string
  timestamp: string
  event_type: string
  tool_name: string | null
  tool_params: Record<string, unknown> | null
  result: string | null
  error: string | null
  user_decision: string | null
  execution_time_ms: number | null
}

export type AuditEventType =
  | 'tool_requested'
  | 'tool_approved'
  | 'tool_rejected'
  | 'tool_executed'
  | 'tool_failed'

export interface AuditStats {
  total: number
  by_event_type: Record<string, number>
  by_tool: Record<string, number>
  avg_execution_time_ms: number | null
}

// ============================================================
// Settings Types
// ============================================================

export interface Settings {
  app_name: string
  app_version: string
  llm_provider: string
  theme: string
  system_prompt?: string
  available_providers: string[]
  // API key status
  anthropic_api_key_set?: boolean
  anthropic_api_key_masked?: string
  openai_api_key_set?: boolean
  openai_api_key_masked?: string
  gemini_api_key_set?: boolean
  gemini_api_key_masked?: string
  groq_api_key_set?: boolean
  groq_api_key_masked?: string
  openrouter_api_key_set?: boolean
  openrouter_api_key_masked?: string
  // Model selections
  ollama_model?: string
  claude_model?: string
  openai_model?: string
  gemini_model?: string
  groq_model?: string
  openrouter_model?: string
  // E-Mail
  email_enabled?: boolean
  imap_host?: string
  imap_port?: string
  imap_user?: string
  imap_password_set?: boolean
  smtp_host?: string
  smtp_port?: string
  smtp_user?: string
  smtp_password_set?: boolean
  smtp_from?: string
  // Telegram / Discord
  telegram_enabled?: boolean
  telegram_bot_token_set?: boolean
  discord_enabled?: boolean
  discord_bot_token_set?: boolean
  // Language
  language?: string
}

// ============================================================
// API Response Types
// ============================================================

export interface StreamChunk {
  type: 'text' | 'tool_request' | 'tool_result' | 'done' | 'error'
  content?: string
  tool?: string
  params?: Record<string, unknown>
  result?: unknown
  session_id?: string
  error?: string
}

export interface HealthStatus {
  status: string
  providers: Record<string, boolean>
}

// ============================================================
// Auth Types
// ============================================================

export interface AuthUser {
  id: string
  email: string
  display_name: string | null
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string | null
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  user: AuthUser
}

export interface AuthStatus {
  has_users: boolean
  registration_enabled: boolean
}

// ============================================================
// Agent Types
// ============================================================

export interface AgentProfile {
  id: string
  name: string
  description: string
  system_prompt: string | null
  model: string | null
  allowed_tools: string[] | null
  allowed_skills: string[] | null
  risk_level_max: string
  auto_approve_tools: string[] | null
  is_default: boolean
  enabled: boolean
  created_at: string
  updated_at: string
}

// ============================================================
// UI State Types
// ============================================================

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
