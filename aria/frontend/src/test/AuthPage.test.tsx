import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AuthPage from '../pages/AuthPage'

vi.mock('../api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  getMe: vi.fn(),
  updatePreferences: vi.fn(),
}))

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthPage />
    </MemoryRouter>,
  )
}

describe('AuthPage', () => {
  it('renders the Account heading', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /account/i })).toBeInTheDocument()
  })

  it('renders the Sign In tab button', () => {
    renderPage()
    expect(screen.getByRole('tab', { name: /sign in/i })).toBeInTheDocument()
  })

  it('renders the Register tab button', () => {
    renderPage()
    expect(screen.getByRole('tab', { name: /register/i })).toBeInTheDocument()
  })

  it('renders the email input', () => {
    renderPage()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
  })

  it('renders the password input', () => {
    renderPage()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('renders the Sign In submit button by default', () => {
    renderPage()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('switches to Register tab when clicked', () => {
    renderPage()
    fireEvent.click(screen.getByRole('tab', { name: /register/i }))
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('shows the sign in form by default', () => {
    renderPage()
    expect(screen.getByRole('form', { name: /sign in form/i })).toBeInTheDocument()
  })

  it('shows the register form after clicking Register tab', () => {
    renderPage()
    fireEvent.click(screen.getByRole('tab', { name: /register/i }))
    expect(screen.getByRole('form', { name: /register form/i })).toBeInTheDocument()
  })
})
