import { useState, useEffect } from 'react'
import { Bot, Loader2 } from 'lucide-react'

interface StreamingMessageProps {
  content: string
  isStreaming: boolean
}

export default function StreamingMessage({ content, isStreaming }: StreamingMessageProps) {
  const [displayedContent, setDisplayedContent] = useState('')
  const [cursorVisible, setCursorVisible] = useState(true)

  // Cursor blink effect
  useEffect(() => {
    if (!isStreaming) {
      setCursorVisible(false)
      return
    }

    const interval = setInterval(() => {
      setCursorVisible(v => !v)
    }, 500)

    return () => clearInterval(interval)
  }, [isStreaming])

  // Update displayed content
  useEffect(() => {
    setDisplayedContent(content)
  }, [content])

  return (
    <div className="flex gap-3 animate-fade-in">
      {/* Avatar */}
      <div className="w-8 h-8 rounded-lg bg-nv-black-lighter border border-nv-gray-light flex items-center justify-center flex-shrink-0">
        {isStreaming ? (
          <Loader2 className="w-4 h-4 text-nv-accent animate-spin" />
        ) : (
          <Bot className="w-4 h-4 text-nv-accent" />
        )}
      </div>

      {/* Message Content */}
      <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-nv-black-lighter border border-nv-gray-light">
        <div className="text-sm whitespace-pre-wrap">
          {displayedContent}
          {isStreaming && cursorVisible && (
            <span className="inline-block w-2 h-4 bg-nv-accent ml-0.5 animate-pulse" />
          )}
        </div>

        {isStreaming && (
          <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>Generiere Antwort...</span>
          </div>
        )}
      </div>
    </div>
  )
}
