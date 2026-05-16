import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import HomePage from '../pages/HomePage'

function renderPage() {
  return render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  )
}

describe('HomePage', () => {
  it('renders the main heading with Aria', () => {
    renderPage()
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/aria/i)
  })

  it('renders the Start Conversation CTA link', () => {
    renderPage()
    expect(screen.getByRole('link', { name: /start conversation/i })).toBeInTheDocument()
  })

  it('renders the Sign In link', () => {
    renderPage()
    expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument()
  })

  it('renders the modules section heading', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /modules/i })).toBeInTheDocument()
  })

  it('renders the module cards list', () => {
    renderPage()
    expect(screen.getByRole('list', { name: /module cards/i })).toBeInTheDocument()
  })

  it('renders the Live Conversation module card', () => {
    renderPage()
    expect(screen.getByRole('link', { name: /live conversation/i })).toBeInTheDocument()
  })

  it('renders the Flashcards module card', () => {
    renderPage()
    expect(screen.getByRole('link', { name: /flashcards/i })).toBeInTheDocument()
  })

  it('renders the Grammar module card', () => {
    renderPage()
    expect(screen.getByRole('link', { name: /grammar/i })).toBeInTheDocument()
  })

  it('renders the Text Practice module card', () => {
    renderPage()
    expect(screen.getByRole('link', { name: /text practice/i })).toBeInTheDocument()
  })
})
