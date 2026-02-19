import { useState, useEffect } from 'react'
import {
  MessageSquare,
  ClipboardList,
  Settings,
  Plus,
  Bird,
  Brain,
  Puzzle,
  Bot,
  Clock,
  GitBranch,
  BarChart3,
  Trash2
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '../../services/api'
import { useTranslation } from 'react-i18next'
import type { Conversation, View } from '../../types'

interface SidebarProps {
  currentView: View
  onViewChange: (view: View) => void
  currentSession: string | null
  onNewChat: () => void
  onSelectConversation?: (id: string) => void
}

export default function Sidebar({
  currentView,
  onViewChange,
  currentSession,
  onNewChat,
  onSelectConversation
}: SidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const { t } = useTranslation()

  const navItems = [
    { id: 'dashboard' as const, label: t('sidebar.dashboard'), icon: BarChart3 },
    { id: 'chat' as const, label: t('sidebar.chat'), icon: MessageSquare },
    { id: 'memory' as const, label: t('sidebar.memory'), icon: Brain },
    { id: 'agents' as const, label: t('sidebar.agents'), icon: Bot },
    { id: 'scheduler' as const, label: t('sidebar.scheduler'), icon: Clock },
    { id: 'workflows' as const, label: t('sidebar.workflows'), icon: GitBranch },
    { id: 'skills' as const, label: t('sidebar.skills'), icon: Puzzle },
    { id: 'audit' as const, label: t('sidebar.audit'), icon: ClipboardList },
    { id: 'settings' as const, label: t('sidebar.settings'), icon: Settings },
  ]

  useEffect(() => {
    loadConversations()
  }, [currentSession])

  const loadConversations = async () => {
    try {
      const data = await api.getConversations(20)
      setConversations(data)
    } catch {
      // Silently fail - sidebar still works
    }
  }

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    try {
      await api.deleteConversation(id)
      setConversations(prev => prev.filter(c => c.id !== id))
      if (currentSession === id) {
        onNewChat()
      }
    } catch {
      // Silently fail
    }
  }

  const handleSelect = (id: string) => {
    onViewChange('chat')
    onSelectConversation?.(id)
  }

  return (
    <aside className="w-64 bg-nv-black border-r border-nv-gray-light h-screen flex flex-col">
      {/* Logo */}
      <div className="flex-none p-4 border-b border-nv-gray-light">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-nv-black-lighter rounded-lg flex items-center justify-center">
            <Bird className="w-5 h-5 text-nv-accent" />
          </div>
          <div>
            <h1 className="font-display text-base font-bold tracking-wider">AXON</h1>
            <p className="text-[10px] text-gray-500 font-mono">by NeuroVexon</p>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="flex-none px-3 py-3">
        <button
          onClick={() => { onNewChat(); onViewChange('chat') }}
          className="w-full px-3 py-2.5 bg-nv-accent text-nv-black font-semibold rounded-lg
                     hover:bg-opacity-90 shadow-nv-glow transition-all flex items-center justify-center gap-2 text-sm"
        >
          <Plus className="w-4 h-4" />
          {t('sidebar.newChat')}
        </button>
      </div>

      {/* Navigation + Conversation History - scrollable together */}
      <div className="flex-1 min-h-0 overflow-y-auto px-3">
        <nav className="space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = currentView === item.id

            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={clsx(
                  'w-full px-3 py-1.5 rounded-lg flex items-center gap-2.5 transition-all text-sm',
                  isActive
                    ? 'bg-nv-accent text-nv-black font-semibold shadow-nv-glow'
                    : 'text-gray-400 hover:text-white hover:bg-nv-black-lighter'
                )}
              >
                <Icon className="w-4 h-4 flex-none" />
                {item.label}
              </button>
            )
          })}
        </nav>

        {/* Conversation History */}
        {conversations.length > 0 && (
          <div className="mt-3 pt-3 border-t border-nv-gray-light">
            <p className="text-xs text-gray-600 uppercase tracking-wider mb-2 px-2">
              {t('sidebar.history')}
            </p>
            <div className="space-y-0.5 pb-2">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => handleSelect(conv.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSelect(conv.id) }}
                  className={clsx(
                    'w-full px-3 py-1.5 rounded-lg text-left text-sm transition-all group flex items-center gap-2 cursor-pointer',
                    currentSession === conv.id
                      ? 'bg-nv-accent/10 text-nv-accent border border-nv-accent/30'
                      : 'text-gray-400 hover:text-white hover:bg-nv-black-lighter'
                  )}
                >
                  <span className="truncate flex-1">
                    {conv.title || t('sidebar.untitled')}
                  </span>
                  <button
                    onClick={(e) => { e.stopPropagation(); e.preventDefault(); handleDelete(e, conv.id) }}
                    className="flex-none opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto p-1 hover:text-red-400 transition-opacity"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex-none px-4 py-2 border-t border-nv-gray-light">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <div className="w-2 h-2 bg-nv-success rounded-full animate-pulse" />
          <span>Axon v2.0.0</span>
        </div>
      </div>
    </aside>
  )
}
