import { useState, useEffect } from 'react'
import { X, Save, Loader2, Check, Globe } from 'lucide-react'
import clsx from 'clsx'
import { api } from '../../services/api'
import { useTranslation } from 'react-i18next'

interface SettingsPanelProps {
  isOpen: boolean
  onClose: () => void
}

interface Settings {
  app_name: string
  app_version: string
  llm_provider: string
  theme: string
  system_prompt?: string
  available_providers: string[]
}

export default function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const { t, i18n } = useTranslation()
  const [settings, setSettings] = useState<Settings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  // Local form state
  const [provider, setProvider] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')

  useEffect(() => {
    if (isOpen) {
      loadSettings()
    }
  }, [isOpen])

  const loadSettings = async () => {
    setLoading(true)
    try {
      const data = await api.getSettings()
      setSettings(data)
      setProvider(data.llm_provider)
      setSystemPrompt(data.system_prompt || '')
    } catch (error) {
      console.error('Failed to load settings:', error)
    }
    setLoading(false)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.updateSettings({
        llm_provider: provider,
        system_prompt: systemPrompt
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (error) {
      console.error('Failed to save settings:', error)
    }
    setSaving(false)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-nv-black-200 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden border border-nv-gray-light animate-slide-up">
        {/* Header */}
        <div className="bg-nv-black px-6 py-4 border-b border-nv-gray-light flex items-center justify-between">
          <h2 className="text-lg font-semibold">{t('settings.title')}</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-nv-black-lighter rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-nv-accent" />
            </div>
          ) : (
            <>
              {/* LLM Provider */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {t('settings.llmProvider')}
                </label>
                <div className="flex gap-2">
                  {settings?.available_providers.map((p) => (
                    <button
                      key={p}
                      onClick={() => setProvider(p)}
                      className={clsx(
                        'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                        provider === p
                          ? 'bg-nv-accent text-nv-black'
                          : 'bg-nv-black-lighter text-gray-400 hover:text-white border border-nv-gray-light'
                      )}
                    >
                      {p.charAt(0).toUpperCase() + p.slice(1)}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {provider === 'ollama' && t('settings.providerOllamaPanel')}
                  {provider === 'claude' && t('settings.providerClaude')}
                  {provider === 'openai' && t('settings.providerOpenai')}
                  {provider === 'gemini' && t('settings.providerGemini')}
                  {provider === 'groq' && t('settings.providerGroq')}
                  {provider === 'openrouter' && t('settings.providerOpenrouter')}
                </p>
              </div>

              {/* System Prompt */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {t('settings.systemPrompt')}
                </label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  placeholder={t('settings.systemPromptPlaceholder')}
                  rows={4}
                  className="w-full px-4 py-3 bg-nv-black border border-nv-gray-light rounded-lg
                             text-white placeholder-gray-500 focus:outline-none focus:border-nv-accent
                             resize-none"
                />
              </div>

              {/* Language Switcher */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
                  <Globe className="w-4 h-4 text-nv-accent" />
                  {t('settings.language')}
                </label>
                <div className="flex gap-2">
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
                        'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                        i18n.language === lang.code
                          ? 'bg-nv-accent text-nv-black'
                          : 'bg-nv-black-lighter text-gray-400 hover:text-white border border-nv-gray-light'
                      )}
                    >
                      {lang.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Version Info */}
              <div className="pt-4 border-t border-nv-gray-light">
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>{t('settings.version')}</span>
                  <span className="font-mono">{settings?.app_version}</span>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-nv-black border-t border-nv-gray-light flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          >
            {t('settings.cancel')}
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="px-4 py-2 bg-nv-accent text-nv-black font-semibold rounded-lg
                       hover:bg-opacity-90 disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : saved ? (
              <Check className="w-4 h-4" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {saved ? t('settings.savedPanel') : t('settings.savePanelBtn')}
          </button>
        </div>
      </div>
    </div>
  )
}
