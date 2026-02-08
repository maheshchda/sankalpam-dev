'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'react-toastify'
import Link from 'next/link'

interface Pooja {
  id: number
  name: string
  description: string
  duration_minutes: number
}

export default function PoojaPage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [poojas, setPoojas] = useState<Pooja[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPooja, setSelectedPooja] = useState<Pooja | null>(null)

  useEffect(() => {
    if (!user) {
      router.push('/login')
    } else {
      fetchPoojas()
    }
  }, [user, router])

  const fetchPoojas = async () => {
    try {
      const response = await api.get('/api/pooja/list')
      setPoojas(response.data)
    } catch (error) {
      console.error('Error fetching poojas:', error)
      toast.error('Failed to load poojas')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectPooja = async (pooja: Pooja) => {
    setSelectedPooja(pooja)
    try {
      // Create a pooja session with default location (user's birth location)
      const response = await api.post('/api/pooja/session', {
        pooja_id: pooja.id,
        location_city: user?.birth_city,
        location_state: user?.birth_state,
        location_country: user?.birth_country,
      })
      
      router.push(`/playback?session_id=${response.data.id}`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start pooja session')
    }
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="text-2xl font-bold text-amber-600">
              Sankalpam
            </Link>
            <div className="flex items-center space-x-4">
              <Link href="/dashboard" className="px-4 py-2 text-gray-700 hover:text-amber-600">
                Back to Dashboard
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

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold mb-6">Select a Pooja</h2>
          
          {poojas.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No poojas available. Please contact admin.</p>
          ) : (
            <div className="space-y-4">
              {poojas.map((pooja) => (
                <div
                  key={pooja.id}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => handleSelectPooja(pooja)}
                >
                  <h3 className="font-bold text-lg mb-2">{pooja.name}</h3>
                  {pooja.description && (
                    <p className="text-gray-600 mb-2">{pooja.description}</p>
                  )}
                  {pooja.duration_minutes && (
                    <p className="text-sm text-gray-500">Duration: {pooja.duration_minutes} minutes</p>
                  )}
                  <button className="mt-3 px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700">
                    Select & Start
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

