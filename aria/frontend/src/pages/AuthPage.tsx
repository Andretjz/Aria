import { useState, type FormEvent } from 'react'
import { useAuthStore } from '../stores/authStore'
import { login, register, logout } from '../api/auth'
import type { ApiError } from '../api/client'

type Tab = 'login' | 'register'

export default function AuthPage() {
  const { user, setUser, setLoading, loading } = useAuthStore()
  const [tab, setTab] = useState<Tab>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      const user =
        tab === 'login' ? await login({ email, password }) : await register({ email, password })
      setUser(user)
      setSuccess(tab === 'login' ? 'Logged in successfully.' : 'Account created successfully.')
    } catch (err) {
      const msg = (err as ApiError).message ?? 'Something went wrong.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  async function handleLogout() {
    setLoading(true)
    try {
      await logout()
      setUser(null)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  if (user) {
    return (
      <div className="max-w-sm mx-auto mt-16 text-center space-y-4">
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Account</h1>
        <p className="text-[var(--color-text-muted)]">Signed in as {user.email}</p>
        <button
          onClick={handleLogout}
          disabled={loading}
          className="px-5 py-2 bg-[var(--color-accent)] text-white rounded-md font-medium hover:opacity-90 disabled:opacity-50 transition-opacity min-h-[var(--tap-target-min)]"
        >
          {loading ? 'Signing out…' : 'Sign Out'}
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-sm mx-auto mt-16 space-y-6">
      <h1 className="text-2xl font-bold text-center text-[var(--color-text)]">Account</h1>

      <div role="tablist" className="flex rounded-md border border-[var(--color-border)] overflow-hidden">
        {(['login', 'register'] as Tab[]).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            onClick={() => {
              setTab(t)
              setError(null)
              setSuccess(null)
            }}
            className={`flex-1 py-2 text-sm font-medium transition-colors min-h-[var(--tap-target-min)] capitalize ${
              tab === t
                ? 'bg-[var(--color-primary)] text-white'
                : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-alt)]'
            }`}
          >
            {t === 'login' ? 'Sign In' : 'Register'}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" aria-label={tab === 'login' ? 'Sign in form' : 'Register form'}>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-[var(--color-text)] mb-1">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border border-[var(--color-border)] rounded-md bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-[var(--color-text)] mb-1">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-[var(--color-border)] rounded-md bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <p role="alert" className="text-sm text-[var(--color-accent)]">
            {error}
          </p>
        )}
        {success && (
          <p role="status" className="text-sm text-[var(--color-success)]">
            {success}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 bg-[var(--color-primary)] text-white rounded-md font-semibold hover:bg-[var(--color-primary-dark)] disabled:opacity-50 transition-colors min-h-[var(--tap-target-min)]"
        >
          {loading ? 'Please wait…' : tab === 'login' ? 'Sign In' : 'Create Account'}
        </button>
      </form>
    </div>
  )
}
