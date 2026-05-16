import { create } from 'zustand'

export type MessageRole = 'user' | 'assistant' | 'system'

export interface ChatMessage {
  id: string
  role: MessageRole
  text: string
  timestamp: number
}

type ConversationStatus = 'idle' | 'connecting' | 'active' | 'ended' | 'error'

interface ConversationStore {
  sessionId: string | null
  language: string
  messages: ChatMessage[]
  status: ConversationStatus
  errorMessage: string | null
  setSession: (id: string, language: string) => void
  addMessage: (msg: ChatMessage) => void
  setStatus: (status: ConversationStatus, error?: string) => void
  reset: () => void
}

export const useConversationStore = create<ConversationStore>((set) => ({
  sessionId: null,
  language: 'en',
  messages: [],
  status: 'idle',
  errorMessage: null,
  setSession: (id, language) => set({ sessionId: id, language, status: 'connecting' }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setStatus: (status, error) => set({ status, errorMessage: error ?? null }),
  reset: () => set({ sessionId: null, messages: [], status: 'idle', errorMessage: null }),
}))
