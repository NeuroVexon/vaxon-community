import { Terminal, CheckCircle, XCircle, Loader2, Clock } from 'lucide-react'
import clsx from 'clsx'

export type ToolStatus = 'pending' | 'approved' | 'executing' | 'executed' | 'failed' | 'rejected'

interface ToolExecutionBadgeProps {
  toolName: string
  status: ToolStatus
  executionTimeMs?: number
  compact?: boolean
}

const statusConfig: Record<ToolStatus, {
  icon: typeof Terminal
  color: string
  bgColor: string
  label: string
}> = {
  pending: {
    icon: Clock,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    label: 'Warte auf Genehmigung'
  },
  approved: {
    icon: CheckCircle,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    label: 'Genehmigt'
  },
  executing: {
    icon: Loader2,
    color: 'text-nv-accent',
    bgColor: 'bg-nv-accent/10',
    label: 'Wird ausgeführt'
  },
  executed: {
    icon: CheckCircle,
    color: 'text-nv-accent',
    bgColor: 'bg-nv-accent/10',
    label: 'Ausgeführt'
  },
  failed: {
    icon: XCircle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    label: 'Fehlgeschlagen'
  },
  rejected: {
    icon: XCircle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    label: 'Abgelehnt'
  }
}

export default function ToolExecutionBadge({
  toolName,
  status,
  executionTimeMs,
  compact = false
}: ToolExecutionBadgeProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  if (compact) {
    return (
      <span
        className={clsx(
          'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
          config.bgColor,
          config.color
        )}
      >
        <Icon className={clsx('w-3 h-3', status === 'executing' && 'animate-spin')} />
        {toolName}
      </span>
    )
  }

  return (
    <div className={clsx('rounded-lg p-3', config.bgColor)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={clsx('w-4 h-4', config.color, status === 'executing' && 'animate-spin')} />
          <span className="font-mono text-sm font-medium">{toolName}</span>
        </div>
        <span className={clsx('text-xs px-2 py-0.5 rounded-full', config.bgColor, config.color)}>
          {config.label}
        </span>
      </div>

      {executionTimeMs !== undefined && status === 'executed' && (
        <p className="text-xs text-gray-500 mt-1">
          Ausgeführt in {executionTimeMs}ms
        </p>
      )}
    </div>
  )
}
