import { useState, useCallback } from 'react'
import { api } from '../services/api'

export interface ToolApprovalRequest {
  tool: string
  params: Record<string, unknown>
  description: string
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
}

export type ApprovalDecision = 'once' | 'session' | 'never'

interface UseToolApprovalOptions {
  sessionId: string | null
  onApproved?: (tool: string, decision: ApprovalDecision) => void
  onRejected?: (tool: string) => void
}

export function useToolApproval({
  sessionId,
  onApproved,
  onRejected
}: UseToolApprovalOptions) {
  const [pendingApproval, setPendingApproval] = useState<ToolApprovalRequest | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const requestApproval = useCallback((request: ToolApprovalRequest) => {
    setPendingApproval(request)
  }, [])

  const approve = useCallback(async (decision: ApprovalDecision) => {
    if (!pendingApproval || !sessionId) return

    setIsProcessing(true)
    try {
      await api.approveTool(
        sessionId,
        pendingApproval.tool,
        pendingApproval.params,
        decision
      )
      onApproved?.(pendingApproval.tool, decision)
    } catch (error) {
      console.error('Failed to approve tool:', error)
    }
    setIsProcessing(false)
    setPendingApproval(null)
  }, [pendingApproval, sessionId, onApproved])

  const reject = useCallback(() => {
    if (!pendingApproval) return

    onRejected?.(pendingApproval.tool)
    setPendingApproval(null)
  }, [pendingApproval, onRejected])

  const block = useCallback(async () => {
    if (!pendingApproval || !sessionId) return

    setIsProcessing(true)
    try {
      await api.approveTool(
        sessionId,
        pendingApproval.tool,
        pendingApproval.params,
        'never'
      )
      onRejected?.(pendingApproval.tool)
    } catch (error) {
      console.error('Failed to block tool:', error)
    }
    setIsProcessing(false)
    setPendingApproval(null)
  }, [pendingApproval, sessionId, onRejected])

  return {
    pendingApproval,
    isProcessing,
    requestApproval,
    approve,
    reject,
    block
  }
}
