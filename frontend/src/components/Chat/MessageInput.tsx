import React, { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'

interface MessageInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export default function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim())
      setInput('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-end gap-3 bg-nv-black-lighter border border-nv-gray-light rounded-xl p-3">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Nachricht eingeben... (Shift+Enter für neue Zeile)"
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent text-white placeholder-gray-500 resize-none
                     focus:outline-none disabled:opacity-50 min-h-[24px] max-h-[200px]"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !input.trim()}
          className="p-2 bg-nv-accent text-nv-black rounded-lg hover:bg-opacity-90
                     disabled:opacity-50 disabled:cursor-not-allowed transition-all
                     shadow-nv-glow"
        >
          {disabled ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
      <p className="text-xs text-gray-600 mt-2 text-center">
        Axon kann Fehler machen. Überprüfe wichtige Informationen.
      </p>
    </div>
  )
}
