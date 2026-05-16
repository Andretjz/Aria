import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AnalysisPage from '../pages/AnalysisPage'
import type { AnalysisSession } from '../api/analysis'

const mockResult: AnalysisSession = {
  id: 'session-uuid-1',
  created_at: '2026-05-16T00:00:00Z',
  audio_filename: 'test.mp3',
  language: 'en',
  duration_seconds: 42.5,
  num_speakers: 2,
  segments: [
    { text: 'Hello world', start: 0, end: 2, speaker: 'Speaker_0', language: 'en' },
  ],
  fluency_score: 78.5,
  vocabulary: ['serendipity', 'ephemeral'],
  status: 'completed',
  quiz: [
    {
      question: 'What did they discuss?',
      options: ['Option A', 'Option B', 'Option C', 'Option D'],
      correct: 0,
      explanation: 'They discussed the main topic.',
    },
  ],
  grammar_spotlights: [
    { rule: 'Past tense', example: 'I go yesterday', correction: 'I went yesterday', frequency: 3 },
  ],
  voice_blueprints: [
    { speaker: 'Speaker_0', tempo_wpm: 120.5, filler_word_count: 4, vocabulary_richness: 0.75 },
  ],
}

vi.mock('../api/analysis', () => ({
  analyzeAudio: vi.fn(() => Promise.resolve(mockResult)),
}))

function renderPage() {
  return render(
    <MemoryRouter>
      <AnalysisPage />
    </MemoryRouter>,
  )
}

describe('AnalysisPage', () => {
  it('renders the Audio Analysis heading', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /audio analysis/i })).toBeInTheDocument()
  })

  it('renders the upload section', () => {
    renderPage()
    expect(screen.getByRole('region', { name: /upload audio/i })).toBeInTheDocument()
  })

  it('renders the file input', () => {
    renderPage()
    expect(screen.getByLabelText(/choose audio file/i)).toBeInTheDocument()
  })

  it('renders the Analyse button (disabled initially)', () => {
    renderPage()
    const btn = screen.getByRole('button', { name: /analyse audio/i })
    expect(btn).toBeDisabled()
  })

  it('enables the Analyse button after file selection', () => {
    renderPage()
    const input = screen.getByLabelText(/choose audio file/i)
    const file = new File(['audio'], 'test.mp3', { type: 'audio/mp3' })
    fireEvent.change(input, { target: { files: [file] } })
    expect(screen.getByRole('button', { name: /analyse audio/i })).not.toBeDisabled()
  })

  it('shows results after successful upload', async () => {
    renderPage()
    const input = screen.getByLabelText(/choose audio file/i)
    const file = new File(['audio'], 'test.mp3', { type: 'audio/mp3' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /analyse audio/i }))
    await waitFor(() => expect(screen.getByRole('region', { name: /analysis results/i })).toBeInTheDocument())
  })

  it('shows the transcript after upload', async () => {
    renderPage()
    const input = screen.getByLabelText(/choose audio file/i)
    const file = new File(['audio'], 'test.mp3', { type: 'audio/mp3' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /analyse audio/i }))
    await waitFor(() => expect(screen.getByText('Hello world')).toBeInTheDocument())
  })

  it('shows the vocabulary chips after upload', async () => {
    renderPage()
    const input = screen.getByLabelText(/choose audio file/i)
    const file = new File(['audio'], 'test.mp3', { type: 'audio/mp3' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /analyse audio/i }))
    await waitFor(() => expect(screen.getByText('serendipity')).toBeInTheDocument())
  })

  it('shows the quiz section after upload', async () => {
    renderPage()
    const input = screen.getByLabelText(/choose audio file/i)
    const file = new File(['audio'], 'test.mp3', { type: 'audio/mp3' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /analyse audio/i }))
    await waitFor(() =>
      expect(screen.getByRole('region', { name: /comprehension quiz/i })).toBeInTheDocument(),
    )
  })

  it('shows voice blueprints after upload', async () => {
    renderPage()
    const input = screen.getByLabelText(/choose audio file/i)
    const file = new File(['audio'], 'test.mp3', { type: 'audio/mp3' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /analyse audio/i }))
    await waitFor(() =>
      expect(screen.getByRole('region', { name: /voice blueprints/i })).toBeInTheDocument(),
    )
  })
})
