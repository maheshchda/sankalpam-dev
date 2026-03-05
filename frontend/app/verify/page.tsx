'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'react-toastify'

export default function VerifyPage() {
  const { user, refreshUser } = useAuth()
  const [emailToken, setEmailToken] = useState('')
  const [phoneToken, setPhoneToken] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const searchParams = useSearchParams()

  // Check for token in URL parameters
  useEffect(() => {
    const token = searchParams.get('token')
    const type = searchParams.get('type')
    if (token && type === 'email') {
      setEmailToken(token)
    }
  }, [searchParams])

  const handleEmailVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/api/auth/verify', {
        token: emailToken,
        verification_type: 'email',
      })
      toast.success('Email verified successfully!')
      setEmailToken('')
      // Refresh user data to reflect verification status
      if (refreshUser) {
        await refreshUser()
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Email verification failed')
    } finally {
      setLoading(false)
    }
  }

  const handlePhoneVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/api/auth/verify', {
        token: phoneToken,
        verification_type: 'phone',
      })
      toast.success('Phone verified successfully!')
      setPhoneToken('')
      // Refresh user data to reflect verification status
      if (refreshUser) {
        await refreshUser()
      }
      // Redirect admins to admin portal, regular users to dashboard
      if (user?.is_admin) {
        router.push('/admin')
      } else {
        router.push('/dashboard')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Phone verification failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 py-12 px-4">
      <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-lg">
        <h2 className="text-2xl font-bold text-center mb-6">Verify Your Account</h2>
        
        <div className="space-y-6">
          {/* Email Verification */}
          <div className="border-b pb-6">
            <h3 className="text-lg font-medium mb-4">Verify Email</h3>
            <form onSubmit={handleEmailVerify} className="space-y-4">
              <input
                type="text"
                placeholder="Enter email verification token"
                className="w-full px-3 py-2 border rounded-md"
                value={emailToken}
                onChange={(e) => setEmailToken(e.target.value)}
                required
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 disabled:opacity-50"
              >
                Verify Email
              </button>
            </form>
          </div>

          {/* Phone Verification */}
          <div>
            <h3 className="text-lg font-medium mb-4">Verify Phone (OTP)</h3>
            <form onSubmit={handlePhoneVerify} className="space-y-4">
              <input
                type="text"
                placeholder="Enter 6-digit OTP"
                className="w-full px-3 py-2 border rounded-md"
                value={phoneToken}
                onChange={(e) => setPhoneToken(e.target.value)}
                maxLength={6}
                required
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 disabled:opacity-50"
              >
                Verify Phone
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

