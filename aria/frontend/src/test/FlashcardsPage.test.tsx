import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import FlashcardsPage from '../pages/FlashcardsPage'
import type { FlashcardDue, FlashcardStats } from '../api/flashcards'

const mockStats: FlashcardStats = {
  total_cards: 10,
  cards_due: 3,
  cards_mastered: 2,
}

const mockDue: FlashcardDue[] = [
  {
    card: {
      id: 'card-uuid-1',
      deck_id: 'deck-uuid-1',
      word: 'Serendipity',
      cefr_level: 'C1',
      definition: 'The occurrence of finding something good by chance.',
      example_sentence: 'It was pure serendipity that they met.',
      created_at: '2026-05-16T00:00:00Z',
    },
    review: {
      id: 'review-uuid-1',
      flashcard_id: 'card-uuid-1',
      ease_factor: 2.5,
      interval: 1,
      repetitions: 0,
      next_review: '2026-05-16',
      last_reviewed: null,
    },
  },
]

vi.mock('../api/flashcards', () => ({
  getStats: vi.fn(() => Promise.resolve(mockStats)),
  getDueCards: vi.fn(() => Promise.resolve(mockDue)),
  submitReview: vi.fn(() =>
    Promise.resolve({
      id: 'review-uuid-1',
      flashcard_id: 'card-uuid-1',
      ease_factor: 2.6,
      interval: 6,
      repetitions: 1,
      next_review: '2026-05-22',
      last_reviewed: '2026-05-16',
    }),
  ),
}))

function renderPage() {
  return render(
    <MemoryRouter>
      <FlashcardsPage />
    </MemoryRouter>,
  )
}

describe('FlashcardsPage', () => {
  it('renders the Flashcards heading', async () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /flashcards/i })).toBeInTheDocument()
  })

  it('shows a loading spinner initially', () => {
    renderPage()
    expect(screen.getByRole('status', { name: /loading flashcards/i })).toBeInTheDocument()
  })

  it('renders the stats section after loading', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('Total')).toBeInTheDocument())
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('renders the due card word after loading', async () => {
    renderPage()
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument())
    expect(screen.getByText('Serendipity')).toBeInTheDocument()
  })

  it('renders the CEFR badge on the card', async () => {
    renderPage()
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument())
    expect(screen.getByText('C1')).toBeInTheDocument()
  })

  it('shows card 1 of N progress', async () => {
    renderPage()
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument())
    expect(screen.getByText(/card 1 of/i)).toBeInTheDocument()
  })

  it('reveals quality rating buttons after flipping the card', async () => {
    renderPage()
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument())
    const cardButton = screen.getByRole('button', { name: /card front/i })
    fireEvent.click(cardButton)
    await waitFor(() => expect(screen.getByText(/how well did you know it/i)).toBeInTheDocument())
    expect(screen.getByRole('button', { name: /quality 0/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /quality 5/i })).toBeInTheDocument()
  })

  it('renders the flashcard statistics dl', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('Total')).toBeInTheDocument())
    expect(screen.getByText('Due Today')).toBeInTheDocument()
    expect(screen.getByText('Mastered')).toBeInTheDocument()
  })
})
