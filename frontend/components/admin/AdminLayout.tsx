'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

const NAV = [
  { href: '/admin/dashboard',   label: 'Dashboard',          icon: '▦'  },
  { href: '/admin/users',       label: 'User Management',    icon: '👥' },
  { href: '/admin/admin-users', label: 'Admin Accounts',     icon: '🛡️' },
  { href: '/admin/roles',       label: 'Roles & Permissions',icon: '🔐' },
  { href: '/admin/db',         label: 'DB Tables',         icon: '🗄️' },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [adminUsername, setAdminUsername] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    const t = localStorage.getItem('admin_token')
    const u = localStorage.getItem('admin_username')
    if (!t) { router.replace('/admin/login'); return }
    setAdminUsername(u || '')
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_username')
    router.push('/admin/login')
  }

  return (
    <div className="min-h-screen bg-cream-100 flex flex-col">
      {/* Top bar */}
      <header className="sacred-header z-30 flex-shrink-0">
        <div className="max-w-full px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              className="lg:hidden text-cream-300 hover:text-gold-400 p-1"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              ☰
            </button>
            <div className="h-9 w-9 rounded-full bg-gold-600 text-sacred-900 flex items-center justify-center text-sm font-bold shrink-0">
              PS
            </div>
            <div>
              <span className="font-cinzel font-bold text-lg text-gold-400 leading-none">Pooja Sankalpam</span>
              <span className="ml-2 text-xs bg-gold-600 text-sacred-900 rounded px-1.5 py-0.5 font-bold align-middle">ADMIN</span>
            </div>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden sm:inline text-cream-300/60">
              Signed in as <span className="text-gold-400 font-semibold">{adminUsername}</span>
            </span>
            <Link href="/" className="text-cream-300/60 hover:text-gold-400 hidden sm:inline transition-colors">Main Site</Link>
            <button onClick={handleLogout} className="bg-sacred-700 hover:bg-sacred-600 px-3 py-1.5 rounded-md text-cream-200 text-xs transition-colors">
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {sidebarOpen && (
          <div className="fixed inset-0 bg-black/50 z-20 lg:hidden" onClick={() => setSidebarOpen(false)} />
        )}

        {/* Sidebar */}
        <aside className={`
          fixed lg:static inset-y-0 left-0 z-20 w-56 bg-sacred-800 text-cream-100 flex flex-col pt-4 transition-transform duration-200 border-r border-gold-700/20
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}>
          <nav className="flex-1 px-2 space-y-1 mt-2">
            {NAV.map(item => {
              const active = pathname.startsWith(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? 'bg-gold-600 text-sacred-900 font-semibold'
                      : 'text-cream-300 hover:bg-sacred-700 hover:text-cream-50'
                  }`}
                >
                  <span className="text-base leading-none">{item.icon}</span>
                  {item.label}
                </Link>
              )
            })}
          </nav>

          <div className="px-4 py-4 border-t border-gold-700/20 text-xs text-cream-300/40">
            Pooja Sankalpam Admin v1.0
          </div>
        </aside>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6 lg:pl-6">
          {children}
        </main>
      </div>
    </div>
  )
}
