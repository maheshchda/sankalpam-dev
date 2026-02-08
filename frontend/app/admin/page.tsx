'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'react-toastify'

interface Pooja {
  id: number
  name: string
  description: string
  duration_minutes: number
  is_active: boolean
  created_at: string
}

interface Template {
  id: number
  name: string
  description: string | null
  template_text: string
  language: string
  variables: string | null
  is_active: boolean
  created_at: string
}

export default function AdminPage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [poojas, setPoojas] = useState<Pooja[]>([])
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [showTemplateForm, setShowTemplateForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    duration_minutes: 60,
  })
  const [templateFormData, setTemplateFormData] = useState({
    name: '',
    description: '',
    template_text: '',
    language: 'sanskrit',
  })
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null)

  useEffect(() => {
    if (!user) {
      router.push('/login')
    } else if (!user.is_admin) {
      toast.error('Admin access required')
      router.push('/dashboard')
    } else {
      fetchPoojas()
      fetchTemplates()
    }
  }, [user, router])

  const fetchPoojas = async () => {
    try {
      const response = await api.get('/api/admin/poojas')
      setPoojas(response.data)
    } catch (error) {
      console.error('Error fetching poojas:', error)
      toast.error('Failed to load poojas')
    }
  }

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/api/admin/templates')
      setTemplates(response.data)
    } catch (error) {
      console.error('Error fetching templates:', error)
      toast.error('Failed to load templates')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/api/admin/poojas', formData)
      toast.success('Pooja created successfully!')
      setShowForm(false)
      setFormData({ name: '', description: '', duration_minutes: 60 })
      fetchPoojas()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create pooja')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this pooja?')) return
    
    try {
      await api.delete(`/api/admin/poojas/${id}`)
      toast.success('Pooja deleted successfully!')
      fetchPoojas()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete pooja')
    }
  }

  const handleTemplateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingTemplate) {
        await api.put(`/api/admin/templates/${editingTemplate.id}`, templateFormData)
        toast.success('Template updated successfully!')
      } else {
        await api.post('/api/admin/templates', templateFormData)
        toast.success('Template created successfully!')
      }
      setShowTemplateForm(false)
      setEditingTemplate(null)
      setTemplateFormData({ name: '', description: '', template_text: '', language: 'sanskrit' })
      fetchTemplates()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save template')
    }
  }

  const handleEditTemplate = (template: Template) => {
    setEditingTemplate(template)
    setTemplateFormData({
      name: template.name,
      description: template.description || '',
      template_text: template.template_text,
      language: template.language,
    })
    setShowTemplateForm(true)
  }

  const handleDeleteTemplate = async (id: number) => {
    if (!confirm('Are you sure you want to delete this template?')) return
    
    try {
      await api.delete(`/api/admin/templates/${id}`)
      toast.success('Template deleted successfully!')
      fetchTemplates()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete template')
    }
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100">
      {/* Admin Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-amber-600">Sankalpam - Admin Portal</h1>
              <span className="text-sm text-gray-500">Welcome, {user?.first_name}!</span>
            </div>
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
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Admin Dashboard Overview */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Total Poojas</h3>
            <p className="text-3xl font-bold text-amber-600 mt-2">{poojas.length}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Active Poojas</h3>
            <p className="text-3xl font-bold text-green-600 mt-2">
              {poojas.filter(p => p.is_active).length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Inactive Poojas</h3>
            <p className="text-3xl font-bold text-gray-400 mt-2">
              {poojas.filter(p => !p.is_active).length}
            </p>
          </div>
        </div>

        {/* Pooja Management Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Manage Poojas</h2>
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700"
            >
              {showForm ? 'Cancel' : '+ Add New Pooja'}
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleSubmit} className="mb-6 border-b pb-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Pooja Name *</label>
                <input
                  type="text"
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Duration (minutes) *</label>
                <input
                  type="number"
                  required
                  min={1}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  value={formData.duration_minutes}
                  onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })}
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700"
              >
                Create Pooja
              </button>
            </form>
          )}

          <div className="space-y-4">
            {poojas.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg mb-4">No poojas created yet.</p>
                <p className="text-gray-400 text-sm">Click "Add New Pooja" to create your first pooja.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Pooja Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Description
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Duration
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {poojas.map((pooja) => (
                      <tr key={pooja.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{pooja.name}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-500">
                            {pooja.description || <span className="text-gray-400">No description</span>}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{pooja.duration_minutes} minutes</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            pooja.is_active 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {pooja.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(pooja.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => handleDelete(pooja.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Template Management Section */}
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Manage Sankalpam Templates</h2>
            <button
              onClick={() => {
                setShowTemplateForm(!showTemplateForm)
                setEditingTemplate(null)
                setTemplateFormData({ name: '', description: '', template_text: '', language: 'sanskrit' })
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              {showTemplateForm ? 'Cancel' : '+ Add New Template'}
            </button>
          </div>

          {showTemplateForm && (
            <form onSubmit={handleTemplateSubmit} className="mb-6 border-b pb-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Template Name *</label>
                <input
                  type="text"
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  value={templateFormData.name}
                  onChange={(e) => setTemplateFormData({ ...templateFormData, name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  rows={2}
                  value={templateFormData.description}
                  onChange={(e) => setTemplateFormData({ ...templateFormData, description: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Language *</label>
                <select
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  value={templateFormData.language}
                  onChange={(e) => setTemplateFormData({ ...templateFormData, language: e.target.value })}
                >
                  <option value="sanskrit">Sanskrit</option>
                  <option value="hindi">Hindi</option>
                  <option value="tamil">Tamil</option>
                  <option value="telugu">Telugu</option>
                  <option value="kannada">Kannada</option>
                  <option value="malayalam">Malayalam</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Template Text *</label>
                <p className="text-xs text-gray-500 mb-1">
                  Use variables like {'{{geographical_reference}}'}, {'{{user_name}}'}, {'{{geographical_feature}}'}, etc.
                </p>
                <textarea
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm font-mono text-sm"
                  rows={15}
                  value={templateFormData.template_text}
                  onChange={(e) => setTemplateFormData({ ...templateFormData, template_text: e.target.value })}
                  placeholder="श्री गणेशाय नमः&#10;&#10;{{geographical_reference}}&#10;{{current_location}} नगरे&#10;{{geographical_feature}}"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                {editingTemplate ? 'Update Template' : 'Create Template'}
              </button>
            </form>
          )}

          <div className="space-y-4">
            {templates.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg mb-4">No templates created yet.</p>
                <p className="text-gray-400 text-sm">Click "Add New Template" to create your first template.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Template Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Description
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Language
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {templates.map((template) => (
                      <tr key={template.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{template.name}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-500">
                            {template.description || <span className="text-gray-400">No description</span>}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 capitalize">{template.language}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            template.is_active 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {template.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(template.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                          <button
                            onClick={() => handleEditTemplate(template)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteTemplate(template.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

