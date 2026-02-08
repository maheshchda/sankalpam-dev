'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'react-toastify'
import Link from 'next/link'

interface FamilyMember {
  id: number
  name: string
  relation: string
  gender: string
  date_of_birth: string
  birth_time: string
  birth_city: string
  birth_state: string
  birth_country: string
}

export default function FamilyPage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [members, setMembers] = useState<FamilyMember[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    relation: '',
    gender: 'male',
    date_of_birth: '',
    birth_time: '',
    birth_city: '',
    birth_state: '',
    birth_country: 'India',
  })

  useEffect(() => {
    if (!user) {
      router.push('/login')
    } else {
      fetchMembers()
    }
  }, [user, router])

  const fetchMembers = async () => {
    try {
      const response = await api.get('/api/family/members')
      setMembers(response.data)
    } catch (error) {
      console.error('Error fetching family members:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/api/family/members', formData)
      toast.success('Family member added successfully!')
      setShowForm(false)
      setFormData({
        name: '',
        relation: '',
        gender: 'male',
        date_of_birth: '',
        birth_time: '',
        birth_city: '',
        birth_state: '',
        birth_country: 'India',
      })
      fetchMembers()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to add family member')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this family member?')) return
    
    try {
      await api.delete(`/api/family/members/${id}`)
      toast.success('Family member deleted successfully!')
      fetchMembers()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete family member')
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
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Family Members</h2>
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700"
            >
              {showForm ? 'Cancel' : 'Add Family Member'}
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleSubmit} className="mb-6 border-b pb-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Name *</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Relation *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., father, mother, spouse"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.relation}
                    onChange={(e) => setFormData({ ...formData, relation: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Gender *</label>
                  <select
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Date of Birth *</label>
                  <input
                    type="date"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.date_of_birth}
                    onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Time of Birth (24hr) *</label>
                  <input
                    type="time"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.birth_time}
                    onChange={(e) => setFormData({ ...formData, birth_time: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Birth City *</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.birth_city}
                    onChange={(e) => setFormData({ ...formData, birth_city: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Birth State *</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.birth_state}
                    onChange={(e) => setFormData({ ...formData, birth_state: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Birth Country *</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.birth_country}
                    onChange={(e) => setFormData({ ...formData, birth_country: e.target.value })}
                  />
                </div>
              </div>
              <button
                type="submit"
                className="px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700"
              >
                Add Member
              </button>
            </form>
          )}

          <div className="space-y-4">
            {members.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No family members added yet.</p>
            ) : (
              members.map((member) => (
                <div key={member.id} className="border rounded-lg p-4 flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-lg">{member.name}</h3>
                    <p className="text-gray-600">{member.relation} • {member.gender}</p>
                    <p className="text-sm text-gray-500">
                      Born: {new Date(member.date_of_birth).toLocaleDateString()} in {member.birth_city}, {member.birth_state}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(member.id)}
                    className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                  >
                    Delete
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

