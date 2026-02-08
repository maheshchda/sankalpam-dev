'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import Link from 'next/link'

interface FamilyMember {
  id: number
  name: string
  relation: string
  gender: string
}

export default function DashboardPage() {
  const { user, loading: authLoading, logout } = useAuth()
  const router = useRouter()
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    } else if (!authLoading && user?.is_admin) {
      // Redirect admins to admin portal instead of regular dashboard
      router.push('/admin')
      return
    }
  }, [user, authLoading, router])

  useEffect(() => {
    // Only fetch family members if user is not an admin
    if (user && !user.is_admin) {
      fetchFamilyMembers()
    }
  }, [user])

  const fetchFamilyMembers = async () => {
    try {
      const response = await api.get('/api/family/members')
      setFamilyMembers(response.data)
    } catch (error) {
      console.error('Error fetching family members:', error)
    } finally {
      setLoading(false)
    }
  }

  if (authLoading || loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  // Don't render dashboard for admins - redirect to admin portal
  if (user?.is_admin) {
    return <div className="min-h-screen flex items-center justify-center">Redirecting to admin portal...</div>
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-amber-600">Sankalpam</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Welcome, {user.first_name}!</span>
              <Link href="/sankalpam" className="px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700">
                Generate Sankalpam
              </Link>
              <Link href="/pooja" className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                Select Pooja
              </Link>
              <button
                onClick={() => {
                  logout()
                  router.push('/login')
                }}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Family Members Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Family Members</h2>
              <Link
                href="/family"
                className="px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 text-sm"
              >
                Manage
              </Link>
            </div>
            {familyMembers.length === 0 ? (
              <p className="text-gray-500">No family members added yet.</p>
            ) : (
              <ul className="space-y-2">
                {familyMembers.map((member) => (
                  <li key={member.id} className="flex justify-between py-2 border-b">
                    <span className="font-medium">{member.name}</span>
                    <span className="text-gray-500">{member.relation}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Quick Actions Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Link
                href="/family"
                className="block px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Add Family Member
              </Link>
              <Link
                href="/sankalpam"
                className="block px-4 py-2 bg-amber-100 rounded-md hover:bg-amber-200 font-medium"
              >
                Generate Sankalpam
              </Link>
              <Link
                href="/pooja"
                className="block px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Select Pooja
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

