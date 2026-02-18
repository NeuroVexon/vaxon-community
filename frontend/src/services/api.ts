/**
 * Axon by NeuroVexon - API Service
 */

const API_BASE = '/api/v1'

function getLangHeaders(): Record<string, string> {
  const lang = localStorage.getItem('axon-language') || 'de'
  return { 'Accept-Language': lang }
}

interface ChatResponse {
  session_id: string
  message: string
  tool_calls?: Array<{
    id: string
    name: string
    parameters: Record<string, unknown>
  }>
}

interface Conversation {
  id: string
  title: string | null
  created_at: string
  updated_at: string
}

interface AuditEntry {
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

interface Settings {
  app_name: string
  app_version: string
  llm_provider: string
  theme: string
  system_prompt?: string
  available_providers: string[]
  // API Keys
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
  // Models
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

export const api = {
  // Chat
  async sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE}/chat/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getLangHeaders() },
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  },

  async streamMessage(
    message: string,
    onChunk: (chunk: { type: string; content?: string }) => void,
    sessionId?: string
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getLangHeaders() },
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

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

  /**
   * Stream a message through the Agent Orchestrator.
   * Handles tool approval via SSE events.
   */
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
    const response = await fetch(`${API_BASE}/chat/agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getLangHeaders() },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        system_prompt: systemPrompt,
        agent_id: agentId,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

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

  /**
   * Approve or reject a pending tool request from the agent stream.
   */
  async approveAgentTool(
    approvalId: string,
    decision: 'once' | 'session' | 'never'
  ): Promise<void> {
    const response = await fetch(
      `${API_BASE}/chat/approve/${approvalId}?decision=${decision}`,
      { method: 'POST' }
    )
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
  },

  // Tool Approval
  async approveTool(
    sessionId: string,
    tool: string,
    params: Record<string, unknown>,
    decision: 'once' | 'session' | 'never'
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/tools/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        tool,
        params,
        decision,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
  },

  // Conversations
  async getConversations(limit = 50): Promise<Conversation[]> {
    const response = await fetch(`${API_BASE}/chat/conversations?limit=${limit}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  },

  async getConversation(id: string): Promise<Conversation & { messages: unknown[] }> {
    const response = await fetch(`${API_BASE}/chat/conversations/${id}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  },

  async deleteConversation(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/chat/conversations/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
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

    const response = await fetch(`${API_BASE}/audit?${params}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  },

  async getAuditStats(sessionId?: string): Promise<{
    total: number
    by_event_type: Record<string, number>
    by_tool: Record<string, number>
    avg_execution_time_ms: number | null
  }> {
    const params = sessionId ? `?session_id=${sessionId}` : ''
    const response = await fetch(`${API_BASE}/audit/stats${params}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  },

  // Settings
  async getSettings(): Promise<Settings> {
    const response = await fetch(`${API_BASE}/settings`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  },

  async updateSettings(settings: Partial<Settings>): Promise<void> {
    const response = await fetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
  },

  async deleteApiKey(keyName: string): Promise<{ status: string; key: string }> {
    const response = await fetch(`${API_BASE}/settings/api-key/${keyName}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async testEmailConnection(): Promise<{
    imap: boolean
    smtp: boolean
    imap_error: string | null
    smtp_error: string | null
  }> {
    const response = await fetch(`${API_BASE}/settings/email/test`, { method: 'POST', headers: { ...getLangHeaders() } })
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
    const response = await fetch(`${API_BASE}/skills`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async approveSkill(id: string, approved: boolean): Promise<void> {
    const response = await fetch(`${API_BASE}/skills/${id}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved }),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async toggleSkill(id: string, enabled: boolean): Promise<void> {
    const response = await fetch(`${API_BASE}/skills/${id}/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled }),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async deleteSkill(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/skills/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async scanSkills(): Promise<{ found: number }> {
    const response = await fetch(`${API_BASE}/skills/scan`, { method: 'POST' })
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
    const response = await fetch(`${API_BASE}/memory?${params}`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async createMemory(data: {
    key: string
    content: string
    source?: string
    category?: string
  }): Promise<{ id: string; key: string; content: string }> {
    const response = await fetch(`${API_BASE}/memory`, {
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
    const response = await fetch(`${API_BASE}/memory/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async deleteMemory(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/memory/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async clearMemories(): Promise<void> {
    const response = await fetch(`${API_BASE}/memory`, { method: 'DELETE' })
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
    const response = await fetch(`${API_BASE}/tasks`)
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
    const response = await fetch(`${API_BASE}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async updateTask(id: string, data: Record<string, unknown>): Promise<void> {
    const response = await fetch(`${API_BASE}/tasks/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async deleteTask(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/tasks/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async runTask(id: string): Promise<{ result: string }> {
    const response = await fetch(`${API_BASE}/tasks/${id}/run`, { method: 'POST' })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async toggleTask(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/tasks/${id}/toggle`, { method: 'POST' })
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
    const response = await fetch(`${API_BASE}/agents`)
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
    const response = await fetch(`${API_BASE}/agents/${id}`)
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
    const response = await fetch(`${API_BASE}/agents`, {
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
    const response = await fetch(`${API_BASE}/agents/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async deleteAgent(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/agents/${id}`, { method: 'DELETE' })
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
    const response = await fetch(`${API_BASE}/workflows`)
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
    const response = await fetch(`${API_BASE}/workflows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async updateWorkflow(id: string, data: Record<string, unknown>): Promise<void> {
    const response = await fetch(`${API_BASE}/workflows/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  async deleteWorkflow(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/workflows/${id}`, { method: 'DELETE' })
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
    const response = await fetch(`${API_BASE}/workflows/${id}/run`, { method: 'POST' })
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
    const response = await fetch(`${API_BASE}/workflows/${id}/history`)
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
    const response = await fetch(`${API_BASE}/analytics/overview`)
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
    const response = await fetch(`${API_BASE}/analytics/tools`)
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
    const response = await fetch(`${API_BASE}/analytics/timeline${params}`)
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
    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      headers: { ...getLangHeaders() },
      body: formData,
    })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    return response.json()
  },

  async deleteDocument(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/upload/${id}`, { method: 'DELETE', headers: { ...getLangHeaders() } })
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  },

  // Health
  async healthCheck(): Promise<{
    status: string
    providers: Record<string, boolean>
  }> {
    const response = await fetch(`${API_BASE}/settings/health`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return response.json()
  },
}
