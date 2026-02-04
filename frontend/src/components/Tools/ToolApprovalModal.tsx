import React from 'react'
import {
  AlertTriangle,
  Shield,
  Terminal,
  Globe,
  FileText,
  X
} from 'lucide-react'
import clsx from 'clsx'

export interface ToolApprovalRequest {
  tool: string
  params: Record<string, unknown>
  description: string
  risk_level: 'low' | 'medium' | 'high' | 'critical'
}

interface ToolApprovalModalProps {
  request: ToolApprovalRequest
  onApprove: (scope: 'once' | 'session') => void
  onReject: () => void
}

const riskConfig = {
  low: {
    color: 'text-green-500',
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    label: 'Niedriges Risiko'
  },
  medium: {
    color: 'text-yellow-500',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    label: 'Mittleres Risiko'
  },
  high: {
    color: 'text-orange-500',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    label: 'Hohes Risiko'
  },
  critical: {
    color: 'text-red-500',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    label: 'Kritisch'
  },
}

const toolIcons: Record<string, React.ReactNode> = {
  file_read: <FileText className="w-5 h-5" />,
  file_write: <FileText className="w-5 h-5" />,
  file_list: <FileText className="w-5 h-5" />,
  web_fetch: <Globe className="w-5 h-5" />,
  web_search: <Globe className="w-5 h-5" />,
  shell_execute: <Terminal className="w-5 h-5" />,
  code_execute: <Terminal className="w-5 h-5" />,
}

export default function ToolApprovalModal({
  request,
  onApprove,
  onReject,
}: ToolApprovalModalProps) {
  const risk = riskConfig[request.risk_level]

  return (
    <div className="modal-backdrop animate-fade-in">
      <div className="bg-nv-black-200 rounded-2xl shadow-2xl max-w-md w-full mx-4 overflow-hidden animate-slide-up border border-nv-gray-light">
        {/* Header */}
        <div className="bg-nv-black px-6 py-4 border-b border-nv-gray-light flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-6 h-6 text-nv-accent" />
            <h2 className="text-lg font-semibold">Tool-Genehmigung</h2>
          </div>
          <button
            onClick={onReject}
            className="p-1 hover:bg-nv-black-lighter rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-4">
          {/* Tool Info */}
          <div className="flex items-start gap-3">
            <div className="p-2 bg-nv-black-lighter rounded-lg text-nv-accent">
              {toolIcons[request.tool] || <Terminal className="w-5 h-5" />}
            </div>
            <div>
              <h3 className="font-mono font-medium">{request.tool}</h3>
              <p className="text-sm text-gray-400">{request.description}</p>
            </div>
          </div>

          {/* Risk Badge */}
          <div className={clsx(
            'inline-flex items-center gap-2 px-3 py-1 rounded-full border',
            risk.bg, risk.border
          )}>
            <AlertTriangle className={clsx('w-4 h-4', risk.color)} />
            <span className={clsx('text-sm font-medium', risk.color)}>
              {risk.label}
            </span>
          </div>

          {/* Parameters */}
          <div className="bg-nv-black rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-2 uppercase tracking-wide">
              Parameter
            </p>
            <pre className="text-sm text-gray-300 overflow-x-auto font-mono">
              {JSON.stringify(request.params, null, 2)}
            </pre>
          </div>

          {/* Warning */}
          {(request.risk_level === 'high' || request.risk_level === 'critical') && (
            <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-300">
                Diese Aktion kann Änderungen an deinem System vornehmen.
                Prüfe die Parameter sorgfältig.
              </p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="px-6 py-4 bg-nv-black border-t border-nv-gray-light">
          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <button
                onClick={() => onApprove('once')}
                className="flex-1 px-4 py-2.5 bg-nv-accent hover:bg-opacity-90
                           text-nv-black font-semibold rounded-lg transition-colors"
              >
                Einmal erlauben
              </button>
              <button
                onClick={() => onApprove('session')}
                className="flex-1 px-4 py-2.5 bg-nv-success hover:bg-opacity-90
                           text-nv-black font-semibold rounded-lg transition-colors"
              >
                Für Session
              </button>
            </div>
            <button
              onClick={onReject}
              className="w-full px-4 py-2.5 bg-nv-black-lighter hover:bg-nv-gray
                         text-gray-300 font-medium rounded-lg transition-colors
                         border border-nv-gray-light"
            >
              Ablehnen
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
