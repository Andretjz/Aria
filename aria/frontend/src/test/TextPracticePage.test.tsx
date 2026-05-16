import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import TextPracticePage from '../pages/TextPracticePage'
import type { TextPracticeResult } from '../api/textPractice'

const mockResult: TextPracticeResult = {
  detected_language: 'fr',
  translated_text: 'The quick brown fox jumps over the lazy dog.',
  vocabulary: [
    { word: 'renard', cefr_level: 'A2', definition: 'fox' },
    { word: 'paresseux', cefr_level: 'B1', definition: 'lazy' },
  ],
  quiz: [
    {
      question: 'What animal is mentioned?',
      options: ['Dog', 'Cat', 'Fox', 'Bird'],
      correct: 2,
      explanation: 'A fox (renard) is explicitly mentioned.',
    },
  ],
  grammar_spotlights: [
    { rule: 'Agreement', example: 'un renard paresseux', correction: 'un renard paresseux', frequency: 1 },
  ],
}

vi.mock('../api/textPractice', () => ({
  uploadText: vi.fn(() => Promise.resolve(mockResult)),
}))

function renderPage() {
  return render(
    <MemoryRouter>
      <TextPracticePage />
    </MemoryRouter>,
  )
}

describe('TextPracticePage', () => {
  it('renders the Text Practice heading', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /text practice/i })).toBeInTheDocument()
  })

  it('renders the upload section', () => {
    renderPage()
    expect(screen.getByRole('region', { name: /upload text file/i })).toBeInTheDocument()
  })

  it('renders the file input', () => {
    renderPage()
    expect(screen.getByLabelText(/choose text file/i)).toBeInTheDocument()
  })

  it('renders the Upload button (disabled initially)', () => {
    renderPage()
    expect(screen.getByRole('button', { name: /upload and analyse/i })).toBeDisabled()
  })

  it('enables the Upload button after file selection', () => {
    renderPage()
    const input = screen.getByLabelText(/choose text file/i)
    const file = new File(['text content'], 'doc.txt', { type: 'text/plain' })
    fireEvent.change(input, { target: { files: [file] } })
    expect(screen.getByRole('button', { name: /upload and analyse/i })).not.toBeDisabled()
  })

  it('shows results after successful upload', async () => {
    renderPage()
    const input = screen.getByLabelText(/choose text file/i)
    const file = new File(['text content'], 'doc.txt', { type: 'text/plain' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /upload and analyse/i }))
    await waitFor(() =>
      expect(screen.getByRole('region', { name: /text practice results/i })).toBeInTheDocument(),
    )
  })

  it('shows the translated text', async () => {
    renderPage()
    const input = screen.getByLabelText(/choose text file/i)
    const file = new File(['text content'], 'doc.txt', { type: 'text/plain' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /upload and analyse/i }))
    await waitFor(() =>
      expect(screen.getByText(/the quick brown fox/i)).toBeInTheDocument(),
    )
  })

  it('shows the vocabulary section', async () => {
    renderPage()
    const input = screen.getByLabelText(/choose text file/i)
    const file = new File(['text content'], 'doc.txt', { type: 'text/plain' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /upload and analyse/i }))
    await waitFor(() =>
      expect(screen.getByRole('region', { name: /cefr vocabulary/i })).toBeInTheDocument(),
    )
  })

  it('shows CEFR level badges', async () => {
    renderPage()
    const input = screen.getByLabelText(/choose text file/i)
    const file = new File(['text content'], 'doc.txt', { type: 'text/plain' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /upload and analyse/i }))
    await waitFor(() => expect(screen.getByText('A2')).toBeInTheDocument())
    expect(screen.getByText('B1')).toBeInTheDocument()
  })

  it('shows quiz section', async () => {
    renderPage()
    const input = screen.getByLabelText(/choose text file/i)
    const file = new File(['text content'], 'doc.txt', { type: 'text/plain' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /upload and analyse/i }))
    await waitFor(() =>
      expect(screen.getByRole('region', { name: /comprehension quiz/i })).toBeInTheDocument(),
    )
  })
})
