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
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host = window.location.host
  return `${protocol}://${host}/ws/v1/conversation/${sessionId}`
}
