'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { toast } from 'react-toastify'
import Link from 'next/link'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [mounted, setMounted] = useState(false)
  const { login } = useAuth()
  const router = useRouter()

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const loggedInUser = await login(username, password)
      toast.success('Login successful!')
      if (loggedInUser?.is_admin) {
        router.push('/admin')
      } else {
        router.push('/dashboard')
      }
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || 'Login failed'
      const isNetwork = !error.response && (error.message === 'Network Error' || error.code === 'ERR_NETWORK')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      toast.error(isNetwork ? `Cannot reach server. Is the backend running at ${apiUrl}? Check browser console (F12) for CORS or network errors.` : msg)
    } finally {
      setLoading(false)
    }
  }

  if (!mounted) {
    return (
      <div className="page-bg flex items-center justify-center">
        <p className="font-cinzel text-sacred-700 text-xl">Loading...</p>
      </div>
    )
  }

  return (
    <div className="page-bg flex flex-col items-center justify-center py-16 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 rounded-full bg-sacred-800 flex items-center justify-center mb-4">
            <span className="font-cinzel text-gold-400 font-bold text-lg">PS</span>
          </div>
          <h2 className="font-cinzel text-3xl font-bold text-sacred-800">
            Sign In
          </h2>
          <p className="text-stone-500 mt-2">Welcome back to Pooja Sankalpam</p>
        </div>

        <div className="sacred-card p-8">
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-sacred-700 mb-1">
                Username or Email
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                autoComplete="username"
                suppressHydrationWarning
                className="sacred-input"
                placeholder="Username or email"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-sacred-700 mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  suppressHydrationWarning
                  className="sacred-input pr-10"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-stone-400 hover:text-gold-600 focus:outline-none z-20"
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer select-none text-sm text-stone-600">
                <input
                  type="checkbox"
                  checked={showPassword}
                  onChange={e => setShowPassword(e.target.checked)}
                  className="h-4 w-4 rounded border-cream-300 accent-gold-600"
                />
                Show password
              </label>
              <Link href="/forgot-password" className="gold-link text-sm">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              suppressHydrationWarning
              className="gold-btn w-full py-2.5"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>

            <div className="text-center">
              <Link href="/register" className="gold-link text-sm">
                Don&apos;t have an account? Register here
              </Link>
            </div>
            <p className="text-xs text-stone-400 text-center">
              API: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
