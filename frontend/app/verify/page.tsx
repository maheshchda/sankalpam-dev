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
      await api.post('/api/auth/verify', { token: emailToken, verification_type: 'email' })
      toast.success('Email verified successfully!')
      setEmailToken('')
      if (refreshUser) await refreshUser()
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
      await api.post('/api/auth/verify', { token: phoneToken, verification_type: 'phone' })
      toast.success('Phone verified successfully!')
      setPhoneToken('')
      if (refreshUser) await refreshUser()
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

  const inputCls = 'w-full px-3 py-2 rounded-md border border-cream-300 bg-white text-stone-800 focus:outline-none focus:ring-1 focus:ring-gold-500 focus:border-gold-500'

  return (
    <div className="page-bg flex flex-col items-center justify-center py-16 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="mx-auto h-14 w-14 rounded-full bg-sacred-800 flex items-center justify-center mb-3">
            <span className="font-cinzel text-gold-400 font-bold">PS</span>
          </div>
          <h2 className="font-cinzel text-3xl font-bold text-sacred-800">Verify Account</h2>
          <p className="text-stone-500 mt-2">Complete your account verification</p>
        </div>

        <div className="sacred-card p-8 space-y-8">
          <div>
            <h3 className="font-cinzel text-lg font-semibold text-sacred-700 mb-4">Verify Email</h3>
            <form onSubmit={handleEmailVerify} className="space-y-4">
              <input
                type="text"
                placeholder="Enter email verification token"
                className={inputCls}
                value={emailToken}
                onChange={(e) => setEmailToken(e.target.value)}
                required
              />
              <button type="submit" disabled={loading} className="gold-btn w-full py-2.5">
                Verify Email
              </button>
            </form>
          </div>

          <div className="gold-divider" />

          <div>
            <h3 className="font-cinzel text-lg font-semibold text-sacred-700 mb-4">Verify Phone (OTP)</h3>
            <form onSubmit={handlePhoneVerify} className="space-y-4">
              <input
                type="text"
                placeholder="Enter 6-digit OTP"
                className={inputCls}
                value={phoneToken}
                onChange={(e) => setPhoneToken(e.target.value)}
                maxLength={6}
                required
              />
              <button type="submit" disabled={loading} className="gold-btn w-full py-2.5">
                Verify Phone
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
