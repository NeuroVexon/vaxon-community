import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'

export interface AuditEntry {
  id: string
  sessionId: string
  timestamp: string
  eventType: string
  toolName: string | null
  toolParams: Record<string, unknown> | null
  result: string | null
  error: string | null
  userDecision: string | null
  executionTimeMs: number | null
}

export interface AuditStats {
  total: number
  byEventType: Record<string, number>
  byTool: Record<string, number>
  avgExecutionTimeMs: number | null
}

interface UseAuditOptions {
  sessionId?: string
  autoRefresh?: boolean
  refreshInterval?: number
}

export function useAudit({
  sessionId,
  autoRefresh = false,
  refreshInterval = 5000
}: UseAuditOptions = {}) {
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [stats, setStats] = useState<AuditStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchEntries = useCallback(async () => {
    try {
      const data = await api.getAuditLogs({
        sessionId,
        limit: 100
      })

      // Transform snake_case to camelCase
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const transformed = (data as any[]).map((entry) => ({
        id: entry.id as string,
        sessionId: entry.session_id as string,
        timestamp: entry.timestamp as string,
        eventType: entry.event_type as string,
        toolName: entry.tool_name as string | null,
        toolParams: entry.tool_params as Record<string, unknown> | null,
        result: entry.result as string | null,
        error: entry.error as string | null,
        userDecision: entry.user_decision as string | null,
        executionTimeMs: entry.execution_time_ms as number | null
      })) as AuditEntry[]

      setEntries(transformed)
      setError(null)
    } catch (err) {
      setError('Failed to load audit logs')
      console.error('Failed to fetch audit entries:', err)
    }
  }, [sessionId])

  const fetchStats = useCallback(async () => {
    try {
      const data = await api.getAuditStats(sessionId)

      setStats({
        total: data.total,
        byEventType: data.by_event_type,
        byTool: data.by_tool,
        avgExecutionTimeMs: data.avg_execution_time_ms
      })
    } catch (err) {
      console.error('Failed to fetch audit stats:', err)
    }
  }, [sessionId])

  const refresh = useCallback(async () => {
    setLoading(true)
    await Promise.all([fetchEntries(), fetchStats()])
    setLoading(false)
  }, [fetchEntries, fetchStats])

  // Initial load
  useEffect(() => {
    refresh()
  }, [refresh])

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchEntries()
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, fetchEntries])

  const exportLogs = useCallback((format: 'csv' | 'json' = 'csv') => {
    const params = new URLSearchParams()
    params.set('format', format)
    if (sessionId) params.set('session_id', sessionId)

    window.open(`/api/v1/audit/export?${params}`, '_blank')
  }, [sessionId])

  return {
    entries,
    stats,
    loading,
    error,
    refresh,
    exportLogs
  }
}
