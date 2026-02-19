import React, { useState, useEffect } from 'react'
import {
  Download,
  Filter,
  RefreshCw,
  Terminal,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react'
import clsx from 'clsx'
import { useTranslation } from 'react-i18next'
import { api } from '../../services/api'

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

export default function AuditDashboard() {
  const { t } = useTranslation()
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('')

  useEffect(() => {
    loadAuditLogs()
  }, [])

  const loadAuditLogs = async () => {
    setLoading(true)
    try {
      const data = await api.getAuditLogs({ limit: 100 })
      setEntries(data)
    } catch (error) {
      console.error('Failed to load audit logs:', error)
    }
    setLoading(false)
  }

  const exportCSV = async () => {
    try {
      const data = await api.getAuditLogs()
      const header = ['id','session_id','timestamp','event_type','tool_name','tool_params','result','error','user_decision','execution_time_ms']
      const rows = data.map(e => [e.id, e.session_id, e.timestamp, e.event_type, e.tool_name ?? '', JSON.stringify(e.tool_params ?? ''), e.result ?? '', e.error ?? '', e.user_decision ?? '', e.execution_time_ms ?? ''])
      const csv = [header, ...rows].map(r => r.join(',')).join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'axon_audit_log.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export audit logs:', error)
    }
  }

  const filteredEntries = entries.filter(entry =>
    !filter ||
    entry.tool_name?.toLowerCase().includes(filter.toLowerCase()) ||
    entry.event_type.toLowerCase().includes(filter.toLowerCase())
  )

  const eventTypeConfig: Record<string, { icon: React.ReactNode; color: string }> = {
    tool_requested: { icon: <Clock className="w-4 h-4" />, color: 'text-yellow-500' },
    tool_approved: { icon: <CheckCircle className="w-4 h-4" />, color: 'text-green-500' },
    tool_rejected: { icon: <XCircle className="w-4 h-4" />, color: 'text-red-500' },
    tool_executed: { icon: <Terminal className="w-4 h-4" />, color: 'text-nv-accent' },
    tool_failed: { icon: <XCircle className="w-4 h-4" />, color: 'text-red-500' },
  }

  return (
    <div className="h-full flex flex-col bg-nv-black-100 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-display font-bold">{t('audit.title')}</h1>
          <p className="text-gray-500 text-sm mt-1">
            {t('audit.subtitle')}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadAuditLogs}
            className="p-2 bg-nv-black-lighter border border-nv-gray-light rounded-lg
                       hover:border-nv-accent transition-colors"
          >
            <RefreshCw className={clsx('w-5 h-5', loading && 'animate-spin')} />
          </button>
          <button
            onClick={exportCSV}
            className="px-4 py-2 bg-nv-accent text-nv-black font-semibold rounded-lg
                       hover:bg-opacity-90 flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            {t('audit.csvExport')}
          </button>
        </div>
      </div>

      {/* Filter */}
      <div className="mb-4">
        <div className="relative max-w-md">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder={t('audit.filterPlaceholder')}
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-nv-black-lighter border border-nv-gray-light
                       rounded-lg text-white placeholder-gray-500 focus:outline-none
                       focus:border-nv-accent transition-colors"
          />
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto bg-nv-black-lighter rounded-xl border border-nv-gray-light">
        <table className="w-full">
          <thead className="sticky top-0 bg-nv-black border-b border-nv-gray-light">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
                {t('audit.colTime')}
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
                {t('audit.colEvent')}
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
                {t('audit.colTool')}
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
                {t('audit.colDecision')}
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
                {t('audit.colDuration')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-nv-gray-light">
            {filteredEntries.map((entry) => {
              const config = eventTypeConfig[entry.event_type] || {
                icon: <Terminal className="w-4 h-4" />,
                color: 'text-gray-500'
              }

              return (
                <tr key={entry.id} className="hover:bg-nv-black/50 transition-colors">
                  <td className="px-4 py-3 text-sm font-mono text-gray-400">
                    {new Date(entry.timestamp).toLocaleString('de-DE', {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit'
                    })}
                  </td>
                  <td className="px-4 py-3">
                    <div className={clsx('flex items-center gap-2', config.color)}>
                      {config.icon}
                      <span className="text-sm">{entry.event_type}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {entry.tool_name && (
                      <code className="text-sm bg-nv-black px-2 py-1 rounded font-mono">
                        {entry.tool_name}
                      </code>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {entry.user_decision || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-gray-400">
                    {entry.execution_time_ms ?? '-'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {filteredEntries.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            {loading ? t('audit.loading') : t('audit.empty')}
          </div>
        )}
      </div>
    </div>
  )
}
