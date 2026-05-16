import type { ReactNode } from 'react'
import Nav from './Nav'

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-dvh flex flex-col bg-[var(--color-surface)]">
      <Nav />
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 py-6">{children}</main>
    </div>
  )
}
