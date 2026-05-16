import { NavLink } from 'react-router-dom'
import {
  Home,
  MessageSquare,
  BarChart2,
  BookOpen,
  FileText,
  Brain,
  LogIn,
} from 'lucide-react'
import { clsx } from 'clsx'

const links = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/conversation', label: 'Conversation', icon: MessageSquare },
  { to: '/analysis', label: 'Analysis', icon: BarChart2 },
  { to: '/grammar', label: 'Grammar', icon: BookOpen },
  { to: '/text-practice', label: 'Text Practice', icon: FileText },
  { to: '/flashcards', label: 'Flashcards', icon: Brain },
  { to: '/auth', label: 'Account', icon: LogIn },
]

export default function Nav() {
  return (
    <header className="sticky top-0 z-50 bg-[var(--color-surface)] border-b border-[var(--color-border)]">
      <nav
        className="max-w-7xl mx-auto px-4 h-14 flex items-center gap-1"
        aria-label="Main navigation"
      >
        <NavLink
          to="/"
          className="mr-4 font-bold text-lg text-[var(--color-primary)] tracking-tight"
          aria-label="Aria home"
        >
          Aria
        </NavLink>

        <ul className="flex items-center gap-1 overflow-x-auto" role="list">
          {links.map(({ to, label, icon: Icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors min-h-[var(--tap-target-min)]',
                    isActive
                      ? 'bg-[var(--color-primary)] text-white'
                      : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-alt)]',
                  )
                }
                aria-label={label}
              >
                <Icon size={16} aria-hidden />
                <span className="hidden sm:inline">{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  )
}
