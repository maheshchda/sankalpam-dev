'use client'

import Link from 'next/link'
import { useAuth } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import HomeButton from './HomeButton'

const NAV_LINKS = [
  { label: 'Poojas', href: '/pooja-calendar', color: 'btn-glossy-green' },
  { label: 'Invitations', href: '/invitations', color: 'btn-glossy-purple' },
  { label: 'About Sankalpam', href: '/about-sankalpam', color: 'btn-glossy-blue' },
]

export default function SiteHeader() {
  const { user, logout } = useAuth()
  const router = useRouter()

  return (
    <header className="sacred-header">
      <div className="mx-auto max-w-7xl px-4 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-2">
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

          <div className="flex flex-wrap items-center gap-2 sm:gap-2 md:gap-3 flex-shrink-0 justify-end sm:justify-end">
            <HomeButton />
            {user ? (
              <>
                <Link href="/dashboard" className="btn-glossy btn-glossy-purple">
                  Dashboard
                </Link>
                <button
                  onClick={() => { logout(); router.push('/login') }}
                  className="btn-glossy btn-glossy-red"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link href="/login" className="btn-glossy btn-glossy-orange">
                Login
              </Link>
            )}
          </div>
        </div>

        <nav className="mt-3 flex flex-wrap items-center gap-2">
          {NAV_LINKS.map((item) => (
            <Link key={item.href} href={item.href} className={`btn-glossy ${item.color}`}>
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}
