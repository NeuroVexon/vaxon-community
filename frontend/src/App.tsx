import { useState, useEffect } from 'react'
import Sidebar from './components/Layout/Sidebar'
import ChatContainer from './components/Chat/ChatContainer'
import AuditDashboard from './components/Monitoring/AuditDashboard'
import MemoryView from './components/Memory/MemoryView'
import SkillsView from './components/Skills/SkillsView'
import AgentsView from './components/Agents/AgentsView'
import SchedulerView from './components/Scheduler/SchedulerView'
import WorkflowsView from './components/Workflows/WorkflowsView'
import Dashboard from './components/Dashboard/Dashboard'
import LoginPage from './components/Auth/LoginPage'
import ErrorBoundary from './components/ErrorBoundary'
import { ChatProvider } from './contexts/ChatContext'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { useChat } from './hooks/useChat'
import { api } from './services/api'
import { Settings as SettingsIcon, Save, Loader2, Check, Key, Eye, EyeOff, Mail, CheckCircle, XCircle, Globe, MessageCircle, Hash, Trash2 } from 'lucide-react'
import clsx from 'clsx'
import { useTranslation } from 'react-i18next'
import type { Settings, View } from './types'

function SettingsView() {
  const { t, i18n } = useTranslation()
  const [settings, setSettings] = useState<Settings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [provider, setProvider] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  // Models
  const [ollamaModel, setOllamaModel] = useState('')
  const [claudeModel, setClaudeModel] = useState('')
  const [openaiModel, setOpenaiModel] = useState('')
  const [geminiModel, setGeminiModel] = useState('')
  const [groqModel, setGroqModel] = useState('')
  const [openrouterModel, setOpenrouterModel] = useState('')
  const [anthropicKey, setAnthropicKey] = useState('')
  const [openaiKey, setOpenaiKey] = useState('')
  const [geminiKey, setGeminiKey] = useState('')
  const [groqKey, setGroqKey] = useState('')
  const [openrouterKey, setOpenrouterKey] = useState('')
  const [showAnthropicKey, setShowAnthropicKey] = useState(false)
  const [showOpenaiKey, setShowOpenaiKey] = useState(false)
  const [showGeminiKey, setShowGeminiKey] = useState(false)
  const [showGroqKey, setShowGroqKey] = useState(false)
  const [showOpenrouterKey, setShowOpenrouterKey] = useState(false)
  // Telegram / Discord
  const [telegramEnabled, setTelegramEnabled] = useState(false)
  const [telegramToken, setTelegramToken] = useState('')
  const [discordEnabled, setDiscordEnabled] = useState(false)
  const [discordToken, setDiscordToken] = useState('')
  // E-Mail
  const [emailEnabled, setEmailEnabled] = useState(false)
  const [imapHost, setImapHost] = useState('')
  const [imapPort, setImapPort] = useState('993')
  const [imapUser, setImapUser] = useState('')
  const [imapPassword, setImapPassword] = useState('')
  const [smtpHost, setSmtpHost] = useState('')
  const [smtpPort, setSmtpPort] = useState('587')
  const [smtpUser, setSmtpUser] = useState('')
  const [smtpPassword, setSmtpPassword] = useState('')
  const [smtpFrom, setSmtpFrom] = useState('')
  const [emailTestResult, setEmailTestResult] = useState<{ imap: boolean; smtp: boolean; imap_error?: string | null; smtp_error?: string | null } | null>(null)
  const [emailTesting, setEmailTesting] = useState(false)

  const handleDeleteKey = async (keyName: string) => {
    try {
      const result = await api.deleteApiKey(keyName)
      console.log('Delete result:', result)
      alert(t('settings.keyDeleted'))
      await loadSettings()
    } catch (error) {
      console.error('Failed to delete API key:', error)
      alert('Error: ' + error)
    }
  }

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    setLoading(true)
    try {
      const data = await api.getSettings()
      setSettings(data)
      setProvider(data.llm_provider)
      setSystemPrompt(data.system_prompt || '')
      // Models
      setOllamaModel(data.ollama_model || '')
      setClaudeModel(data.claude_model || '')
      setOpenaiModel(data.openai_model || '')
      setGeminiModel(data.gemini_model || '')
      setGroqModel(data.groq_model || '')
      setOpenrouterModel(data.openrouter_model || '')
      // E-Mail
      setEmailEnabled(data.email_enabled || false)
      setImapHost(data.imap_host || '')
      setImapPort(data.imap_port || '993')
      setImapUser(data.imap_user || '')
      setSmtpHost(data.smtp_host || '')
      setSmtpPort(data.smtp_port || '587')
      setSmtpUser(data.smtp_user || '')
      setSmtpFrom(data.smtp_from || '')
      // Telegram / Discord
      setTelegramEnabled(data.telegram_enabled || false)
      setDiscordEnabled(data.discord_enabled || false)
      // Don't load actual keys/passwords - just show if they're set
    } catch (error) {
      console.error('Failed to load settings:', error)
    }
    setLoading(false)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const updates: Record<string, string> = {
        llm_provider: provider,
        system_prompt: systemPrompt,
        ollama_model: ollamaModel,
        claude_model: claudeModel,
        openai_model: openaiModel,
        gemini_model: geminiModel,
        groq_model: groqModel,
        openrouter_model: openrouterModel,
        email_enabled: emailEnabled ? 'true' : 'false',
        imap_host: imapHost,
        imap_port: imapPort,
        imap_user: imapUser,
        smtp_host: smtpHost,
        smtp_port: smtpPort,
        smtp_user: smtpUser,
        smtp_from: smtpFrom,
        telegram_enabled: telegramEnabled ? 'true' : 'false',
        discord_enabled: discordEnabled ? 'true' : 'false',
      }
      // Only send API keys/passwords if they were changed (not empty)
      if (anthropicKey) updates.anthropic_api_key = anthropicKey
      if (openaiKey) updates.openai_api_key = openaiKey
      if (geminiKey) updates.gemini_api_key = geminiKey
      if (groqKey) updates.groq_api_key = groqKey
      if (openrouterKey) updates.openrouter_api_key = openrouterKey
      if (imapPassword) updates.imap_password = imapPassword
      if (smtpPassword) updates.smtp_password = smtpPassword
      if (telegramToken) updates.telegram_bot_token = telegramToken
      if (discordToken) updates.discord_bot_token = discordToken
      await api.updateSettings(updates)
      setSaved(true)
      // Clear the key/password inputs after save
      setAnthropicKey('')
      setOpenaiKey('')
      setGeminiKey('')
      setGroqKey('')
      setOpenrouterKey('')
      setImapPassword('')
      setSmtpPassword('')
      setTelegramToken('')
      setDiscordToken('')
      // Reload settings to get updated masked keys
      await loadSettings()
      setTimeout(() => setSaved(false), 2000)
    } catch (error) {
      console.error('Failed to save settings:', error)
    }
    setSaving(false)
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-nv-accent" />
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto p-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <SettingsIcon className="w-8 h-8 text-nv-accent" />
          <h1 className="text-2xl font-bold">{t('settings.title')}</h1>
        </div>

        <div className="space-y-8">
          {/* LLM Provider */}
          <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
            <h2 className="text-lg font-semibold mb-4">{t('settings.llmProvider')}</h2>
            <div className="flex gap-3">
              {settings?.available_providers.map((p) => (
                <button
                  key={p}
                  onClick={() => setProvider(p)}
                  className={clsx(
                    'px-5 py-3 rounded-lg text-sm font-medium transition-all',
                    provider === p
                      ? 'bg-nv-accent text-nv-black shadow-nv-glow'
                      : 'bg-nv-black-lighter text-gray-400 hover:text-white border border-nv-gray-light'
                  )}
                >
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>
            <p className="text-sm text-gray-500 mt-3">
              {provider === 'ollama' && t('settings.providerOllama')}
              {provider === 'claude' && t('settings.providerClaude')}
              {provider === 'openai' && t('settings.providerOpenai')}
              {provider === 'gemini' && t('settings.providerGemini')}
              {provider === 'groq' && t('settings.providerGroq')}
              {provider === 'openrouter' && t('settings.providerOpenrouter')}
            </p>

            {/* Model Input */}
            <div className="mt-4">
              <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1">{t('agents.model')}</label>
              {provider === 'ollama' && (
                <input type="text" value={ollamaModel} onChange={(e) => setOllamaModel(e.target.value)}
                  placeholder="llama3.1:8b" className="w-full px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm font-mono placeholder-gray-500 focus:outline-none focus:border-nv-accent" />
              )}
              {provider === 'claude' && (
                <input type="text" value={claudeModel} onChange={(e) => setClaudeModel(e.target.value)}
                  placeholder="claude-sonnet-4-20250514" className="w-full px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm font-mono placeholder-gray-500 focus:outline-none focus:border-nv-accent" />
              )}
              {provider === 'openai' && (
                <input type="text" value={openaiModel} onChange={(e) => setOpenaiModel(e.target.value)}
                  placeholder="gpt-4o" className="w-full px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm font-mono placeholder-gray-500 focus:outline-none focus:border-nv-accent" />
              )}
              {provider === 'gemini' && (
                <input type="text" value={geminiModel} onChange={(e) => setGeminiModel(e.target.value)}
                  placeholder="gemini-2.0-flash" className="w-full px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm font-mono placeholder-gray-500 focus:outline-none focus:border-nv-accent" />
              )}
              {provider === 'groq' && (
                <input type="text" value={groqModel} onChange={(e) => setGroqModel(e.target.value)}
                  placeholder="llama-3.3-70b-versatile" className="w-full px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm font-mono placeholder-gray-500 focus:outline-none focus:border-nv-accent" />
              )}
              {provider === 'openrouter' && (
                <input type="text" value={openrouterModel} onChange={(e) => setOpenrouterModel(e.target.value)}
                  placeholder="anthropic/claude-sonnet-4" className="w-full px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm font-mono placeholder-gray-500 focus:outline-none focus:border-nv-accent" />
              )}
            </div>
          </div>

          {/* Claude API Key */}
          {(provider === 'claude' || settings?.anthropic_api_key_set) && (
            <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
              <div className="flex items-center gap-2 mb-4">
                <Key className="w-5 h-5 text-nv-accent" />
                <h2 className="text-lg font-semibold">Anthropic API Key</h2>
              </div>
              {settings?.anthropic_api_key_set && (
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm text-green-400">
                    ✓ {t('settings.apiKeySet', { masked: settings.anthropic_api_key_masked })}
                  </p>
                  <button
                    onClick={() => handleDeleteKey('anthropic_api_key')}
                    className="px-3 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-400/10 border border-red-400/30 rounded-lg transition-all flex items-center gap-1"
                  >
                    <Trash2 className="w-3 h-3" />
                    {t('settings.deleteKey')}
                  </button>
                </div>
              )}
              <div className="relative">
                <input
                  type={showAnthropicKey ? 'text' : 'password'}
                  value={anthropicKey}
                  onChange={(e) => setAnthropicKey(e.target.value)}
                  placeholder={settings?.anthropic_api_key_set ? t('settings.changeKey') : 'sk-ant-api...'}
                  className="w-full px-4 py-3 pr-12 bg-nv-black border border-nv-gray-light rounded-lg
                             text-white placeholder-gray-500 focus:outline-none focus:border-nv-accent font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowAnthropicKey(!showAnthropicKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                >
                  {showAnthropicKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {t('settings.getKeyAnthropic')}{' '}
                <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer"
                   className="text-nv-accent hover:underline">console.anthropic.com</a>
              </p>
            </div>
          )}

          {/* OpenAI API Key */}
          {(provider === 'openai' || settings?.openai_api_key_set) && (
            <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
              <div className="flex items-center gap-2 mb-4">
                <Key className="w-5 h-5 text-nv-accent" />
                <h2 className="text-lg font-semibold">OpenAI API Key</h2>
              </div>
              {settings?.openai_api_key_set && (
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm text-green-400">
                    ✓ {t('settings.apiKeySet', { masked: settings.openai_api_key_masked })}
                  </p>
                  <button
                    onClick={() => handleDeleteKey('openai_api_key')}
                    className="px-3 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-400/10 border border-red-400/30 rounded-lg transition-all flex items-center gap-1"
                  >
                    <Trash2 className="w-3 h-3" />
                    {t('settings.deleteKey')}
                  </button>
                </div>
              )}
              <div className="relative">
                <input
                  type={showOpenaiKey ? 'text' : 'password'}
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  placeholder={settings?.openai_api_key_set ? t('settings.changeKey') : 'sk-...'}
                  className="w-full px-4 py-3 pr-12 bg-nv-black border border-nv-gray-light rounded-lg
                             text-white placeholder-gray-500 focus:outline-none focus:border-nv-accent font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                >
                  {showOpenaiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {t('settings.getKeyOpenai')}{' '}
                <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer"
                   className="text-nv-accent hover:underline">platform.openai.com</a>
              </p>
            </div>
          )}

          {/* Gemini API Key */}
          {(provider === 'gemini' || settings?.gemini_api_key_set) && (
            <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
              <div className="flex items-center gap-2 mb-4">
                <Key className="w-5 h-5 text-nv-accent" />
                <h2 className="text-lg font-semibold">Google Gemini API Key</h2>
              </div>
              {settings?.gemini_api_key_set && (
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm text-green-400">
                    ✓ {t('settings.apiKeySet', { masked: settings.gemini_api_key_masked })}
                  </p>
                  <button
                    onClick={() => handleDeleteKey('gemini_api_key')}
                    className="px-3 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-400/10 border border-red-400/30 rounded-lg transition-all flex items-center gap-1"
                  >
                    <Trash2 className="w-3 h-3" />
                    {t('settings.deleteKey')}
                  </button>
                </div>
              )}
              <div className="relative">
                <input
                  type={showGeminiKey ? 'text' : 'password'}
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder={settings?.gemini_api_key_set ? t('settings.changeKey') : 'AIza...'}
                  className="w-full px-4 py-3 pr-12 bg-nv-black border border-nv-gray-light rounded-lg
                             text-white placeholder-gray-500 focus:outline-none focus:border-nv-accent font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowGeminiKey(!showGeminiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                >
                  {showGeminiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {t('settings.getKeyGemini')}{' '}
                <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer"
                   className="text-nv-accent hover:underline">aistudio.google.com</a>
              </p>
            </div>
          )}

          {/* Groq API Key */}
          {(provider === 'groq' || settings?.groq_api_key_set) && (
            <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
              <div className="flex items-center gap-2 mb-4">
                <Key className="w-5 h-5 text-nv-accent" />
                <h2 className="text-lg font-semibold">Groq API Key</h2>
              </div>
              {settings?.groq_api_key_set && (
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm text-green-400">
                    ✓ {t('settings.apiKeySet', { masked: settings.groq_api_key_masked })}
                  </p>
                  <button
                    onClick={() => handleDeleteKey('groq_api_key')}
                    className="px-3 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-400/10 border border-red-400/30 rounded-lg transition-all flex items-center gap-1"
                  >
                    <Trash2 className="w-3 h-3" />
                    {t('settings.deleteKey')}
                  </button>
                </div>
              )}
              <div className="relative">
                <input
                  type={showGroqKey ? 'text' : 'password'}
                  value={groqKey}
                  onChange={(e) => setGroqKey(e.target.value)}
                  placeholder={settings?.groq_api_key_set ? t('settings.changeKey') : 'gsk_...'}
                  className="w-full px-4 py-3 pr-12 bg-nv-black border border-nv-gray-light rounded-lg
                             text-white placeholder-gray-500 focus:outline-none focus:border-nv-accent font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowGroqKey(!showGroqKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                >
                  {showGroqKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {t('settings.getKeyGroq')}{' '}
                <a href="https://console.groq.com/keys" target="_blank" rel="noopener noreferrer"
                   className="text-nv-accent hover:underline">console.groq.com</a>
              </p>
            </div>
          )}

          {/* OpenRouter API Key */}
          {(provider === 'openrouter' || settings?.openrouter_api_key_set) && (
            <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
              <div className="flex items-center gap-2 mb-4">
                <Key className="w-5 h-5 text-nv-accent" />
                <h2 className="text-lg font-semibold">OpenRouter API Key</h2>
              </div>
              {settings?.openrouter_api_key_set && (
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm text-green-400">
                    ✓ {t('settings.apiKeySet', { masked: settings.openrouter_api_key_masked })}
                  </p>
                  <button
                    onClick={() => handleDeleteKey('openrouter_api_key')}
                    className="px-3 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-400/10 border border-red-400/30 rounded-lg transition-all flex items-center gap-1"
                  >
                    <Trash2 className="w-3 h-3" />
                    {t('settings.deleteKey')}
                  </button>
                </div>
              )}
              <div className="relative">
                <input
                  type={showOpenrouterKey ? 'text' : 'password'}
                  value={openrouterKey}
                  onChange={(e) => setOpenrouterKey(e.target.value)}
                  placeholder={settings?.openrouter_api_key_set ? t('settings.changeKey') : 'sk-or-...'}
                  className="w-full px-4 py-3 pr-12 bg-nv-black border border-nv-gray-light rounded-lg
                             text-white placeholder-gray-500 focus:outline-none focus:border-nv-accent font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowOpenrouterKey(!showOpenrouterKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                >
                  {showOpenrouterKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {t('settings.getKeyOpenrouter')}{' '}
                <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer"
                   className="text-nv-accent hover:underline">openrouter.ai</a>
              </p>
            </div>
          )}

          {/* System Prompt */}
          <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
            <h2 className="text-lg font-semibold mb-4">{t('settings.systemPrompt')}</h2>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder={t('settings.systemPromptPlaceholder')}
              rows={5}
              className="w-full px-4 py-3 bg-nv-black border border-nv-gray-light rounded-lg
                         text-white placeholder-gray-500 focus:outline-none focus:border-nv-accent
                         resize-none"
            />
          </div>

          {/* E-Mail Integration */}
          <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
            <div className="flex items-center gap-2 mb-4">
              <Mail className="w-5 h-5 text-nv-accent" />
              <h2 className="text-lg font-semibold">{t('settings.email')}</h2>
            </div>

            <label className="flex items-center gap-3 cursor-pointer mb-4">
              <input
                type="checkbox"
                checked={emailEnabled}
                onChange={(e) => setEmailEnabled(e.target.checked)}
                className="accent-nv-accent w-4 h-4"
              />
              <span className="text-sm font-medium">{t('settings.emailEnabled')}</span>
            </label>

            {emailEnabled && (
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">{t('settings.imapTitle')}</p>
                  <div className="grid grid-cols-3 gap-2">
                    <input
                      type="text" value={imapHost} onChange={(e) => setImapHost(e.target.value)}
                      placeholder="imap.example.com"
                      className="col-span-2 px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-nv-accent"
                    />
                    <input
                      type="text" value={imapPort} onChange={(e) => setImapPort(e.target.value)}
                      placeholder="993"
                      className="px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-nv-accent"
                    />
                  </div>
                  <input
                    type="text" value={imapUser} onChange={(e) => setImapUser(e.target.value)}
                    placeholder="user@example.com"
                    className="w-full mt-2 px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-nv-accent"
                  />
                  <input
                    type="password" value={imapPassword} onChange={(e) => setImapPassword(e.target.value)}
                    placeholder={settings?.imap_password_set ? t('settings.imapPasswordSet') : t('settings.imapPasswordPlaceholder')}
                    className="w-full mt-2 px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-nv-accent"
                  />
                </div>

                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">{t('settings.smtpTitle')}</p>
                  <div className="grid grid-cols-3 gap-2">
                    <input
                      type="text" value={smtpHost} onChange={(e) => setSmtpHost(e.target.value)}
                      placeholder="smtp.example.com"
                      className="col-span-2 px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-nv-accent"
                    />
                    <input
                      type="text" value={smtpPort} onChange={(e) => setSmtpPort(e.target.value)}
                      placeholder="587"
                      className="px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-nv-accent"
                    />
                  </div>
                  <input
                    type="text" value={smtpUser} onChange={(e) => setSmtpUser(e.target.value)}
                    placeholder="user@example.com"
                    className="w-full mt-2 px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-nv-accent"
                  />
                  <input
                    type="password" value={smtpPassword} onChange={(e) => setSmtpPassword(e.target.value)}
                    placeholder={settings?.smtp_password_set ? t('settings.smtpPasswordSet') : t('settings.smtpPasswordPlaceholder')}
                    className="w-full mt-2 px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-nv-accent"
                  />
                  <input
                    type="text" value={smtpFrom} onChange={(e) => setSmtpFrom(e.target.value)}
                    placeholder={t('settings.smtpFromPlaceholder')}
                    className="w-full mt-2 px-3 py-2 bg-nv-black border border-nv-gray-light rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-nv-accent"
                  />
                </div>

                {/* Test Button */}
                <button
                  onClick={async () => {
                    setEmailTesting(true)
                    setEmailTestResult(null)
                    try {
                      const result = await api.testEmailConnection()
                      setEmailTestResult(result)
                    } catch {
                      setEmailTestResult({ imap: false, smtp: false, imap_error: t('settings.testError'), smtp_error: t('settings.testError') })
                    }
                    setEmailTesting(false)
                  }}
                  disabled={emailTesting}
                  className="px-4 py-2 bg-nv-black-lighter text-sm text-gray-300 hover:text-white border border-nv-gray-light rounded-lg transition-all flex items-center gap-2"
                >
                  {emailTesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
                  {t('settings.testConnection')}
                </button>

                {emailTestResult && (
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center gap-2">
                      {emailTestResult.imap ? <CheckCircle className="w-4 h-4 text-green-400" /> : <XCircle className="w-4 h-4 text-red-400" />}
                      <span>IMAP: {emailTestResult.imap ? t('settings.connected') : emailTestResult.imap_error || t('settings.testFailed')}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {emailTestResult.smtp ? <CheckCircle className="w-4 h-4 text-green-400" /> : <XCircle className="w-4 h-4 text-red-400" />}
                      <span>SMTP: {emailTestResult.smtp ? t('settings.connected') : emailTestResult.smtp_error || t('settings.testFailed')}</span>
                    </div>
                  </div>
                )}

                <p className="text-xs text-gray-500">
                  {t('settings.emailReadonly')}
                </p>
              </div>
            )}
          </div>

          {/* Telegram Integration */}
          <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
            <div className="flex items-center gap-2 mb-4">
              <MessageCircle className="w-5 h-5 text-nv-accent" />
              <h2 className="text-lg font-semibold">{t('settings.telegram')}</h2>
            </div>
            <label className="flex items-center gap-3 cursor-pointer mb-4">
              <input
                type="checkbox"
                checked={telegramEnabled}
                onChange={(e) => setTelegramEnabled(e.target.checked)}
                className="accent-nv-accent w-4 h-4"
              />
              <span className="text-sm font-medium">{t('settings.telegramEnabled')}</span>
            </label>
            {telegramEnabled && (
              <input
                type="password"
                value={telegramToken}
                onChange={(e) => setTelegramToken(e.target.value)}
                placeholder={settings?.telegram_bot_token_set ? t('settings.telegramTokenSet') : t('settings.telegramTokenPlaceholder')}
                className="w-full px-4 py-3 bg-nv-black border border-nv-gray-light rounded-lg
                           text-white placeholder-gray-500 focus:outline-none focus:border-nv-accent font-mono"
              />
            )}
          </div>

          {/* Discord Integration */}
          <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
            <div className="flex items-center gap-2 mb-4">
              <Hash className="w-5 h-5 text-nv-accent" />
              <h2 className="text-lg font-semibold">{t('settings.discord')}</h2>
            </div>
            <label className="flex items-center gap-3 cursor-pointer mb-4">
              <input
                type="checkbox"
                checked={discordEnabled}
                onChange={(e) => setDiscordEnabled(e.target.checked)}
                className="accent-nv-accent w-4 h-4"
              />
              <span className="text-sm font-medium">{t('settings.discordEnabled')}</span>
            </label>
            {discordEnabled && (
              <input
                type="password"
                value={discordToken}
                onChange={(e) => setDiscordToken(e.target.value)}
                placeholder={settings?.discord_bot_token_set ? t('settings.discordTokenSet') : t('settings.discordTokenPlaceholder')}
                className="w-full px-4 py-3 bg-nv-black border border-nv-gray-light rounded-lg
                           text-white placeholder-gray-500 focus:outline-none focus:border-nv-accent font-mono"
              />
            )}
          </div>

          {/* Language Switcher */}
          <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
            <div className="flex items-center gap-2 mb-4">
              <Globe className="w-5 h-5 text-nv-accent" />
              <h2 className="text-lg font-semibold">{t('settings.language')}</h2>
            </div>
            <div className="flex gap-3">
              {[
                { code: 'de', label: 'Deutsch' },
                { code: 'en', label: 'English' },
              ].map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => {
                    i18n.changeLanguage(lang.code)
                    localStorage.setItem('axon-language', lang.code)
                    api.updateSettings({ language: lang.code })
                  }}
                  className={clsx(
                    'px-5 py-3 rounded-lg text-sm font-medium transition-all',
                    i18n.language === lang.code
                      ? 'bg-nv-accent text-nv-black shadow-nv-glow'
                      : 'bg-nv-black-lighter text-gray-400 hover:text-white border border-nv-gray-light'
                  )}
                >
                  {lang.label}
                </button>
              ))}
            </div>
          </div>

          {/* App Info */}
          <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
            <h2 className="text-lg font-semibold mb-4">{t('settings.about')}</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">{t('settings.appName')}</span>
                <span>{settings?.app_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">{t('settings.version')}</span>
                <span className="font-mono">{settings?.app_version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">{t('settings.activeProvider')}</span>
                <span className="text-nv-accent">{settings?.llm_provider}</span>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full px-6 py-4 bg-nv-accent text-nv-black font-semibold rounded-xl
                       hover:bg-opacity-90 disabled:opacity-50 flex items-center justify-center gap-2
                       shadow-nv-glow transition-all"
          >
            {saving ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : saved ? (
              <Check className="w-5 h-5" />
            ) : (
              <Save className="w-5 h-5" />
            )}
            {saved ? t('settings.saved') : t('settings.save')}
          </button>
        </div>
      </div>
    </div>
  )
}

interface AppContentProps {
  currentSession: string | null
  setCurrentSession: (session: string | null) => void
  currentAgentId: string | null
  setCurrentAgentId: (id: string | null) => void
}

function AppContent({ currentSession, setCurrentSession, currentAgentId, setCurrentAgentId }: AppContentProps) {
  const [currentView, setCurrentView] = useState<View>('dashboard')
  const { clearChat, loadConversation } = useChat()

  const handleSelectConversation = (id: string) => {
    setCurrentSession(id)
    loadConversation(id)
  }

  const handleNewChat = () => {
    setCurrentSession(null)
    clearChat()
  }

  return (
    <div className="flex h-screen bg-nv-black">
      {/* Sidebar */}
      <Sidebar
        currentView={currentView}
        onViewChange={setCurrentView}
        currentSession={currentSession}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
      />

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {currentView === 'dashboard' && (
          <Dashboard onNavigate={setCurrentView} />
        )}
        {currentView === 'chat' && (
          <ChatContainer
            agentId={currentAgentId}
            onAgentChange={setCurrentAgentId}
          />
        )}
        {currentView === 'audit' && (
          <AuditDashboard />
        )}
        {currentView === 'memory' && (
          <MemoryView />
        )}
        {currentView === 'skills' && (
          <SkillsView />
        )}
        {currentView === 'agents' && (
          <AgentsView />
        )}
        {currentView === 'scheduler' && (
          <SchedulerView />
        )}
        {currentView === 'workflows' && (
          <WorkflowsView />
        )}
        {currentView === 'settings' && (
          <SettingsView />
        )}
      </main>
    </div>
  )
}

function AuthGate() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-nv-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-nv-accent" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return <AuthenticatedApp />
}

function AuthenticatedApp() {
  const [currentSession, setCurrentSession] = useState<string | null>(null)
  const [currentAgentId, setCurrentAgentId] = useState<string | null>(null)

  return (
    <ChatProvider onSessionChange={(id) => setCurrentSession(id)} agentId={currentAgentId}>
      <AppContent
        currentSession={currentSession}
        setCurrentSession={setCurrentSession}
        currentAgentId={currentAgentId}
        setCurrentAgentId={setCurrentAgentId}
      />
    </ChatProvider>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AuthGate />
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
