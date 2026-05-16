import { useRef, useState, type ChangeEvent } from 'react'
import { Mic, Upload } from 'lucide-react'
import type { AnalysisSession } from '../api/analysis'
import { analyzeAudio } from '../api/analysis'

const ACCEPTED_TYPES = '.mp3,.mp4,.wav,.m4a,.ogg,.webm,.flac'

export default function AnalysisPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisSession | null>(null)
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
      const data = await analyzeAudio(file)
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
        <Mic size={24} className="text-[var(--color-primary)]" aria-hidden />
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Audio Analysis</h1>
      </div>

      <section
        aria-label="Upload audio"
        className="border-2 border-dashed border-[var(--color-border)] rounded-lg p-8 text-center space-y-4"
      >
        <Upload size={36} className="mx-auto text-[var(--color-text-muted)]" aria-hidden />
        <p className="text-[var(--color-text-muted)] text-sm">
          Supported formats: MP3, MP4, WAV, M4A, OGG, WebM, FLAC
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_TYPES}
          onChange={handleFileChange}
          className="sr-only"
          id="audio-upload"
          aria-label="Choose audio file"
        />
        <label
          htmlFor="audio-upload"
          className="inline-block cursor-pointer px-4 py-2 border border-[var(--color-border)] rounded-md text-sm font-medium hover:bg-[var(--color-surface-alt)] transition-colors min-h-[var(--tap-target-min)] leading-[calc(var(--tap-target-min)-4px)]"
        >
          Choose file
        </label>
        {file && <p className="text-sm text-[var(--color-text)]">{file.name}</p>}
        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className="block mx-auto px-6 py-2 bg-[var(--color-primary)] text-white rounded-md font-semibold hover:bg-[var(--color-primary-dark)] disabled:opacity-50 transition-colors min-h-[var(--tap-target-min)]"
          aria-label="Analyse audio"
        >
          {loading ? 'Analysing…' : 'Analyse'}
        </button>
      </section>

      {loading && (
        <div className="flex justify-center py-8" role="status" aria-label="Analysing audio">
          <div className="w-8 h-8 border-4 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <p role="alert" className="text-sm text-[var(--color-accent)]">
          {error}
        </p>
      )}

      {result && (
        <section className="space-y-8" aria-label="Analysis results">
          <section aria-label="Summary">
            <h2 className="text-lg font-semibold mb-3 text-[var(--color-text)]">Summary</h2>
            <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Language', value: result.language },
                { label: 'Duration', value: `${result.duration_seconds.toFixed(1)}s` },
                { label: 'Speakers', value: result.num_speakers },
                {
                  label: 'Fluency',
                  value: result.fluency_score != null ? `${result.fluency_score.toFixed(1)}%` : 'N/A',
                },
              ].map(({ label, value }) => (
                <div key={label} className="border border-[var(--color-border)] rounded-lg p-3">
                  <dt className="text-xs text-[var(--color-text-muted)] uppercase tracking-wide">{label}</dt>
                  <dd className="font-semibold text-[var(--color-text)] mt-1">{value}</dd>
                </div>
              ))}
            </dl>
          </section>

          {result.segments.length > 0 && (
            <section aria-label="Transcript">
              <h2 className="text-lg font-semibold mb-3 text-[var(--color-text)]">Transcript</h2>
              <ul className="space-y-2" role="list">
                {result.segments.map((seg, i) => (
                  <li
                    key={i}
                    className="flex gap-3 text-sm border-b border-[var(--color-border)] pb-2"
                  >
                    <span className="font-mono text-[var(--color-primary)] shrink-0 w-16">
                      {seg.speaker}
                    </span>
                    <span className="text-[var(--color-text)]">{seg.text}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {result.vocabulary.length > 0 && (
            <section aria-label="Vocabulary">
              <h2 className="text-lg font-semibold mb-3 text-[var(--color-text)]">Vocabulary</h2>
              <div className="flex flex-wrap gap-2">
                {result.vocabulary.map((word) => (
                  <span
                    key={word}
                    className="px-2 py-1 bg-[var(--color-surface-alt)] rounded text-sm font-mono text-[var(--color-text)]"
                  >
                    {word}
                  </span>
                ))}
              </div>
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
                    <p className="text-xs text-[var(--color-text-muted)] mt-1">
                      Frequency: {g.frequency}
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {result.voice_blueprints.length > 0 && (
            <section aria-label="Voice blueprints">
              <h2 className="text-lg font-semibold mb-3 text-[var(--color-text)]">
                Voice Blueprints
              </h2>
              <ul className="space-y-3" role="list">
                {result.voice_blueprints.map((vb, i) => (
                  <li key={i} className="border border-[var(--color-border)] rounded-lg p-4">
                    <p className="font-semibold text-[var(--color-primary)] mb-2">{vb.speaker}</p>
                    <dl className="grid grid-cols-3 gap-2 text-center text-sm">
                      <div>
                        <dt className="text-xs text-[var(--color-text-muted)]">Tempo (WPM)</dt>
                        <dd className="font-semibold">{vb.tempo_wpm.toFixed(0)}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-[var(--color-text-muted)]">Filler words</dt>
                        <dd className="font-semibold">{vb.filler_word_count}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-[var(--color-text-muted)]">Vocab richness</dt>
                        <dd className="font-semibold">{(vb.vocabulary_richness * 100).toFixed(0)}%</dd>
                      </div>
                    </dl>
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
