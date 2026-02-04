import { useState } from 'react'
import Sidebar from './components/Layout/Sidebar'
import ChatContainer from './components/Chat/ChatContainer'
import AuditDashboard from './components/Monitoring/AuditDashboard'

type View = 'chat' | 'audit' | 'settings'

function App() {
  const [currentView, setCurrentView] = useState<View>('chat')
  const [currentSession, setCurrentSession] = useState<string | null>(null)

  return (
    <div className="flex h-screen bg-nv-black">
      {/* Sidebar */}
      <Sidebar
        currentView={currentView}
        onViewChange={setCurrentView}
        currentSession={currentSession}
        onNewChat={() => setCurrentSession(null)}
      />

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {currentView === 'chat' && (
          <ChatContainer
            sessionId={currentSession}
            onSessionChange={setCurrentSession}
          />
        )}
        {currentView === 'audit' && (
          <AuditDashboard />
        )}
        {currentView === 'settings' && (
          <div className="h-full flex items-center justify-center">
            <p className="text-gray-500">Settings coming soon...</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
