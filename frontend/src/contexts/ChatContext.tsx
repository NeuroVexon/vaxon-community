import { createContext, useState, useCallback, type ReactNode } from 'react'
import type { Message, ToolApprovalRequest } from '../types'
import { api } from '../services/api'
import { useTranslation } from 'react-i18next'

export interface ChatContextValue {
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
  pendingApproval: (ToolApprovalRequest & { approval_id?: string }) | null
  currentSessionId: string | null
  sendMessage: (content: string) => Promise<void>
  approveToolCall: (scope: 'once' | 'session') => Promise<void>
  rejectToolCall: () => Promise<void>
  loadConversation: (conversationId: string) => Promise<void>
  clearChat: () => void
}

export const ChatContext = createContext<ChatContextValue | null>(null)

interface ChatProviderProps {
  children: ReactNode
  onSessionChange: (id: string) => void
  agentId: string | null
}

export function ChatProvider({ children, onSessionChange, agentId }: ChatProviderProps) {
  const { t } = useTranslation()
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [pendingApproval, setPendingApproval] = useState<
    (ToolApprovalRequest & { approval_id?: string }) | null
  >(null)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)

  const sendMessage = useCallback(async (content: string) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setIsStreaming(true)

    const assistantId = `assistant-${Date.now()}`
    setMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }])

    try {
      await api.streamAgentMessage(
        content,
        (event) => {
          switch (event.type) {
            case 'text':
              setMessages(prev => prev.map(msg =>
                msg.id === assistantId
                  ? { ...msg, content: msg.content + (event.content || '') }
                  : msg
              ))
              break

            case 'tool_request':
              setMessages(prev => [...prev, {
                id: `tool-${Date.now()}-${event.tool}`,
                role: 'tool' as const,
                content: '',
                timestamp: new Date(),
                toolInfo: {
                  name: event.tool || '',
                  status: 'pending' as const,
                },
              }])
              setPendingApproval({
                tool: event.tool || '',
                params: event.params || {},
                description: event.description || t('useChat.toolDefault', { tool: event.tool }),
                risk_level: (event.risk_level as 'low' | 'medium' | 'high' | 'critical') || 'medium',
                approval_id: event.approval_id,
              })
              break

            case 'tool_result':
              setMessages(prev => prev.map(msg => {
                if (msg.role === 'tool' && msg.toolInfo?.name === event.tool && msg.toolInfo?.status === 'pending') {
                  return {
                    ...msg,
                    content: typeof event.result === 'string' ? event.result : JSON.stringify(event.result),
                    toolInfo: {
                      ...msg.toolInfo,
                      status: 'executed' as const,
                      result: typeof event.result === 'string' ? event.result : JSON.stringify(event.result),
                      executionTimeMs: event.execution_time_ms,
                    },
                  }
                }
                return msg
              }))
              break

            case 'tool_rejected':
              setMessages(prev => prev.map(msg => {
                if (msg.role === 'tool' && msg.toolInfo?.name === event.tool && msg.toolInfo?.status === 'pending') {
                  return {
                    ...msg,
                    toolInfo: { ...msg.toolInfo, status: 'rejected' as const },
                  }
                }
                return msg
              }))
              break

            case 'tool_blocked':
              setMessages(prev => prev.map(msg => {
                if (msg.role === 'tool' && msg.toolInfo?.name === event.tool && msg.toolInfo?.status === 'pending') {
                  return {
                    ...msg,
                    toolInfo: { ...msg.toolInfo, status: 'rejected' as const },
                  }
                }
                return msg
              }))
              break

            case 'tool_error':
              setMessages(prev => prev.map(msg => {
                if (msg.role === 'tool' && msg.toolInfo?.name === event.tool) {
                  return {
                    ...msg,
                    toolInfo: {
                      ...msg.toolInfo,
                      name: msg.toolInfo?.name || event.tool || '',
                      status: 'failed' as const,
                      error: event.error,
                    },
                  }
                }
                return msg
              }))
              break

            case 'error':
              setMessages(prev => prev.map(msg =>
                msg.id === assistantId
                  ? { ...msg, content: msg.content || t('useChat.errorDefault', { message: event.message || t('useChat.errorUnknown') }) }
                  : msg
              ))
              break

            case 'done':
              if (event.session_id) {
                setCurrentSessionId(event.session_id)
                onSessionChange(event.session_id)
              }
              break
          }
        },
        currentSessionId || undefined,
        undefined,
        agentId || undefined
      )
    } catch (error) {
      console.error('Failed to send message:', error)
      setMessages(prev => prev.map(msg =>
        msg.id === assistantId
          ? { ...msg, content: t('useChat.sendError') }
          : msg
      ))
    }

    setMessages(prev => prev.filter(msg => msg.id !== assistantId || msg.content.length > 0))

    setIsLoading(false)
    setIsStreaming(false)
  }, [currentSessionId, onSessionChange, agentId, t])

  const approveToolCall = useCallback(async (scope: 'once' | 'session') => {
    if (!pendingApproval?.approval_id) return

    try {
      await api.approveAgentTool(pendingApproval.approval_id, scope)

      setMessages(prev => prev.map(msg => {
        if (msg.role === 'tool' && msg.toolInfo?.name === pendingApproval.tool && msg.toolInfo?.status === 'pending') {
          return {
            ...msg,
            toolInfo: { ...msg.toolInfo, status: 'approved' as const },
          }
        }
        return msg
      }))
    } catch (error) {
      console.error('Failed to approve tool:', error)
    }

    setPendingApproval(null)
  }, [pendingApproval])

  const rejectToolCall = useCallback(async () => {
    if (!pendingApproval?.approval_id) {
      setPendingApproval(null)
      return
    }

    try {
      await api.approveAgentTool(pendingApproval.approval_id, 'never')
    } catch (error) {
      console.error('Failed to reject tool:', error)
    }

    setMessages(prev => prev.map(msg => {
      if (msg.role === 'tool' && msg.toolInfo?.name === pendingApproval.tool && msg.toolInfo?.status === 'pending') {
        return {
          ...msg,
          toolInfo: { ...msg.toolInfo, status: 'rejected' as const },
        }
      }
      return msg
    }))

    setPendingApproval(null)
  }, [pendingApproval])

  const loadConversation = useCallback(async (conversationId: string) => {
    setIsLoading(true)
    try {
      const data = await api.getConversation(conversationId)
      setCurrentSessionId(conversationId)

      const loadedMessages: Message[] = (data.messages as Array<{
        id: string
        role: string
        content: string
        created_at: string
      }>).map(m => ({
        id: m.id,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        timestamp: new Date(m.created_at),
      }))

      setMessages(loadedMessages)
    } catch (error) {
      console.error('Failed to load conversation:', error)
    }
    setIsLoading(false)
  }, [])

  const clearChat = useCallback(() => {
    setMessages([])
    setCurrentSessionId(null)
    setPendingApproval(null)
  }, [])

  return (
    <ChatContext.Provider value={{
      messages,
      isLoading,
      isStreaming,
      pendingApproval,
      currentSessionId,
      sendMessage,
      approveToolCall,
      rejectToolCall,
      loadConversation,
      clearChat,
    }}>
      {children}
    </ChatContext.Provider>
  )
}
