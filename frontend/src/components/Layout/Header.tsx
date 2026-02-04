import { Settings, Moon, Sun, RefreshCw } from 'lucide-react'
import { useState } from 'react'

interface HeaderProps {
  title?: string
  onSettingsClick?: () => void
  onRefresh?: () => void
}

export default function Header({ title, onSettingsClick, onRefresh }: HeaderProps) {
  const [isDark, setIsDark] = useState(true)

  const toggleTheme = () => {
    setIsDark(!isDark)
    // In production, this would update the actual theme
    document.documentElement.classList.toggle('dark')
  }

  return (
    <header className="h-14 bg-nv-black border-b border-nv-gray-light flex items-center justify-between px-6">
      {/* Title */}
      <div className="flex items-center gap-3">
        {title && (
          <h1 className="text-lg font-semibold text-white">{title}</h1>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-2 text-gray-400 hover:text-white hover:bg-nv-black-lighter
                       rounded-lg transition-colors"
            title="Aktualisieren"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        )}

        <button
          onClick={toggleTheme}
          className="p-2 text-gray-400 hover:text-white hover:bg-nv-black-lighter
                     rounded-lg transition-colors"
          title={isDark ? 'Light Mode' : 'Dark Mode'}
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        {onSettingsClick && (
          <button
            onClick={onSettingsClick}
            className="p-2 text-gray-400 hover:text-white hover:bg-nv-black-lighter
                       rounded-lg transition-colors"
            title="Einstellungen"
          >
            <Settings className="w-5 h-5" />
          </button>
        )}
      </div>
    </header>
  )
}
