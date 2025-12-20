import { useState } from 'react'
import Dashboard from './components/Dashboard'
import QueueViewer from './components/QueueViewer'
import ConfigEditor from './components/ConfigEditor'
import HookManager from './components/HookManager'
import TTSTester from './components/TTSTester'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  const tabs = [
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'queue', label: '🎵 Queue', icon: '🎵' },
    { id: 'hooks', label: '🎚️ Hooks', icon: '🎚️' },
    { id: 'config', label: '⚙️ Config', icon: '⚙️' },
    { id: 'test', label: '🧪 Test TTS', icon: '🧪' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-md border-b border-purple-500/30">
        <div className="container mx-auto px-6 py-4">
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            🎸 Voice Handler Control Panel
            <span className="text-sm font-normal text-purple-300">v1.0.0</span>
          </h1>
          <p className="text-purple-200 text-sm mt-1">
            Rock'n'Roll control center for Claude Code voice notifications
          </p>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-black/20 backdrop-blur-md border-b border-purple-500/20">
        <div className="container mx-auto px-6">
          <div className="flex gap-2 overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  px-6 py-3 font-medium transition-all whitespace-nowrap
                  ${activeTab === tab.id
                    ? 'bg-purple-600 text-white border-b-2 border-purple-400'
                    : 'text-purple-200 hover:text-white hover:bg-purple-700/30'
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="bg-white/10 backdrop-blur-md rounded-lg shadow-2xl border border-purple-500/30 p-6">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'queue' && <QueueViewer />}
          {activeTab === 'hooks' && <HookManager />}
          {activeTab === 'config' && <ConfigEditor />}
          {activeTab === 'test' && <TTSTester />}
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-6 text-purple-200 text-sm">
        <p>🎸 Made with rock'n'roll vibes | Powered by Claude Code</p>
      </footer>
    </div>
  )
}

export default App
