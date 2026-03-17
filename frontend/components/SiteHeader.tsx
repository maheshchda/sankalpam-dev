'use client'

import Link from 'next/link'
import { useAuth } from '@/lib/auth'
import { useRouter } from 'next/navigation'

const NAV_LINKS = [
  { label: 'Poojas', href: '/pooja-calendar' },
  { label: 'Invitations', href: '/invitations' },
  { label: 'About Sankalpam', href: '/about-sankalpam' },
]

export default function SiteHeader() {
  const { user, logout } = useAuth()
  const router = useRouter()

  return (
    <header className="sacred-header">
      <div className="mx-auto max-w-7xl px-4 py-4">
        <div className="flex items-center justify-between gap-2 flex-wrap sm:flex-nowrap">
          <Link href={user ? '/dashboard' : '/'} className="flex items-center gap-2 sm:gap-3 group min-w-0 shrink">
            <div className="h-11 w-11 rounded-full bg-gold-600 text-sacred-900 font-bold flex items-center justify-center text-sm shrink-0 group-hover:bg-gold-400 transition-colors">
              PS
            </div>
            <div className="min-w-0">
              <h1 className="text-lg sm:text-xl md:text-2xl font-cinzel font-bold text-gold-400 leading-tight tracking-wide truncate">
                Pooja Sankalpam
              </h1>
              <p className="text-xs text-cream-300/70 hidden md:block">Your personal assistant for Poojas</p>
            </div>
          </Link>

          <div className="flex items-center gap-1.5 sm:gap-2 md:gap-3 flex-shrink-0 flex-wrap justify-end">
            {user ? (
              <>
                <span className="hidden sm:inline text-cream-300/70 text-sm">
                  Welcome, <span className="text-gold-400 font-medium">{user.first_name}</span>
                </span>
                <Link href="/dashboard" className="sacred-pill text-cream-200 border-gold-600/40 hover:text-gold-400">
                  Dashboard
                </Link>
                <button
                  onClick={() => { logout(); router.push('/login') }}
                  className="rounded-md border border-gold-600/40 px-3 py-1.5 text-sm text-cream-300 hover:bg-sacred-700 transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link href="/login" className="gold-btn text-sm px-4 py-2">
                Login
              </Link>
            )}
          </div>
        </div>

        <nav className="mt-3 flex flex-wrap items-center gap-2">
          {NAV_LINKS.map((item) => (
            <Link key={item.href} href={item.href} className="sacred-pill">
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}
