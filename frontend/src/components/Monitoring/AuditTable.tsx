import { Terminal, CheckCircle, XCircle, Clock } from 'lucide-react'
import clsx from 'clsx'

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

interface AuditTableProps {
  entries: AuditEntry[]
  onRowClick?: (entry: AuditEntry) => void
  loading?: boolean
}

const eventTypeConfig: Record<string, { icon: typeof Terminal; color: string }> = {
  tool_requested: { icon: Clock, color: 'text-yellow-500' },
  tool_approved: { icon: CheckCircle, color: 'text-green-500' },
  tool_rejected: { icon: XCircle, color: 'text-red-500' },
  tool_executed: { icon: Terminal, color: 'text-nv-accent' },
  tool_failed: { icon: XCircle, color: 'text-red-500' },
}

export default function AuditTable({ entries, onRowClick, loading }: AuditTableProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin w-8 h-8 border-2 border-nv-accent border-t-transparent rounded-full" />
      </div>
    )
  }

  if (entries.length === 0) {
    return (
      <div className="text-center p-8 text-gray-500">
        Keine Audit-Einträge gefunden
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="sticky top-0 bg-nv-black border-b border-nv-gray-light">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
              Zeit
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
              Event
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
              Tool
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
              Parameter
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
              Entscheidung
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
              Zeit (ms)
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-nv-gray-light">
          {entries.map((entry) => {
            const config = eventTypeConfig[entry.event_type] || {
              icon: Terminal,
              color: 'text-gray-500'
            }
            const Icon = config.icon

            return (
              <tr
                key={entry.id}
                onClick={() => onRowClick?.(entry)}
                className={clsx(
                  'hover:bg-nv-black/50 transition-colors',
                  onRowClick && 'cursor-pointer'
                )}
              >
                <td className="px-4 py-3 text-sm font-mono text-gray-400">
                  {new Date(entry.timestamp).toLocaleString('de-DE', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                  })}
                </td>
                <td className="px-4 py-3">
                  <div className={clsx('flex items-center gap-2', config.color)}>
                    <Icon className="w-4 h-4" />
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
                <td className="px-4 py-3 text-sm text-gray-400 max-w-xs truncate">
                  {entry.tool_params && (
                    <span title={JSON.stringify(entry.tool_params)}>
                      {JSON.stringify(entry.tool_params).slice(0, 50)}...
                    </span>
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
    </div>
  )
}
