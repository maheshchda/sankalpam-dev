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
      toast.success(response.data.message || 'Password reset instructions have been sent to your email!')
      
      // In development, if token is returned, store it for display
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-100">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Loading...</h2>
        </div>
      </div>
    )
  }

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-lg">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-gray-900 mb-4">
              Check Your Email
            </h2>
            <p className="text-gray-600 mb-6">
              If an account with that email exists, we've sent password reset instructions to your email address.
            </p>
            
            {resetToken && (
              <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-md">
                <p className="text-sm text-gray-700 mb-2 font-semibold">Development Mode - Reset Token:</p>
                <p className="text-xs text-gray-600 break-all mb-3">{resetToken}</p>
                <Link
                  href={`/reset-password?token=${resetToken}`}
                  className="inline-block text-sm text-amber-600 hover:text-amber-500 font-medium underline"
                >
                  Click here to reset your password
                </Link>
              </div>
            )}
            
            <div className="space-y-2">
              <Link
                href="/login"
                className="block text-amber-600 hover:text-amber-500 font-medium"
              >
                Back to Login
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-lg">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Forgot Password
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter your email address and we'll send you instructions to reset your password.
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="sr-only">
              Email Address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              autoComplete="email"
              suppressHydrationWarning
              className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-amber-500 focus:border-amber-500 focus:z-10 sm:text-sm"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              suppressHydrationWarning
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-amber-600 hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 disabled:opacity-50"
            >
              {loading ? 'Sending...' : 'Send Reset Instructions'}
            </button>
          </div>

          <div className="text-center">
            <Link href="/login" className="text-sm text-amber-600 hover:text-amber-500">
              Back to Login
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}

