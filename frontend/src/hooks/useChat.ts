import { useState, useCallback } from 'react'
import { Message } from '../components/Chat/MessageList'
import { ToolApprovalRequest } from '../components/Tools/ToolApprovalModal'
import { api } from '../services/api'

export function useChat(
  sessionId: string | null,
  onSessionChange: (id: string) => void
) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [pendingApproval, setPendingApproval] = useState<ToolApprovalRequest | null>(null)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(sessionId)

  const sendMessage = useCallback(async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await api.sendMessage(content, currentSessionId || undefined)

      // Update session ID if new
      if (response.session_id && response.session_id !== currentSessionId) {
        setCurrentSessionId(response.session_id)
        onSessionChange(response.session_id)
      }

      // Handle tool calls
      if (response.tool_calls && response.tool_calls.length > 0) {
        for (const toolCall of response.tool_calls) {
          // Show tool request in messages
          const toolMessage: Message = {
            id: `tool-${Date.now()}-${toolCall.name}`,
            role: 'tool',
            content: '',
            timestamp: new Date(),
            toolInfo: {
              name: toolCall.name,
              status: 'pending',
            },
          }
          setMessages(prev => [...prev, toolMessage])

          // Request approval
          setPendingApproval({
            tool: toolCall.name,
            params: toolCall.parameters,
            description: `Tool ${toolCall.name} möchte ausgeführt werden`,
            risk_level: 'medium', // Would come from backend
          })
        }
      } else if (response.message) {
        // Add assistant message
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: response.message,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, assistantMessage])
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Fehler beim Senden der Nachricht. Bitte versuche es erneut.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    }

    setIsLoading(false)
  }, [currentSessionId, onSessionChange])

  const approveToolCall = useCallback(async (scope: 'once' | 'session') => {
    if (!pendingApproval || !currentSessionId) return

    try {
      await api.approveTool(
        currentSessionId,
        pendingApproval.tool,
        pendingApproval.params,
        scope
      )

      // Update tool message status
      setMessages(prev => prev.map(msg => {
        if (msg.role === 'tool' && msg.toolInfo?.name === pendingApproval.tool && msg.toolInfo?.status === 'pending') {
          return {
            ...msg,
            toolInfo: {
              ...msg.toolInfo,
              status: 'approved',
            },
          }
        }
        return msg
      }))

      // In a real implementation, this would trigger tool execution
      // and then update the message with the result

    } catch (error) {
      console.error('Failed to approve tool:', error)
    }

    setPendingApproval(null)
  }, [pendingApproval, currentSessionId])

  const rejectToolCall = useCallback(() => {
    if (!pendingApproval) return

    // Update tool message status
    setMessages(prev => prev.map(msg => {
      if (msg.role === 'tool' && msg.toolInfo?.name === pendingApproval.tool && msg.toolInfo?.status === 'pending') {
        return {
          ...msg,
          toolInfo: {
            ...msg.toolInfo,
            status: 'rejected',
          },
        }
      }
      return msg
    }))

    // Add rejection message
    const rejectMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: `Tool "${pendingApproval.tool}" wurde abgelehnt.`,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, rejectMessage])

    setPendingApproval(null)
  }, [pendingApproval])

  return {
    messages,
    isLoading,
    pendingApproval,
    sendMessage,
    approveToolCall,
    rejectToolCall,
  }
}
