import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'

describe('App routing', () => {
  it('renders home page at /', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByText(/HomePage/i)).toBeInTheDocument()
  })

  it('renders 404 page for unknown routes', () => {
    render(
      <MemoryRouter initialEntries={['/nonexistent']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByText(/NotFoundPage/i)).toBeInTheDocument()
  })
})
