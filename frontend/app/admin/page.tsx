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
    return <div className="page-bg flex items-center justify-center">
      <p className="font-cinzel text-sacred-700 text-xl">Loading...</p>
    </div>
  }

  const thCls = 'px-6 py-3 text-left text-xs font-cinzel font-semibold text-gold-400 uppercase'
  const tdCls = 'px-6 py-4'
  const inputCls = 'mt-1 block w-full rounded-md border-cream-300 bg-white shadow-sm focus:border-gold-500 focus:ring-1 focus:ring-gold-500 text-stone-800'

  return (
    <div className="page-bg">
      <nav className="sacred-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-3">
              <h1 className="font-cinzel text-xl font-bold text-gold-400">Sankalpam Admin Portal</h1>
              <span className="text-cream-300/60 text-sm hidden sm:inline">Welcome, {user?.first_name}!</span>
            </div>
            <button onClick={() => { logout(); router.push('/login') }} className="rounded-md border border-gold-600/40 px-3 py-1.5 text-sm text-cream-300 hover:bg-sacred-700 transition-colors">Logout</button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="sacred-card p-4">
            <h3 className="text-sm font-medium text-stone-500">Total Poojas</h3>
            <p className="text-3xl font-bold text-gold-600 mt-2">{poojas.length}</p>
          </div>
          <div className="sacred-card p-4">
            <h3 className="text-sm font-medium text-stone-500">Active Poojas</h3>
            <p className="text-3xl font-bold text-green-600 mt-2">{poojas.filter(p => p.is_active).length}</p>
          </div>
          <div className="sacred-card p-4">
            <h3 className="text-sm font-medium text-stone-500">Inactive Poojas</h3>
            <p className="text-3xl font-bold text-stone-400 mt-2">{poojas.filter(p => !p.is_active).length}</p>
          </div>
        </div>

        <div className="sacred-card p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="font-cinzel text-2xl font-bold text-sacred-800">Manage Poojas</h2>
            <button onClick={() => setShowForm(!showForm)} className="gold-btn">{showForm ? 'Cancel' : '+ Add New Pooja'}</button>
          </div>

          {showForm && (
            <form onSubmit={handleSubmit} className="mb-6 border-b border-cream-300 pb-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-sacred-700">Pooja Name *</label>
                <input type="text" required className={inputCls} value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
              </div>
              <div>
                <label className="block text-sm font-medium text-sacred-700">Description</label>
                <textarea className={inputCls} rows={3} value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
              </div>
              <div>
                <label className="block text-sm font-medium text-sacred-700">Duration (minutes) *</label>
                <input type="number" required min={1} className={inputCls} value={formData.duration_minutes} onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })} />
              </div>
              <button type="submit" className="gold-btn">Create Pooja</button>
            </form>
          )}

          {poojas.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-stone-500 text-lg mb-2">No poojas created yet.</p>
              <p className="text-stone-400 text-sm">Click &quot;Add New Pooja&quot; to create your first pooja.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-cream-300">
                <thead className="bg-sacred-800">
                  <tr>
                    <th className={thCls}>Pooja Name</th>
                    <th className={thCls}>Description</th>
                    <th className={thCls}>Duration</th>
                    <th className={thCls}>Status</th>
                    <th className={thCls}>Created</th>
                    <th className={`${thCls} text-right`}>Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cream-200">
                  {poojas.map((pooja) => (
                    <tr key={pooja.id} className="hover:bg-cream-100">
                      <td className={tdCls}><div className="text-sm font-medium text-sacred-800">{pooja.name}</div></td>
                      <td className={tdCls}><div className="text-sm text-stone-500">{pooja.description || <span className="text-stone-400 italic">No description</span>}</div></td>
                      <td className={tdCls}><div className="text-sm text-stone-700">{pooja.duration_minutes} min</div></td>
                      <td className={tdCls}><span className={`px-2 text-xs font-semibold rounded-full py-0.5 ${pooja.is_active ? 'bg-green-100 text-green-800' : 'bg-stone-100 text-stone-600'}`}>{pooja.is_active ? 'Active' : 'Inactive'}</span></td>
                      <td className={`${tdCls} text-sm text-stone-500`}>{new Date(pooja.created_at).toLocaleDateString()}</td>
                      <td className={`${tdCls} text-right`}><button onClick={() => handleDelete(pooja.id)} className="text-red-600 hover:text-red-900 text-sm">Delete</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="mt-6 sacred-card p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="font-cinzel text-2xl font-bold text-sacred-800">Manage Sankalpam Templates</h2>
            <button onClick={() => { setShowTemplateForm(!showTemplateForm); setEditingTemplate(null); setTemplateFormData({ name: '', description: '', template_text: '', language: 'sanskrit' }) }} className="sacred-btn">
              {showTemplateForm ? 'Cancel' : '+ Add New Template'}
            </button>
          </div>

          {showTemplateForm && (
            <form onSubmit={handleTemplateSubmit} className="mb-6 border-b border-cream-300 pb-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-sacred-700">Template Name *</label>
                <input type="text" required className={inputCls} value={templateFormData.name} onChange={(e) => setTemplateFormData({ ...templateFormData, name: e.target.value })} />
              </div>
              <div>
                <label className="block text-sm font-medium text-sacred-700">Description</label>
                <textarea className={inputCls} rows={2} value={templateFormData.description} onChange={(e) => setTemplateFormData({ ...templateFormData, description: e.target.value })} />
              </div>
              <div>
                <label className="block text-sm font-medium text-sacred-700">Language *</label>
                <select required className={inputCls} value={templateFormData.language} onChange={(e) => setTemplateFormData({ ...templateFormData, language: e.target.value })}>
                  <option value="sanskrit">Sanskrit</option>
                  <option value="hindi">Hindi</option>
                  <option value="tamil">Tamil</option>
                  <option value="telugu">Telugu</option>
                  <option value="kannada">Kannada</option>
                  <option value="malayalam">Malayalam</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-sacred-700">Template Text *</label>
                <p className="text-xs text-stone-500 mb-1">Use variables like {'{'}{'{'} geographical_reference {'}'}{'}'},  {'{'}{'{'} user_name {'}'}{'}'}', etc.</p>
                <textarea required className={`${inputCls} font-mono text-sm`} rows={15} value={templateFormData.template_text} onChange={(e) => setTemplateFormData({ ...templateFormData, template_text: e.target.value })} />
              </div>
              <button type="submit" className="sacred-btn">{editingTemplate ? 'Update Template' : 'Create Template'}</button>
            </form>
          )}

          {templates.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-stone-500 text-lg mb-2">No templates created yet.</p>
              <p className="text-stone-400 text-sm">Click &quot;Add New Template&quot; to create your first template.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-cream-300">
                <thead className="bg-sacred-800">
                  <tr>
                    <th className={thCls}>Template Name</th>
                    <th className={thCls}>Description</th>
                    <th className={thCls}>Language</th>
                    <th className={thCls}>Status</th>
                    <th className={thCls}>Created</th>
                    <th className={`${thCls} text-right`}>Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cream-200">
                  {templates.map((template) => (
                    <tr key={template.id} className="hover:bg-cream-100">
                      <td className={tdCls}><div className="text-sm font-medium text-sacred-800">{template.name}</div></td>
                      <td className={tdCls}><div className="text-sm text-stone-500">{template.description || <span className="italic">No description</span>}</div></td>
                      <td className={tdCls}><div className="text-sm text-stone-700 capitalize">{template.language}</div></td>
                      <td className={tdCls}><span className={`px-2 text-xs font-semibold rounded-full py-0.5 ${template.is_active ? 'bg-green-100 text-green-800' : 'bg-stone-100 text-stone-600'}`}>{template.is_active ? 'Active' : 'Inactive'}</span></td>
                      <td className={`${tdCls} text-sm text-stone-500`}>{new Date(template.created_at).toLocaleDateString()}</td>
                      <td className={`${tdCls} text-right space-x-2`}>
                        <button onClick={() => handleEditTemplate(template)} className="gold-link text-sm">Edit</button>
                        <button onClick={() => handleDeleteTemplate(template.id)} className="text-red-600 hover:text-red-900 text-sm">Delete</button>
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
  )
}

