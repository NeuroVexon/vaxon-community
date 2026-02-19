/**
 * Axon by NeuroVexon - API Service
 */

import type { AuthTokens, AuthUser, AuthStatus, Settings, AuditEntry, Conversation, ChatResponse } from '../types'

const API_BASE = '/api/v1'

// --- Token Storage ---

const TOKEN_KEY = 'axon-tokens'

function getStoredTokens(): AuthTokens | null {
  try {
    const raw = localStorage.getItem(TOKEN_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function storeTokens(tokens: AuthTokens): void {
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens))
}

function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function getAccessToken(): string | null {
  return getStoredTokens()?.access_token ?? null
}

// --- Helpers ---

function getLangHeaders(): Record<string, string> {
  const lang = localStorage.getItem('axon-language') || 'de'
  return { 'Accept-Language': lang }
}

function getAuthHeaders(): Record<string, string> {
  const token = getAccessToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// --- Auth Fetch with 401 Refresh ---

let refreshPromise: Promise<boolean> | null = null

async function tryRefresh(): Promise<boolean> {
  const tokens = getStoredTokens()
  if (!tokens?.refresh_token) return false

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: tokens.refresh_token }),
    })
    if (!res.ok) {
      clearTokens()
      return false
    }
    const newTokens: AuthTokens = await res.json()
    storeTokens(newTokens)
    return true
  } catch {
    clearTokens()
    return false
  }
}

async function authFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers)

  // Add auth + lang headers if not already set
  const authH = getAuthHeaders()
  for (const [k, v] of Object.entries(authH)) {
    if (!headers.has(k)) headers.set(k, v)
  }
  const langH = getLangHeaders()
  for (const [k, v] of Object.entries(langH)) {
    if (!headers.has(k)) headers.set(k, v)
  }

  let response = await fetch(input, { ...init, headers })

  if (response.status === 401) {
    // Deduplicate concurrent refresh attempts
    if (!refreshPromise) {
      refreshPromise = tryRefresh().finally(() => { refreshPromise = null })
    }
    const refreshed = await refreshPromise
    if (refreshed) {
      // Retry with new token
      const retryHeaders = new Headers(init?.headers)
      const newAuth = getAuthHeaders()
      for (const [k, v] of Object.entries(newAuth)) retryHeaders.set(k, v)
      for (const [k, v] of Object.entries(langH)) {
        if (!retryHeaders.has(k)) retryHeaders.set(k, v)
      }
      response = await fetch(input, { ...init, headers: retryHeaders })
    }
  }

  return response
}

export const api = {
  // ==================
  // Auth
  // ==================

  async getAuthStatus(): Promise<AuthStatus> {
    const response = await fetch(`${API_BASE}/auth/status`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async login(email: string, password: string): Promise<AuthTokens> {
    const formData = new URLSearchParams()
    formData.set('username', email)
    formData.set('password', password)

    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(err.detail || `HTTP error! status: ${response.status}`)
    }
    const tokens: AuthTokens = await response.json()
    storeTokens(tokens)
    return tokens
  },

  async register(email: string, password: string, displayName?: string): Promise<AuthTokens> {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name: displayName }),
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Registration failed' }))
      throw new Error(err.detail || `HTTP error! status: ${response.status}`)
    }
    const tokens: AuthTokens = await response.json()
    storeTokens(tokens)
    return tokens
  },

  async getMe(): Promise<AuthUser> {
    const response = await authFetch(`${API_BASE}/auth/me`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  logout(): void {
    clearTokens()
  },

  // ==================
  // Chat
  // ==================

  async sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
    const response = await authFetch(`${API_BASE}/chat/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async streamMessage(
    message: string,
    onChunk: (chunk: { type: string; content?: string }) => void,
    sessionId?: string
  ): Promise<void> {
    const response = await authFetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

    const reader = response.body?.getReader()
    if (!reader) return

    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            onChunk(data)
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  },

  async streamAgentMessage(
    message: string,
    onEvent: (event: {
      type: string
      content?: string
      tool?: string
      params?: Record<string, unknown>
      description?: string
      risk_level?: string
      approval_id?: string
      result?: unknown
      execution_time_ms?: number
      session_id?: string
      message?: string
      error?: string
    }) => void,
    sessionId?: string,
    systemPrompt?: string,
    agentId?: string
  ): Promise<void> {
    const response = await authFetch(`${API_BASE}/chat/agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        system_prompt: systemPrompt,
        agent_id: agentId,
      }),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

    const reader = response.body?.getReader()
    if (!reader) return

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            onEvent(data)
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  },

  async approveAgentTool(
    approvalId: string,
    decision: 'once' | 'session' | 'never'
  ): Promise<void> {
    const response = await authFetch(
      `${API_BASE}/chat/approve/${approvalId}?decision=${decision}`,
      { method: 'POST' }
    )
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  // Tool Approval
  async approveTool(
    sessionId: string,
    tool: string,
    params: Record<string, unknown>,
    decision: 'once' | 'session' | 'never'
  ): Promise<void> {
    const response = await authFetch(`${API_BASE}/tools/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, tool, params, decision }),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  // Conversations
  async getConversations(limit = 50): Promise<Conversation[]> {
    const response = await authFetch(`${API_BASE}/chat/conversations?limit=${limit}`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async getConversation(id: string): Promise<Conversation & { messages: unknown[] }> {
    const response = await authFetch(`${API_BASE}/chat/conversations/${id}`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async deleteConversation(id: string): Promise<void> {
    const response = await authFetch(`${API_BASE}/chat/conversations/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  // Audit
  async getAuditLogs(options?: {
    sessionId?: string
    eventType?: string
    limit?: number
  }): Promise<AuditEntry[]> {
    const params = new URLSearchParams()
    if (options?.sessionId) params.set('session_id', options.sessionId)
    if (options?.eventType) params.set('event_type', options.eventType)
    if (options?.limit) params.set('limit', options.limit.toString())

    const response = await authFetch(`${API_BASE}/audit?${params}`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async getAuditStats(sessionId?: string): Promise<{
    total: number
    by_event_type: Record<string, number>
    by_tool: Record<string, number>
    avg_execution_time_ms: number | null
  }> {
    const params = sessionId ? `?session_id=${sessionId}` : ''
    const response = await authFetch(`${API_BASE}/audit/stats${params}`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  // Settings
  async getSettings(): Promise<Settings> {
    const response = await authFetch(`${API_BASE}/settings`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async updateSettings(settings: Partial<Settings>): Promise<void> {
    const response = await authFetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async deleteApiKey(keyName: string): Promise<{ status: string; key: string }> {
    const response = await authFetch(`${API_BASE}/settings/api-key/${keyName}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async testEmailConnection(): Promise<{
    imap: boolean
    smtp: boolean
    imap_error: string | null
    smtp_error: string | null
  }> {
    const response = await authFetch(`${API_BASE}/settings/email/test`, { method: 'POST' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  // Skills
  async getSkills(): Promise<Array<{
    id: string
    name: string
    display_name: string
    description: string
    version: string
    author: string | null
    enabled: boolean
    approved: boolean
    risk_level: string
    created_at: string
    updated_at: string
  }>> {
    const response = await authFetch(`${API_BASE}/skills`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async approveSkill(id: string, approved: boolean): Promise<void> {
    const response = await authFetch(`${API_BASE}/skills/${id}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved }),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async toggleSkill(id: string, enabled: boolean): Promise<void> {
    const response = await authFetch(`${API_BASE}/skills/${id}/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled }),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async deleteSkill(id: string): Promise<void> {
    const response = await authFetch(`${API_BASE}/skills/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async scanSkills(): Promise<{ found: number }> {
    const response = await authFetch(`${API_BASE}/skills/scan`, { method: 'POST' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  // Memory
  async getMemories(options?: {
    category?: string
    search?: string
    limit?: number
  }): Promise<Array<{
    id: string
    key: string
    content: string
    source: string
    category: string | null
    created_at: string
    updated_at: string
  }>> {
    const params = new URLSearchParams()
    if (options?.category) params.set('category', options.category)
    if (options?.search) params.set('search', options.search)
    if (options?.limit) params.set('limit', options.limit.toString())
    const response = await authFetch(`${API_BASE}/memory?${params}`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async createMemory(data: {
    key: string
    content: string
    source?: string
    category?: string
  }): Promise<{ id: string; key: string; content: string }> {
    const response = await authFetch(`${API_BASE}/memory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async updateMemory(id: string, data: {
    content?: string
    category?: string
  }): Promise<void> {
    const response = await authFetch(`${API_BASE}/memory/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async deleteMemory(id: string): Promise<void> {
    const response = await authFetch(`${API_BASE}/memory/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async clearMemories(): Promise<void> {
    const response = await authFetch(`${API_BASE}/memory`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  // Scheduled Tasks
  async getTasks(): Promise<Array<{
    id: string
    name: string
    cron_expression: string
    agent_id: string | null
    prompt: string
    approval_required: boolean
    notification_channel: string
    max_retries: number
    last_run: string | null
    last_result: string | null
    next_run: string | null
    enabled: boolean
    created_at: string
    updated_at: string
  }>> {
    const response = await authFetch(`${API_BASE}/tasks`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async createTask(data: {
    name: string
    cron_expression: string
    prompt: string
    agent_id?: string
    approval_required?: boolean
    notification_channel?: string
  }): Promise<{ id: string }> {
    const response = await authFetch(`${API_BASE}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async updateTask(id: string, data: Record<string, unknown>): Promise<void> {
    const response = await authFetch(`${API_BASE}/tasks/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async deleteTask(id: string): Promise<void> {
    const response = await authFetch(`${API_BASE}/tasks/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async runTask(id: string): Promise<{ result: string }> {
    const response = await authFetch(`${API_BASE}/tasks/${id}/run`, { method: 'POST' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async toggleTask(id: string): Promise<void> {
    const response = await authFetch(`${API_BASE}/tasks/${id}/toggle`, { method: 'POST' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  // Agents
  async getAgents(): Promise<Array<{
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
  }>> {
    const response = await authFetch(`${API_BASE}/agents`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async getAgent(id: string): Promise<{
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
  }> {
    const response = await authFetch(`${API_BASE}/agents/${id}`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async createAgent(data: {
    name: string
    description?: string
    system_prompt?: string
    model?: string
    allowed_tools?: string[]
    allowed_skills?: string[]
    risk_level_max?: string
    auto_approve_tools?: string[]
  }): Promise<{ id: string }> {
    const response = await authFetch(`${API_BASE}/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async updateAgent(id: string, data: {
    name?: string
    description?: string
    system_prompt?: string
    model?: string
    allowed_tools?: string[] | null
    allowed_skills?: string[] | null
    risk_level_max?: string
    auto_approve_tools?: string[] | null
    enabled?: boolean
  }): Promise<void> {
    const response = await authFetch(`${API_BASE}/agents/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async deleteAgent(id: string): Promise<void> {
    const response = await authFetch(`${API_BASE}/agents/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  // Workflows
  async getWorkflows(): Promise<Array<{
    id: string
    name: string
    description: string | null
    trigger_phrase: string | null
    agent_id: string | null
    steps: Array<{ order: number; prompt: string; store_as: string }>
    approval_mode: string
    enabled: boolean
    created_at: string
    updated_at: string
  }>> {
    const response = await authFetch(`${API_BASE}/workflows`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async createWorkflow(data: {
    name: string
    description?: string
    trigger_phrase?: string
    agent_id?: string
    steps: Array<{ order: number; prompt: string; store_as: string }>
    approval_mode?: string
  }): Promise<{ id: string }> {
    const response = await authFetch(`${API_BASE}/workflows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async updateWorkflow(id: string, data: Record<string, unknown>): Promise<void> {
    const response = await authFetch(`${API_BASE}/workflows/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async deleteWorkflow(id: string): Promise<void> {
    const response = await authFetch(`${API_BASE}/workflows/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async runWorkflow(id: string): Promise<{
    id: string
    status: string
    context: Record<string, string> | null
    error: string | null
    started_at: string
    completed_at: string | null
  }> {
    const response = await authFetch(`${API_BASE}/workflows/${id}/run`, { method: 'POST' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async getWorkflowHistory(id: string): Promise<Array<{
    id: string
    workflow_id: string
    status: string
    current_step: number
    context: Record<string, string> | null
    error: string | null
    started_at: string
    completed_at: string | null
  }>> {
    const response = await authFetch(`${API_BASE}/workflows/${id}/history`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  // Analytics / Dashboard
  async getAnalyticsOverview(): Promise<{
    conversations: number
    messages: number
    agents: number
    tool_calls: number
    approval_rate: number
    active_tasks: number
    workflows: number
    active_skills: number
  }> {
    const response = await authFetch(`${API_BASE}/analytics/overview`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async getAnalyticsTools(): Promise<{
    tools: Array<{
      tool: string
      count: number
      avg_time_ms: number
      failures: number
      error_rate: number
    }>
  }> {
    const response = await authFetch(`${API_BASE}/analytics/tools`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async getAnalyticsTimeline(days?: number): Promise<{
    timeline: Array<{
      date: string
      conversations: number
      tool_calls: number
    }>
  }> {
    const params = days ? `?days=${days}` : ''
    const response = await authFetch(`${API_BASE}/analytics/timeline${params}`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  // Document Upload
  async uploadDocument(file: File, conversationId?: string): Promise<{
    id: string
    filename: string
    mime_type: string
    file_size: number
    has_text: boolean
    text_preview: string
  }> {
    const formData = new FormData()
    formData.append('file', file)
    if (conversationId) {
      formData.append('conversation_id', conversationId)
    }
    const response = await authFetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async deleteDocument(id: string): Promise<void> {
    const response = await authFetch(`${API_BASE}/upload/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  // Health
  async healthCheck(): Promise<{
    status: string
    providers: Record<string, boolean>
  }> {
    const response = await authFetch(`${API_BASE}/settings/health`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },
}
