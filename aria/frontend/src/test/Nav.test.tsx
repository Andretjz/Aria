import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Nav from '../components/Nav'

function renderNav(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Nav />
    </MemoryRouter>,
  )
}

describe('Nav', () => {
  it('renders the Aria brand link', () => {
    renderNav()
    expect(screen.getByRole('link', { name: /aria home/i })).toBeInTheDocument()
  })

  it('renders the Conversation nav link', () => {
    renderNav()
    expect(screen.getByRole('link', { name: /conversation/i })).toBeInTheDocument()
  })

  it('renders the Analysis nav link', () => {
    renderNav()
    expect(screen.getByRole('link', { name: /analysis/i })).toBeInTheDocument()
  })

  it('renders the Grammar nav link', () => {
    renderNav()
    expect(screen.getByRole('link', { name: /grammar/i })).toBeInTheDocument()
  })

  it('renders the Text Practice nav link', () => {
    renderNav()
    expect(screen.getByRole('link', { name: /text practice/i })).toBeInTheDocument()
  })

  it('renders the Flashcards nav link', () => {
    renderNav()
    expect(screen.getByRole('link', { name: /flashcards/i })).toBeInTheDocument()
  })

  it('renders the Account nav link', () => {
    renderNav()
    expect(screen.getByRole('link', { name: /account/i })).toBeInTheDocument()
  })
})
