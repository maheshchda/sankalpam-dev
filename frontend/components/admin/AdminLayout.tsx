'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

const NAV = [
  { href: '/admin/dashboard',   label: 'Dashboard',          icon: '▦'  },
  { href: '/admin/users',       label: 'User Management',    icon: '👥' },
  { href: '/admin/admin-users', label: 'Admin Accounts',     icon: '🛡️' },
  { href: '/admin/roles',       label: 'Roles & Permissions',icon: '🔐' },
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
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top bar */}
      <header className="bg-slate-900 text-white shadow-md z-30 flex-shrink-0">
        <div className="max-w-full px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Hamburger for mobile */}
            <button
              className="lg:hidden text-slate-300 hover:text-white p-1"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              ☰
            </button>
            <div className="h-9 w-9 rounded-full bg-orange-600 flex items-center justify-center text-sm font-bold shrink-0">
              PS
            </div>
            <div>
              <span className="font-bold text-lg leading-none">Pooja Sankalpam</span>
              <span className="ml-2 text-xs bg-orange-600 rounded px-1.5 py-0.5 font-semibold align-middle">ADMIN</span>
            </div>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden sm:inline text-slate-400">
              Signed in as <span className="text-white font-semibold">{adminUsername}</span>
            </span>
            <Link href="/" className="text-slate-400 hover:text-white hidden sm:inline">Main Site</Link>
            <button onClick={handleLogout} className="bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-md text-slate-200 text-xs">
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar overlay for mobile */}
        {sidebarOpen && (
          <div className="fixed inset-0 bg-black/50 z-20 lg:hidden" onClick={() => setSidebarOpen(false)} />
        )}

        {/* Sidebar */}
        <aside className={`
          fixed lg:static inset-y-0 left-0 z-20 w-56 bg-slate-800 text-white flex flex-col pt-4 transition-transform duration-200
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
                      ? 'bg-orange-600 text-white'
                      : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  <span className="text-base leading-none">{item.icon}</span>
                  {item.label}
                </Link>
              )
            })}
          </nav>

          <div className="px-4 py-4 border-t border-slate-700 text-xs text-slate-500">
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
