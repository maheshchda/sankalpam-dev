'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function AdminLoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Redirect if already logged in as admin
  useEffect(() => {
    const token = localStorage.getItem('admin_token')
    if (token) router.replace('/admin/dashboard')
  }, [router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const body = new URLSearchParams()
      body.append('username', username.trim())
      body.append('password', password)

      const res = await fetch(`${API}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Login failed')
        return
      }

      localStorage.setItem('admin_token', data.access_token)
      localStorage.setItem('admin_username', data.username)
      router.replace('/admin/dashboard')
    } catch {
      setError('Could not connect to the server. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-orange-600 text-white text-2xl font-bold mb-4">
            PS
          </div>
          <h1 className="text-3xl font-extrabold text-white">Pooja Sankalpam</h1>
          <p className="text-slate-400 mt-1">Admin Control Panel</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-xl font-bold text-slate-800 mb-6 text-center">Administrator Login</h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-slate-700 mb-1">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 focus:border-orange-500 focus:ring-2 focus:ring-orange-200 outline-none transition"
                placeholder="Admin username"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 focus:border-orange-500 focus:ring-2 focus:ring-orange-200 outline-none transition"
                placeholder="Admin password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-orange-600 py-3 text-white font-semibold hover:bg-orange-700 disabled:opacity-60 disabled:cursor-not-allowed transition"
            >
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            <Link href="/" className="text-orange-600 hover:underline">
              &larr; Back to main site
            </Link>
          </p>
        </div>

        <p className="mt-4 text-center text-xs text-slate-500">
          This portal is restricted to authorised administrators only.
        </p>
      </div>
    </div>
  )
}
