'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import Link from 'next/link'
import HomeButton from '@/components/HomeButton'

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
    return <div className="page-bg flex items-center justify-center">
      <p className="font-cinzel text-sacred-700 text-xl">Loading...</p>
    </div>
  }

  if (user?.is_admin) {
    return <div className="page-bg flex items-center justify-center">
      <p className="font-cinzel text-sacred-700 text-xl">Redirecting to admin portal...</p>
    </div>
  }

  if (!user) {
    return null
  }

  return (
    <div className="page-bg">
      <nav className="sacred-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:h-14 sm:h-16 items-stretch sm:items-center gap-3 sm:gap-4 py-3 sm:py-0">
            <h1 className="font-cinzel text-lg sm:text-xl font-bold text-gold-400 truncate min-w-0 shrink">Pooja Sankalpam</h1>
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 justify-end flex-shrink-0">
              <HomeButton />
              <Link href="/profile" className="btn-glossy btn-glossy-blue shrink-0">Profile</Link>
              <Link href="/pooja-calendar" className="btn-glossy btn-glossy-orange shrink-0">Pooja Calendar</Link>
              <button onClick={() => { logout(); router.push('/login') }} className="btn-glossy btn-glossy-red shrink-0">Logout</button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="sacred-card p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-cinzel text-xl font-bold text-sacred-700">Family Members</h2>
              <Link href="/family" className="btn-glossy btn-glossy-green text-sm">Manage</Link>
            </div>
            {familyMembers.length === 0 ? (
              <p className="text-stone-500">No family members added yet.</p>
            ) : (
              <ul className="space-y-2">
                {familyMembers.map((member) => (
                  <li key={member.id} className="flex justify-between py-2 border-b border-cream-300">
                    <span className="font-medium text-sacred-700">{member.name}</span>
                    <span className="text-stone-500 text-sm">{member.relation}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="sacred-card p-6">
            <h2 className="font-cinzel text-xl font-bold text-sacred-700 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Link href="/family" className="btn-glossy btn-glossy-green block text-center">
                Add Family Member
              </Link>
              <Link href="/schedule-pooja" className="btn-glossy btn-glossy-orange block text-center">
                🪔 Schedule a Pooja
              </Link>
              <Link href="/pooja-calendar" className="btn-glossy btn-glossy-blue block text-center">
                Pooja Calendar
              </Link>
              <Link href="/sankalpam?autoGenerate=1" className="btn-glossy btn-glossy-purple block text-center">
                Generic Sankalpam
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

