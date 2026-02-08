'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'

export default function Home() {
  const router = useRouter()
  const { user, loading } = useAuth()

  useEffect(() => {
    if (!loading) {
      if (user) {
        // Redirect admins to admin portal, regular users to dashboard
        if (user.is_admin) {
          router.push('/admin')
        } else {
          router.push('/dashboard')
        }
      } else {
        router.push('/login')
      }
    }
  }, [user, loading, router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Sankalpam</h1>
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  )
}

