import { Link } from 'react-router-dom'
import { MessageSquare, BarChart2, BookOpen, FileText, Brain, Mic } from 'lucide-react'

const modules = [
  {
    to: '/conversation',
    icon: MessageSquare,
    label: 'Live Conversation',
    description: 'Practice speaking with an AI tutor in real-time.',
    color: 'text-purple-500',
    bg: 'bg-purple-50 dark:bg-purple-900/20',
  },
  {
    to: '/analysis',
    icon: Mic,
    label: 'Audio Analysis',
    description: 'Upload a recording for fluency, vocabulary, and speaker analysis.',
    color: 'text-blue-500',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
  },
  {
    to: '/grammar',
    icon: BookOpen,
    label: 'Grammar',
    description: 'See your top grammar errors aggregated across all sessions.',
    color: 'text-green-500',
    bg: 'bg-green-50 dark:bg-green-900/20',
  },
  {
    to: '/text-practice',
    icon: FileText,
    label: 'Text Practice',
    description: 'Upload a PDF, TXT, or DOCX to translate, quiz, and analyse vocabulary.',
    color: 'text-orange-500',
    bg: 'bg-orange-50 dark:bg-orange-900/20',
  },
  {
    to: '/flashcards',
    icon: Brain,
    label: 'Flashcards',
    description: 'Review your vocabulary with SM-2 spaced repetition.',
    color: 'text-pink-500',
    bg: 'bg-pink-50 dark:bg-pink-900/20',
  },
  {
    to: '/analysis',
    icon: BarChart2,
    label: 'Session History',
    description: 'Review past analysis sessions and track your progress over time.',
    color: 'text-cyan-500',
    bg: 'bg-cyan-50 dark:bg-cyan-900/20',
  },
]

export default function HomePage() {
  return (
    <div className="space-y-10">
      <section className="text-center py-10 space-y-3">
        <h1 className="text-4xl font-bold text-[var(--color-text)]">
          Welcome to <span className="text-[var(--color-primary)]">Aria</span>
        </h1>
        <p className="text-lg text-[var(--color-text-muted)] max-w-xl mx-auto">
          Your conversational language learning platform. Practice speaking, analyse your sessions,
          and master vocabulary — all in one place.
        </p>
        <div className="flex justify-center gap-3 pt-2">
          <Link
            to="/conversation"
            className="px-5 py-2.5 bg-[var(--color-primary)] text-white rounded-md font-semibold hover:bg-[var(--color-primary-dark)] transition-colors min-h-[var(--tap-target-min)] flex items-center"
          >
            Start Conversation
          </Link>
          <Link
            to="/auth"
            className="px-5 py-2.5 border border-[var(--color-border)] text-[var(--color-text)] rounded-md font-semibold hover:bg-[var(--color-surface-alt)] transition-colors min-h-[var(--tap-target-min)] flex items-center"
          >
            Sign In
          </Link>
        </div>
      </section>

      <section aria-label="Modules">
        <h2 className="text-xl font-semibold mb-4 text-[var(--color-text)]">Modules</h2>
        <ul
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
          role="list"
          aria-label="Module cards"
        >
          {modules.map(({ to, icon: Icon, label, description, color, bg }) => (
            <li key={label}>
              <Link
                to={to}
                className="block p-5 border border-[var(--color-border)] rounded-lg hover:border-[var(--color-primary)] hover:shadow-sm transition-all group"
                aria-label={label}
              >
                <div className={`inline-flex p-2 rounded-md mb-3 ${bg}`}>
                  <Icon size={22} className={color} aria-hidden />
                </div>
                <h3 className="font-semibold text-[var(--color-text)] group-hover:text-[var(--color-primary)] transition-colors">
                  {label}
                </h3>
                <p className="text-sm text-[var(--color-text-muted)] mt-1">{description}</p>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
