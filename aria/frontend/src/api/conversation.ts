import { apiFetch } from './client'

export interface ConversationSession {
  id: string
  created_at: string
  language: string
  status: string
  turn_count: number
  ended_at: string | null
}

export function createSession(language: string): Promise<ConversationSession> {
  return apiFetch('/v1/conversations/', {
    method: 'POST',
    body: JSON.stringify({ language }),
  })
}

export function buildWsUrl(sessionId: string): string {
  // In production (Vercel), WebSocket can't be proxied — use the Fly.io backend directly.
  // Set VITE_WS_URL=wss://aria-backend.fly.dev in Vercel project settings.
  const wsBase = import.meta.env.VITE_WS_URL as string | undefined
  if (wsBase) {
    return `${wsBase.replace(/\/$/, '')}/ws/v1/conversation/${sessionId}`
  }
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host = window.location.host
  return `${protocol}://${host}/ws/v1/conversation/${sessionId}`
}
