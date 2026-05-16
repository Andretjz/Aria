import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import GrammarPage from '../pages/GrammarPage'
import type { GrammarDeficit } from '../api/grammar'
import { getDeficits } from '../api/grammar'

const mockDeficits: GrammarDeficit[] = [
  { rule: 'Subject-verb agreement', total_frequency: 12, example: 'She go to school.' },
  { rule: 'Article usage', total_frequency: 8, example: null },
]

vi.mock('../api/grammar', () => ({
  getDeficits: vi.fn(() => Promise.resolve(mockDeficits)),
}))

function renderPage() {
  return render(
    <MemoryRouter>
      <GrammarPage />
    </MemoryRouter>,
  )
}

describe('GrammarPage', () => {
  it('renders the Grammar Deficits heading', async () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /grammar deficits/i })).toBeInTheDocument()
  })

  it('shows loading spinner initially', () => {
    renderPage()
    expect(screen.getByRole('status', { name: /loading grammar/i })).toBeInTheDocument()
  })

  it('renders the first deficit rule after loading', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('Subject-verb agreement')).toBeInTheDocument())
  })

  it('renders the second deficit rule', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('Article usage')).toBeInTheDocument())
  })

  it('renders the frequency badge', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('×12')).toBeInTheDocument())
  })

  it('renders the example for the first deficit', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText(/she go to school/i)).toBeInTheDocument())
  })

  it('renders the deficit list', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByRole('list', { name: /grammar deficit list/i })).toBeInTheDocument())
  })
})

describe('GrammarPage — empty state', () => {
  beforeEach(() => {
    vi.mocked(getDeficits).mockResolvedValueOnce([])
  })

  it('shows empty state message when no deficits', async () => {
    renderPage()
    await waitFor(() =>
      expect(screen.getByRole('region', { name: /no grammar data/i })).toBeInTheDocument(),
    )
  })
})
