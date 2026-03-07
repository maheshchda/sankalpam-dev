'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { toast } from 'react-toastify'
import Link from 'next/link'
import api from '@/lib/api'

const inputCls = 'block w-full rounded-md border-cream-300 bg-white shadow-sm focus:border-gold-500 focus:ring-gold-500 focus:ring-1 placeholder-stone-400 text-stone-800'

export default function ResetPasswordPage() {
  const [token, setToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [success, setSuccess] = useState(false)
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    setMounted(true)
    const tokenParam = searchParams.get('token')
    if (tokenParam) setToken(tokenParam)
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (newPassword !== confirmPassword) { toast.error('Passwords do not match'); return }
    if (newPassword.length < 8) { toast.error('Password must be at least 8 characters long'); return }
    setLoading(true)
    try {
      await api.post('/api/auth/reset-password', { token, new_password: newPassword })
      toast.success('Password reset successfully!')
      setSuccess(true)
      setTimeout(() => router.push('/login'), 2000)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to reset password')
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

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
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

  if (success) {
    return (
      <Wrapper>
        <div className="text-center space-y-4">
          <h2 className="font-cinzel text-2xl font-bold text-sacred-800">Password Reset!</h2>
          <p className="text-stone-600">Your password has been reset. Redirecting to login...</p>
          <Link href="/login" className="gold-link font-medium">Go to Login</Link>
        </div>
      </Wrapper>
    )
  }

  return (
    <Wrapper>
      <h2 className="font-cinzel text-2xl font-bold text-sacred-800 text-center mb-2">Reset Password</h2>
      <p className="text-stone-500 text-sm text-center mb-6">Enter your reset token and new password.</p>
      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="token" className="sr-only">Reset Token</label>
          <input id="token" name="token" type="text" required suppressHydrationWarning className={inputCls} placeholder="Reset token" value={token} onChange={(e) => setToken(e.target.value)} />
        </div>
        <div>
          <label htmlFor="newPassword" className="sr-only">New Password</label>
          <input id="newPassword" name="newPassword" type="password" required minLength={8} suppressHydrationWarning className={inputCls} placeholder="New password (min 8 characters)" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
        </div>
        <div>
          <label htmlFor="confirmPassword" className="sr-only">Confirm Password</label>
          <input id="confirmPassword" name="confirmPassword" type="password" required minLength={8} suppressHydrationWarning className={inputCls} placeholder="Confirm new password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
        </div>

        <button type="submit" disabled={loading} suppressHydrationWarning className="gold-btn w-full py-2.5">
          {loading ? 'Resetting...' : 'Reset Password'}
        </button>

        <div className="text-center">
          <Link href="/login" className="gold-link text-sm">Back to Login</Link>
        </div>
      </form>
    </Wrapper>
  )
}
