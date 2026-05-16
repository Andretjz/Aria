import { useEffect, useState } from 'react'
import { BookOpen } from 'lucide-react'
import type { GrammarDeficit } from '../api/grammar'
import { getDeficits } from '../api/grammar'

export default function GrammarPage() {
  const [deficits, setDeficits] = useState<GrammarDeficit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDeficits()
      .then(setDeficits)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-2">
        <BookOpen size={24} className="text-[var(--color-primary)]" aria-hidden />
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Grammar Deficits</h1>
      </div>

      <p className="text-sm text-[var(--color-text-muted)]">
        Your top grammar errors aggregated across all analysis sessions.
      </p>

      {loading && (
        <div className="flex justify-center py-16" role="status" aria-label="Loading grammar deficits">
          <div className="w-8 h-8 border-4 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <p role="alert" className="text-sm text-[var(--color-accent)]">
          {error}
        </p>
      )}

      {!loading && !error && deficits.length === 0 && (
        <section className="text-center py-16 space-y-2" aria-label="No grammar data">
          <p className="text-[var(--color-text-muted)]">No grammar data yet.</p>
          <p className="text-sm text-[var(--color-text-muted)]">
            Upload an audio recording in the Analysis module to get started.
          </p>
        </section>
      )}

      {!loading && !error && deficits.length > 0 && (
        <ol className="space-y-3" role="list" aria-label="Grammar deficit list">
          {deficits.map((deficit, i) => (
            <li
              key={i}
              className="border border-[var(--color-border)] rounded-lg p-4 flex gap-4 items-start"
            >
              <span className="text-2xl font-bold text-[var(--color-primary)] shrink-0 w-8 text-center">
                {i + 1}
              </span>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-[var(--color-text)]">{deficit.rule}</p>
                {deficit.example && (
                  <p className="text-sm text-[var(--color-text-muted)] mt-1 italic">
                    &ldquo;{deficit.example}&rdquo;
                  </p>
                )}
              </div>
              <span className="shrink-0 text-sm font-mono px-2 py-1 rounded bg-[var(--color-surface-alt)] text-[var(--color-text-muted)]">
                ×{deficit.total_frequency}
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
