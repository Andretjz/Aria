import { useRef, useState, type ChangeEvent } from 'react'
import { FileText, Upload } from 'lucide-react'
import type { TextPracticeResult } from '../api/textPractice'
import { uploadText } from '../api/textPractice'

const ACCEPTED_TYPES = '.pdf,.txt,.docx'
const CEFR_COLOURS: Record<string, string> = {
  A1: 'bg-green-100 text-green-800',
  A2: 'bg-green-200 text-green-900',
  B1: 'bg-yellow-100 text-yellow-800',
  B2: 'bg-yellow-200 text-yellow-900',
  C1: 'bg-orange-100 text-orange-800',
  C2: 'bg-red-100 text-red-800',
}

export default function TextPracticePage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TextPracticeResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [quizAnswer, setQuizAnswer] = useState<Record<number, number>>({})
  const [quizChecked, setQuizChecked] = useState<Record<number, boolean>>({})

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    setFile(e.target.files?.[0] ?? null)
    setResult(null)
    setError(null)
  }

  async function handleUpload() {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const data = await uploadText(file)
      setResult(data)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      <div className="flex items-center gap-2">
        <FileText size={24} className="text-[var(--color-primary)]" aria-hidden />
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Text Practice</h1>
      </div>

      <section
        aria-label="Upload text file"
        className="border-2 border-dashed border-[var(--color-border)] rounded-lg p-8 text-center space-y-4"
      >
        <Upload size={36} className="mx-auto text-[var(--color-text-muted)]" aria-hidden />
        <p className="text-[var(--color-text-muted)] text-sm">
          Supported formats: PDF, TXT, DOCX
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_TYPES}
          onChange={handleFileChange}
          className="sr-only"
          id="text-upload"
          aria-label="Choose text file"
        />
        <label
          htmlFor="text-upload"
          className="inline-block cursor-pointer px-4 py-2 border border-[var(--color-border)] rounded-md text-sm font-medium hover:bg-[var(--color-surface-alt)] transition-colors min-h-[var(--tap-target-min)] leading-[calc(var(--tap-target-min)-4px)]"
        >
          Choose file
        </label>
        {file && <p className="text-sm text-[var(--color-text)]">{file.name}</p>}
        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className="block mx-auto px-6 py-2 bg-[var(--color-primary)] text-white rounded-md font-semibold hover:bg-[var(--color-primary-dark)] disabled:opacity-50 transition-colors min-h-[var(--tap-target-min)]"
          aria-label="Upload and analyse"
        >
          {loading ? 'Analysing…' : 'Upload & Analyse'}
        </button>
      </section>

      {loading && (
        <div className="flex justify-center py-8" role="status" aria-label="Analysing text">
          <div className="w-8 h-8 border-4 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <p role="alert" className="text-sm text-[var(--color-accent)]">
          {error}
        </p>
      )}

      {result && (
        <section className="space-y-8" aria-label="Text practice results">
          <section aria-label="Translation">
            <h2 className="text-lg font-semibold mb-2 text-[var(--color-text)]">
              Translation{' '}
              <span className="text-sm font-mono text-[var(--color-text-muted)]">
                ({result.detected_language})
              </span>
            </h2>
            <p className="text-sm text-[var(--color-text)] bg-[var(--color-surface-alt)] p-4 rounded-lg border border-[var(--color-border)] whitespace-pre-wrap">
              {result.translated_text}
            </p>
          </section>

          {result.vocabulary.length > 0 && (
            <section aria-label="CEFR vocabulary">
              <h2 className="text-lg font-semibold mb-3 text-[var(--color-text)]">Vocabulary</h2>
              <ul className="space-y-2" role="list">
                {result.vocabulary.map((item, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-3 border border-[var(--color-border)] rounded-lg p-3"
                  >
                    <span
                      className={`shrink-0 text-xs font-bold px-1.5 py-0.5 rounded ${CEFR_COLOURS[item.cefr_level] ?? 'bg-gray-100 text-gray-700'}`}
                    >
                      {item.cefr_level}
                    </span>
                    <div>
                      <p className="font-medium text-[var(--color-text)]">{item.word}</p>
                      <p className="text-sm text-[var(--color-text-muted)]">{item.definition}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {result.quiz.length > 0 && (
            <section aria-label="Comprehension quiz">
              <h2 className="text-lg font-semibold mb-3 text-[var(--color-text)]">
                Comprehension Quiz
              </h2>
              <ol className="space-y-6" role="list">
                {result.quiz.map((q, qi) => (
                  <li key={qi} className="space-y-2">
                    <p className="font-medium text-[var(--color-text)]">
                      {qi + 1}. {q.question}
                    </p>
                    <ul className="space-y-1" role="list">
                      {q.options.map((opt, oi) => {
                        const selected = quizAnswer[qi] === oi
                        const checked = quizChecked[qi]
                        const correct = oi === q.correct
                        return (
                          <li key={oi}>
                            <button
                              onClick={() => {
                                if (!checked) setQuizAnswer((a) => ({ ...a, [qi]: oi }))
                              }}
                              className={`w-full text-left px-3 py-2 rounded-md text-sm border transition-colors min-h-[var(--tap-target-min)] ${
                                checked
                                  ? correct
                                    ? 'border-[var(--color-success)] bg-green-50 text-green-700'
                                    : selected
                                      ? 'border-[var(--color-accent)] bg-red-50 text-red-700'
                                      : 'border-[var(--color-border)]'
                                  : selected
                                    ? 'border-[var(--color-primary)] bg-[var(--color-surface-alt)]'
                                    : 'border-[var(--color-border)] hover:bg-[var(--color-surface-alt)]'
                              }`}
                              aria-pressed={selected}
                            >
                              {opt}
                            </button>
                          </li>
                        )
                      })}
                    </ul>
                    {!quizChecked[qi] && quizAnswer[qi] !== undefined && (
                      <button
                        onClick={() => setQuizChecked((c) => ({ ...c, [qi]: true }))}
                        className="text-xs text-[var(--color-primary)] underline"
                      >
                        Check answer
                      </button>
                    )}
                    {quizChecked[qi] && (
                      <p className="text-xs text-[var(--color-text-muted)]">{q.explanation}</p>
                    )}
                  </li>
                ))}
              </ol>
            </section>
          )}

          {result.grammar_spotlights.length > 0 && (
            <section aria-label="Grammar spotlights">
              <h2 className="text-lg font-semibold mb-3 text-[var(--color-text)]">
                Grammar Spotlights
              </h2>
              <ul className="space-y-3" role="list">
                {result.grammar_spotlights.map((g, i) => (
                  <li key={i} className="border border-[var(--color-border)] rounded-lg p-4">
                    <p className="font-medium text-[var(--color-text)]">{g.rule}</p>
                    <p className="text-sm text-[var(--color-text-muted)] mt-1">
                      <span className="line-through mr-2">{g.example}</span>→{' '}
                      <span className="text-[var(--color-success)]">{g.correction}</span>
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </section>
      )}
    </div>
  )
}
