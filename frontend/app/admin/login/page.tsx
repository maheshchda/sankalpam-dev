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
    <div className="min-h-screen bg-sacred-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 rounded-full bg-gold-600 text-sacred-900 font-bold flex items-center justify-center text-lg mb-4">
            PS
          </div>
          <h1 className="font-cinzel text-3xl font-bold text-gold-400">Pooja Sankalpam</h1>
          <p className="text-cream-300/60 mt-1">Admin Control Panel</p>
        </div>

        <div className="sacred-card p-8">
          <h2 className="font-cinzel text-xl font-bold text-sacred-800 mb-6 text-center">Administrator Login</h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-sacred-700 mb-1">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                className="w-full rounded-lg border border-cream-300 px-4 py-2.5 text-stone-900 bg-white focus:border-gold-500 focus:ring-2 focus:ring-gold-200 outline-none transition"
                placeholder="Admin username"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-sacred-700 mb-1">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="w-full rounded-lg border border-cream-300 px-4 py-2.5 text-stone-900 bg-white focus:border-gold-500 focus:ring-2 focus:ring-gold-200 outline-none transition"
                placeholder="Admin password"
              />
            </div>

            <button type="submit" disabled={loading} className="gold-btn w-full py-3">
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-stone-500">
            <Link href="/" className="gold-link">&larr; Back to main site</Link>
          </p>
        </div>

        <p className="mt-4 text-center text-xs text-cream-300/40">
          This portal is restricted to authorised administrators only.
        </p>
      </div>
    </div>
  )
}
