'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'react-toastify'
import Link from 'next/link'
import api from '@/lib/api'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [resetToken, setResetToken] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await api.post('/api/auth/forgot-password', { email })
      toast.success(response.data.message || 'Password reset instructions sent!')
      if (response.data.reset_token) {
        setResetToken(response.data.reset_token)
      }
      setSubmitted(true)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to send reset email')
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

  const Card = ({ children }: { children: React.ReactNode }) => (
    <div className="page-bg flex flex-col items-center justify-center py-16 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="mx-auto h-14 w-14 rounded-full bg-sacred-800 flex items-center justify-center mb-3">
            <span className="font-cinzel text-gold-400 font-bold">PS</span>
          </div>
        </div>
        <div className="sacred-card p-8">{children}</div>
      </div>
    </div>
  )

  if (submitted) {
    return (
      <Card>
        <div className="text-center space-y-4">
          <h2 className="font-cinzel text-2xl font-bold text-sacred-800">Check Your Email</h2>
          <p className="text-stone-600">
            If an account with that email exists, we&apos;ve sent password reset instructions.
          </p>
          {resetToken && (
            <div className="p-4 bg-cream-200 border border-gold-500/40 rounded-md text-left">
              <p className="text-sm text-sacred-700 font-semibold mb-2">Development Mode — Reset Token:</p>
              <p className="text-xs text-stone-600 break-all mb-3">{resetToken}</p>
              <Link
                href={`/reset-password?token=${resetToken}`}
                className="gold-link text-sm font-medium underline"
              >
                Click here to reset your password
              </Link>
            </div>
          )}
          <Link href="/login" className="gold-link block font-medium">
            Back to Login
          </Link>
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <h2 className="font-cinzel text-2xl font-bold text-sacred-800 text-center mb-2">
        Forgot Password
      </h2>
      <p className="text-stone-500 text-center text-sm mb-6">
        Enter your email and we&apos;ll send instructions to reset your password.
      </p>
      <form className="space-y-5" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-sacred-700 mb-1">
            Email Address
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            autoComplete="email"
            suppressHydrationWarning
            className="block w-full rounded-md border-cream-300 bg-white shadow-sm focus:border-gold-500 focus:ring-gold-500 focus:ring-1 placeholder-stone-400 text-stone-800"
            placeholder="your@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          suppressHydrationWarning
          className="gold-btn w-full py-2.5"
        >
          {loading ? 'Sending...' : 'Send Reset Instructions'}
        </button>

        <div className="text-center">
          <Link href="/login" className="gold-link text-sm">
            Back to Login
          </Link>
        </div>
      </form>
    </Card>
  )
}
