import {
  MessageSquare,
  ClipboardList,
  Settings,
  Plus,
  Bird
} from 'lucide-react'
import clsx from 'clsx'

interface SidebarProps {
  currentView: 'chat' | 'audit' | 'settings'
  onViewChange: (view: 'chat' | 'audit' | 'settings') => void
  currentSession: string | null
  onNewChat: () => void
}

export default function Sidebar({
  currentView,
  onViewChange,
  onNewChat
}: SidebarProps) {
  const navItems = [
    { id: 'chat' as const, label: 'Chat', icon: MessageSquare },
    { id: 'audit' as const, label: 'Audit Log', icon: ClipboardList },
    { id: 'settings' as const, label: 'Einstellungen', icon: Settings },
  ]

  return (
    <aside className="w-64 bg-nv-black border-r border-nv-gray-light h-screen flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-nv-gray-light">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-nv-black-lighter rounded-lg flex items-center justify-center">
            <Bird className="w-6 h-6 text-nv-accent" />
          </div>
          <div>
            <h1 className="font-display text-lg font-bold tracking-wider">AXON</h1>
            <p className="text-xs text-gray-500 font-mono">by NeuroVexon</p>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="w-full px-4 py-3 bg-nv-accent text-nv-black font-semibold rounded-lg
                     hover:bg-opacity-90 shadow-nv-glow transition-all flex items-center justify-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Neuer Chat
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = currentView === item.id

          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={clsx(
                'w-full px-4 py-3 rounded-lg flex items-center gap-3 transition-all',
                isActive
                  ? 'bg-nv-accent text-nv-black font-semibold shadow-nv-glow'
                  : 'text-gray-400 hover:text-white hover:bg-nv-black-lighter'
              )}
            >
              <Icon className="w-5 h-5" />
              {item.label}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-nv-gray-light">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <div className="w-2 h-2 bg-nv-success rounded-full animate-pulse" />
          <span>Axon v1.0.0</span>
        </div>
        <p className="text-xs text-gray-600 mt-1">
          Agentic AI - ohne Kontrollverlust
        </p>
      </div>
    </aside>
  )
}
