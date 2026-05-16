import { useEffect, useRef, useState } from 'react'
import { MessageSquare, Send, Mic, MicOff, StopCircle } from 'lucide-react'
import { useConversationStore, type ChatMessage } from '../stores/conversationStore'
import { createSession, buildWsUrl } from '../api/conversation'

const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'de', label: 'Deutsch' },
  { code: 'es', label: 'Español' },
  { code: 'fr', label: 'Français' },
  { code: 'it', label: 'Italiano' },
]

export default function ConversationPage() {
  const { sessionId, language, messages, status, errorMessage, setSession, addMessage, setStatus, reset } =
    useConversationStore()
  const [selectedLang, setSelectedLang] = useState('en')
  const [textInput, setTextInput] = useState('')
  const [starting, setStarting] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    return () => {
      wsRef.current?.close()
    }
  }, [])

  async function startSession() {
    setStarting(true)
    try {
      const session = await createSession(selectedLang)
      setSession(session.id, selectedLang)
      const ws = new WebSocket(buildWsUrl(session.id))
      wsRef.current = ws

      ws.onopen = () => setStatus('active')
      ws.onclose = () => setStatus('ended')
      ws.onerror = () => setStatus('error', 'Connection error')
      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data as string) as { text?: string; type?: string }
          if (data.text) {
            addMessage({
              id: crypto.randomUUID(),
              role: 'assistant',
              text: data.text,
              timestamp: Date.now(),
            })
          }
        } catch {
          // non-JSON WS frames (e.g. binary audio) ignored
        }
      }
    } catch (err) {
      setStatus('error', (err as Error).message)
    } finally {
      setStarting(false)
    }
  }

  function sendText() {
    if (!textInput.trim() || !wsRef.current) return
    const msg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      text: textInput.trim(),
      timestamp: Date.now(),
    }
    addMessage(msg)
    wsRef.current.send(JSON.stringify({ type: 'text', text: msg.text }))
    setTextInput('')
  }

  function endSession() {
    wsRef.current?.close()
    setStatus('ended')
  }

  function handleReset() {
    wsRef.current?.close()
    wsRef.current = null
    reset()
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-2">
        <MessageSquare size={24} className="text-[var(--color-primary)]" aria-hidden />
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Live Conversation</h1>
      </div>

      {status === 'idle' && (
        <section className="space-y-4 border border-[var(--color-border)] rounded-lg p-6" aria-label="Start session">
          <div>
            <label
              htmlFor="lang-select"
              className="block text-sm font-medium text-[var(--color-text)] mb-1"
            >
              Practice language
            </label>
            <select
              id="lang-select"
              value={selectedLang}
              onChange={(e) => setSelectedLang(e.target.value)}
              className="w-full px-3 py-2 border border-[var(--color-border)] rounded-md bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] min-h-[var(--tap-target-min)]"
              aria-label="Select practice language"
            >
              {SUPPORTED_LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={startSession}
            disabled={starting}
            className="w-full py-2 bg-[var(--color-primary)] text-white rounded-md font-semibold hover:bg-[var(--color-primary-dark)] disabled:opacity-50 transition-colors min-h-[var(--tap-target-min)] flex items-center justify-center gap-2"
            aria-label="Start conversation"
          >
            <Mic size={18} aria-hidden />
            {starting ? 'Starting…' : 'Start Conversation'}
          </button>
        </section>
      )}

      {status === 'connecting' && (
        <div className="flex justify-center py-8" role="status" aria-label="Connecting">
          <div className="w-8 h-8 border-4 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {(status === 'active' || status === 'ended') && (
        <section className="space-y-4" aria-label="Conversation">
          <div
            className="border border-[var(--color-border)] rounded-lg p-4 h-[400px] overflow-y-auto flex flex-col gap-3"
            aria-live="polite"
            aria-label="Chat messages"
          >
            {messages.length === 0 && (
              <p className="text-center text-[var(--color-text-muted)] text-sm mt-auto mb-auto">
                The conversation will appear here…
              </p>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] px-3 py-2 rounded-lg text-sm ${
                    msg.role === 'user'
                      ? 'bg-[var(--color-primary)] text-white'
                      : 'bg-[var(--color-surface-alt)] text-[var(--color-text)] border border-[var(--color-border)]'
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {status === 'active' && (
            <div className="flex gap-2">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendText()}
                placeholder="Type a message…"
                className="flex-1 px-3 py-2 border border-[var(--color-border)] rounded-md bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                aria-label="Message input"
              />
              <button
                onClick={sendText}
                disabled={!textInput.trim()}
                className="px-3 py-2 bg-[var(--color-primary)] text-white rounded-md hover:bg-[var(--color-primary-dark)] disabled:opacity-50 transition-colors min-h-[var(--tap-target-min)]"
                aria-label="Send message"
              >
                <Send size={18} aria-hidden />
              </button>
              <button
                onClick={endSession}
                className="px-3 py-2 border border-[var(--color-accent)] text-[var(--color-accent)] rounded-md hover:bg-red-50 transition-colors min-h-[var(--tap-target-min)]"
                aria-label="End conversation"
              >
                <StopCircle size={18} aria-hidden />
              </button>
            </div>
          )}

          {status === 'ended' && (
            <div className="text-center space-y-2">
              <p className="text-[var(--color-text-muted)] text-sm">Session ended.</p>
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-md font-medium hover:bg-[var(--color-primary-dark)] transition-colors min-h-[var(--tap-target-min)]"
              >
                New Conversation
              </button>
            </div>
          )}
        </section>
      )}

      {status === 'error' && (
        <div className="text-center space-y-3 py-8">
          <p role="alert" className="text-[var(--color-accent)]">
            {errorMessage ?? 'An error occurred.'}
          </p>
          <button
            onClick={handleReset}
            className="px-4 py-2 border border-[var(--color-border)] rounded-md text-sm hover:bg-[var(--color-surface-alt)] transition-colors min-h-[var(--tap-target-min)]"
          >
            Try again
          </button>
        </div>
      )}
    </div>
  )
}
