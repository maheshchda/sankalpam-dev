'use client'

import Link from 'next/link'
import { Home } from 'lucide-react'
import { useAuth } from '@/lib/auth'

/** Home icon button — navigates to dashboard (logged in) or / (logged out) */
interface HomeButtonProps {
  /** Use for light backgrounds (e.g. white nav) */
  variant?: 'default' | 'light'
}

export default function HomeButton({ variant = 'default' }: HomeButtonProps) {
  const { user } = useAuth()
  const href = user ? '/dashboard' : '/'

  const isLight = variant === 'light'
  const className = isLight
    ? 'inline-flex items-center justify-center min-w-[44px] min-h-[44px] rounded-2xl bg-stone-100 hover:bg-stone-200 text-stone-600 hover:text-amber-600 transition-colors touch-manipulation border border-stone-300 hover:border-amber-400/50'
    : 'inline-flex items-center justify-center min-w-[44px] min-h-[44px] rounded-2xl bg-cream-100/10 hover:bg-cream-100/20 text-cream-200 hover:text-gold-400 transition-colors touch-manipulation border border-gold-600/30 hover:border-gold-500/50'

  return (
    <Link
      href={href}
      className={className}
      aria-label="Go to home"
      title="Home"
    >
      <Home className="w-5 h-5" strokeWidth={2} />
    </Link>
  )
}
