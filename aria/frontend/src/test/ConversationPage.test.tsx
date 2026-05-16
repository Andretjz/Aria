import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ConversationPage from '../pages/ConversationPage'

vi.mock('../api/conversation', () => ({
  createSession: vi.fn(() =>
    Promise.resolve({
      id: 'session-uuid-1',
      created_at: '2026-05-16T00:00:00Z',
      language: 'en',
      status: 'active',
      turn_count: 0,
      ended_at: null,
    }),
  ),
  buildWsUrl: vi.fn(() => 'ws://localhost:8000/ws/v1/conversation/session-uuid-1'),
}))

// Prevent real WebSocket connections in tests
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onerror: ((e: Event) => void) | null = null
  onmessage: ((e: MessageEvent) => void) | null = null
  send = vi.fn()
  close = vi.fn()
}

Object.defineProperty(global, 'WebSocket', { value: MockWebSocket, writable: true })

function renderPage() {
  return render(
    <MemoryRouter>
      <ConversationPage />
    </MemoryRouter>,
  )
}

describe('ConversationPage', () => {
  it('renders the Live Conversation heading', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /live conversation/i })).toBeInTheDocument()
  })

  it('renders the language selector', () => {
    renderPage()
    expect(screen.getByRole('combobox', { name: /select practice language/i })).toBeInTheDocument()
  })

  it('renders English as the default language option', () => {
    renderPage()
    const select = screen.getByRole('combobox', { name: /select practice language/i })
    expect(select).toHaveValue('en')
  })

  it('renders all five supported language options', () => {
    renderPage()
    expect(screen.getByRole('option', { name: /english/i })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /deutsch/i })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /español/i })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /français/i })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /italiano/i })).toBeInTheDocument()
  })

  it('renders the Start Conversation button', () => {
    renderPage()
    expect(screen.getByRole('button', { name: /start conversation/i })).toBeInTheDocument()
  })

  it('renders the session setup section', () => {
    renderPage()
    expect(screen.getByRole('region', { name: /start session/i })).toBeInTheDocument()
  })
})
