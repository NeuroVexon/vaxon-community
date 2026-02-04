import React from 'react'
import { User, Bot, Terminal, AlertCircle, CheckCircle } from 'lucide-react'
import clsx from 'clsx'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  timestamp: Date
  toolInfo?: {
    name: string
    status: 'pending' | 'approved' | 'rejected' | 'executed' | 'failed'
    result?: string
    error?: string
  }
}

interface MessageListProps {
  messages: Message[]
}

export default function MessageList({ messages }: MessageListProps) {
  return (
    <div className="space-y-4 max-w-4xl mx-auto">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  const isTool = message.role === 'tool'

  if (isTool && message.toolInfo) {
    return <ToolMessage toolInfo={message.toolInfo} />
  }

  return (
    <div
      className={clsx(
        'flex gap-3 animate-fade-in',
        isUser ? 'flex-row-reverse' : ''
      )}
    >
      {/* Avatar */}
      <div
        className={clsx(
          'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
          isUser ? 'bg-nv-accent' : 'bg-nv-black-lighter border border-nv-gray-light'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-nv-black" />
        ) : (
          <Bot className="w-4 h-4 text-nv-accent" />
        )}
      </div>

      {/* Message Content */}
      <div
        className={clsx(
          'max-w-[80%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-nv-accent/10 border border-nv-accent/30'
            : 'bg-nv-black-lighter border border-nv-gray-light'
        )}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        <p className="text-xs text-gray-500 mt-2">
          {message.timestamp.toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  )
}

function ToolMessage({ toolInfo }: { toolInfo: Message['toolInfo'] }) {
  if (!toolInfo) return null

  const statusConfig = {
    pending: { icon: Terminal, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
    approved: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-500/10' },
    rejected: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
    executed: { icon: CheckCircle, color: 'text-nv-accent', bg: 'bg-nv-accent/10' },
    failed: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
  }

  const config = statusConfig[toolInfo.status]
  const Icon = config.icon

  return (
    <div className={clsx('rounded-lg p-4 animate-fade-in', config.bg)}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className={clsx('w-4 h-4', config.color)} />
        <span className="font-mono text-sm font-medium">{toolInfo.name}</span>
        <span className={clsx('text-xs px-2 py-0.5 rounded-full', config.bg, config.color)}>
          {toolInfo.status}
        </span>
      </div>

      {toolInfo.result && (
        <pre className="text-xs bg-nv-black rounded p-2 mt-2 overflow-x-auto font-mono">
          {toolInfo.result.slice(0, 500)}
          {toolInfo.result.length > 500 && '...'}
        </pre>
      )}

      {toolInfo.error && (
        <p className="text-xs text-red-400 mt-2">{toolInfo.error}</p>
      )}
    </div>
  )
}
