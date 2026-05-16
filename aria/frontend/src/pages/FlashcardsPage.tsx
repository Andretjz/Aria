import { useEffect, useState } from 'react'
import { Brain } from 'lucide-react'
import type { FlashcardDue, FlashcardStats } from '../api/flashcards'
import { getDueCards, getStats, submitReview } from '../api/flashcards'

const QUALITY_LABELS: Record<number, string> = {
  0: 'Blackout',
  1: 'Wrong',
  2: 'Hard',
  3: 'OK',
  4: 'Good',
  5: 'Easy',
}

export default function FlashcardsPage() {
  const [stats, setStats] = useState<FlashcardStats | null>(null)
  const [dueCards, setDueCards] = useState<FlashcardDue[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  useEffect(() => {
    Promise.all([getStats(), getDueCards()])
      .then(([s, cards]) => {
        setStats(s)
        setDueCards(cards)
        if (cards.length === 0) setDone(true)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleReview(quality: number) {
    const current = dueCards[currentIdx]
    if (!current) return
    setSubmitting(true)
    try {
      await submitReview(current.card.id, quality)
      const next = currentIdx + 1
      if (next >= dueCards.length) {
        setDone(true)
        const s = await getStats()
        setStats(s)
      } else {
        setCurrentIdx(next)
        setFlipped(false)
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  const current = dueCards[currentIdx]

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-2">
        <Brain size={24} className="text-[var(--color-primary)]" aria-hidden />
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Flashcards</h1>
      </div>

      {stats && (
        <dl
          className="grid grid-cols-3 gap-3"
          aria-label="Flashcard statistics"
        >
          {[
            { label: 'Total', value: stats.total_cards },
            { label: 'Due Today', value: stats.cards_due },
            { label: 'Mastered', value: stats.cards_mastered },
          ].map(({ label, value }) => (
            <div
              key={label}
              className="border border-[var(--color-border)] rounded-lg p-3 text-center"
            >
              <dt className="text-xs text-[var(--color-text-muted)] uppercase tracking-wide">{label}</dt>
              <dd className="text-2xl font-bold text-[var(--color-primary)] mt-1">{value}</dd>
            </div>
          ))}
        </dl>
      )}

      {loading && (
        <div className="flex justify-center py-16" role="status" aria-label="Loading flashcards">
          <div className="w-8 h-8 border-4 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <p role="alert" className="text-sm text-[var(--color-accent)]">
          {error}
        </p>
      )}

      {!loading && !error && done && (
        <div className="text-center py-16 space-y-3">
          <p className="text-2xl">🎉</p>
          <p className="text-lg font-semibold text-[var(--color-text)]">All cards reviewed!</p>
          <p className="text-[var(--color-text-muted)] text-sm">Come back tomorrow for new cards.</p>
        </div>
      )}

      {!loading && !error && !done && current && (
        <div className="space-y-4" aria-label="Flashcard review">
          <p className="text-sm text-[var(--color-text-muted)]">
            Card {currentIdx + 1} of {dueCards.length}
          </p>

          <button
            onClick={() => setFlipped((f) => !f)}
            className="w-full min-h-[200px] border-2 border-[var(--color-border)] rounded-lg p-6 text-left hover:border-[var(--color-primary)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]"
            aria-label={flipped ? 'Card back — click to flip' : 'Card front — click to flip'}
          >
            {!flipped ? (
              <div>
                <p className="text-xs uppercase tracking-wide text-[var(--color-text-muted)] mb-2">Word</p>
                <p className="text-3xl font-bold text-[var(--color-text)]">{current.card.word}</p>
                {current.card.cefr_level && (
                  <span className="mt-2 inline-block text-xs font-mono px-2 py-0.5 rounded bg-[var(--color-surface-alt)] text-[var(--color-text-muted)]">
                    {current.card.cefr_level}
                  </span>
                )}
                <p className="mt-4 text-xs text-[var(--color-text-muted)]">Tap to reveal</p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-wide text-[var(--color-text-muted)]">Definition</p>
                <p className="text-lg text-[var(--color-text)]">
                  {current.card.definition ?? 'No definition available.'}
                </p>
                {current.card.example_sentence && (
                  <p className="text-sm italic text-[var(--color-text-muted)] border-l-2 border-[var(--color-primary)] pl-3">
                    {current.card.example_sentence}
                  </p>
                )}
              </div>
            )}
          </button>

          {flipped && (
            <div className="space-y-2" aria-label="Quality rating buttons">
              <p className="text-sm text-[var(--color-text-muted)]">How well did you know it?</p>
              <div className="flex gap-2 flex-wrap">
                {([0, 1, 2, 3, 4, 5] as const).map((q) => (
                  <button
                    key={q}
                    onClick={() => handleReview(q)}
                    disabled={submitting}
                    aria-label={`Quality ${q}: ${QUALITY_LABELS[q]}`}
                    className={`flex-1 min-w-[60px] py-2 rounded-md text-sm font-medium border disabled:opacity-50 transition-colors min-h-[var(--tap-target-min)] ${
                      q <= 2
                        ? 'border-[var(--color-accent)] text-[var(--color-accent)] hover:bg-[var(--color-accent)] hover:text-white'
                        : 'border-[var(--color-success)] text-[var(--color-success)] hover:bg-[var(--color-success)] hover:text-white'
                    }`}
                  >
                    {q} — {QUALITY_LABELS[q]}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
