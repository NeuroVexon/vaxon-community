/**
 * Axon by NeuroVexon - API Service
 */

const API_BASE = '/api/v1'

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
  available_providers: string[]
}

export const api = {
  // Chat
  async sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE}/chat/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
    sessionId?: string,
    onChunk: (chunk: { type: string; content?: string }) => void
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
