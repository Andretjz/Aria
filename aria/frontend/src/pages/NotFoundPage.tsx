import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="text-center py-24 space-y-4">
      <p className="text-6xl font-bold text-[var(--color-primary)]">404</p>
      <h1 className="text-2xl font-semibold text-[var(--color-text)]">Page not found</h1>
      <p className="text-[var(--color-text-muted)]">
        The page you&apos;re looking for doesn&apos;t exist.
      </p>
      <Link
        to="/"
        className="inline-block mt-4 px-5 py-2 bg-[var(--color-primary)] text-white rounded-md font-medium hover:bg-[var(--color-primary-dark)] transition-colors min-h-[var(--tap-target-min)] leading-[calc(var(--tap-target-min)-4px)]"
      >
        Back to Home
      </Link>
    </div>
  )
}
