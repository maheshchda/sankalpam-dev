'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import AdminLayout from '@/components/admin/AdminLayout'
import UserManagementPanel from '@/components/admin/UserManagementPanel'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const VALID_TABS = ['stats', 'roles', 'users', 'admins'] as const
type TabType = (typeof VALID_TABS)[number]

type Stats = {
  total_users: number
  active_users: number
  inactive_users: number
  verified_users: number
  unverified_users: number
  admin_users: number
  total_poojas: number
  total_sessions: number
}

type AdminRole = {
  id: number
  name: string
  description: string | null
  permissions: string[]
  is_system_role: boolean
  created_at: string
  user_count: number
}

type Permission = { code: string; description: string }

export default function AdminDashboard() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const tabParam = searchParams.get('tab')
  const initialTab: TabType = VALID_TABS.includes(tabParam as TabType) ? (tabParam as TabType) : 'stats'
  const [token, setToken] = useState<string | null>(null)
  const [tab, setTab] = useState<TabType>(initialTab)

  useEffect(() => {
    if (tabParam && VALID_TABS.includes(tabParam as TabType)) {
      setTab(tabParam as TabType)
    }
  }, [tabParam])

  const [stats, setStats] = useState<Stats | null>(null)
  const [roles, setRoles] = useState<AdminRole[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [loadingStats, setLoadingStats] = useState(false)
  const [loadingRoles, setLoadingRoles] = useState(false)
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

  // Role editor
  const [showEditor, setShowEditor] = useState(false)
  const [editingRole, setEditingRole] = useState<AdminRole | null>(null)
  const [roleForm, setRoleForm] = useState({ name: '', description: '', permissions: [] as string[] })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const t = localStorage.getItem('admin_token')
    if (!t) { router.replace('/admin/login'); return }
    setToken(t)
  }, [router])

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 4000)
  }

  const apiFetch = useCallback(async (path: string, opts: RequestInit = {}) => {
    if (!token) return null
    const res = await fetch(`${API}${path}`, {
      ...opts,
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...(opts.headers as Record<string, string> || {}),
      },
    })
    if (res.status === 401 || res.status === 403) {
      localStorage.removeItem('admin_token')
      router.replace('/admin/login')
      return null
    }
    return res
  }, [token, router])

  const fetchStats = useCallback(async () => {
    if (!token) return
    setLoadingStats(true)
    try {
      const res = await apiFetch('/api/admin/stats')
      if (res?.ok) setStats(await res.json())
    } finally { setLoadingStats(false) }
  }, [token, apiFetch])

  const fetchRoles = useCallback(async () => {
    if (!token) return
    setLoadingRoles(true)
    try {
      const [rolesRes, permsRes] = await Promise.all([
        apiFetch('/api/admin/roles'),
        apiFetch('/api/admin/permissions'),
      ])
      if (rolesRes?.ok) setRoles(await rolesRes.json())
      if (permsRes?.ok) setPermissions(await permsRes.json())
    } finally { setLoadingRoles(false) }
  }, [token, apiFetch])

  useEffect(() => {
    if (token) { fetchStats(); fetchRoles() }
  }, [token, fetchStats, fetchRoles])

  const openEditor = (role?: AdminRole) => {
    if (role) {
      setEditingRole(role)
      setRoleForm({ name: role.name, description: role.description || '', permissions: [...role.permissions] })
    } else {
      setEditingRole(null)
      setRoleForm({ name: '', description: '', permissions: [] })
    }
    setShowEditor(true)
  }

  const saveRole = async () => {
    if (!roleForm.name.trim()) { showToast('Role name is required', 'error'); return }
    setSaving(true)
    const body = { name: roleForm.name.trim(), description: roleForm.description, permissions: roleForm.permissions }
    const res = editingRole
      ? await apiFetch(`/api/admin/roles/${editingRole.id}`, { method: 'PUT', body: JSON.stringify(body) })
      : await apiFetch('/api/admin/roles', { method: 'POST', body: JSON.stringify(body) })
    setSaving(false)
    if (res?.ok) {
      showToast(editingRole ? 'Role updated' : 'Role created')
      setShowEditor(false)
      fetchRoles()
    } else {
      showToast((await res?.json())?.detail || 'Failed', 'error')
    }
  }

  const deleteRole = async (role: AdminRole) => {
    if (role.is_system_role) { showToast('System roles cannot be deleted', 'error'); return }
    if (!window.confirm(`Delete role "${role.name}"?`)) return
    const res = await apiFetch(`/api/admin/roles/${role.id}`, { method: 'DELETE' })
    if (res?.status === 204) { showToast(`Role "${role.name}" deleted`); fetchRoles() }
    else showToast((await res?.json())?.detail || 'Delete failed', 'error')
  }

  const togglePermission = (code: string) => {
    setRoleForm(prev => ({
      ...prev,
      permissions: prev.permissions.includes(code)
        ? prev.permissions.filter(p => p !== code)
        : [...prev.permissions, code],
    }))
  }

  if (!token) return null

  return (
    <AdminLayout>
      {toast && (
        <div className={`fixed top-4 right-4 z-50 rounded-lg px-5 py-3 shadow-lg text-white text-sm font-medium ${toast.type === 'error' ? 'bg-red-600' : 'bg-emerald-600'}`}>
          {toast.msg}
        </div>
      )}

      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-cinzel text-2xl font-bold text-sacred-800">Admin Dashboard</h1>
          <p className="text-sm text-stone-500 mt-0.5">Overview and role management</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-cream-300 mb-6 flex-wrap">
        {([
          ['stats',  'Dashboard Stats'],
          ['users',  'User Management'],
          ['admins', 'Admin Accounts'],
          ['roles',  'Roles & Permissions'],
        ] as [TabType, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-5 py-2.5 text-sm font-semibold rounded-t-lg transition -mb-px ${
              tab === key
                ? 'bg-white border border-b-white border-cream-300 text-gold-600'
                : 'text-stone-500 hover:text-stone-800'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Stats tab */}
      {tab === 'stats' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-cinzel text-lg font-semibold text-sacred-700">System Overview</h2>
            <button onClick={fetchStats} className="text-sm gold-link hover:underline">Refresh</button>
          </div>
          {loadingStats ? (
            <p className="text-slate-500">Loading…</p>
          ) : stats ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {([
                ['Total Users',    stats.total_users,     'bg-blue-50 text-blue-700'],
                ['Active',         stats.active_users,    'bg-green-50 text-green-700'],
                ['Inactive',       stats.inactive_users,  'bg-red-50 text-red-600'],
                ['Verified',       stats.verified_users,  'bg-teal-50 text-teal-700'],
                ['Unverified',     stats.unverified_users,'bg-yellow-50 text-yellow-700'],
                ['Admin Users',    stats.admin_users,     'bg-purple-50 text-purple-700'],
                ['Total Poojas',   stats.total_poojas,    'bg-orange-50 text-orange-700'],
                ['Pooja Sessions', stats.total_sessions,  'bg-slate-50 text-slate-700'],
              ] as [string, number, string][]).map(([label, value, cls]) => (
                <div key={label} className={`rounded-xl border p-5 ${cls.split(' ')[0]} border-opacity-30`}>
                  <p className={`text-3xl font-bold ${cls.split(' ')[1]}`}>{value}</p>
                  <p className="text-sm text-slate-500 mt-1">{label}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-400">No stats available.</p>
          )}
        </div>
      )}

      {/* Roles tab */}
      {tab === 'roles' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-cinzel text-lg font-semibold text-sacred-700">Roles &amp; Permissions</h2>
              <p className="text-sm text-stone-500">Define what each admin role can do.</p>
            </div>
            <button onClick={() => openEditor()} className="gold-btn text-sm py-2">+ Create Role</button>
          </div>

          {loadingRoles ? (
            <p className="text-stone-500">Loading…</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {roles.map(role => (
                <div key={role.id} className="sacred-card p-5">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-cinzel font-bold text-sacred-800">{role.name}</h3>
                        {role.is_system_role && (
                          <span className="text-xs bg-gold-500/20 text-gold-700 px-2 py-0.5 rounded-full font-medium border border-gold-500/30">System</span>
                        )}
                      </div>
                      {role.description && <p className="text-sm text-stone-500 mt-0.5">{role.description}</p>}
                      <p className="text-xs text-stone-400 mt-1">{role.user_count} user(s) assigned</p>
                    </div>
                    <div className="flex gap-1 shrink-0">
                      <button onClick={() => openEditor(role)} className="px-2 py-1 text-xs rounded bg-cream-200 hover:bg-cream-300 text-sacred-700 border border-cream-300">Edit</button>
                      {!role.is_system_role && (
                        <button onClick={() => deleteRole(role)} className="px-2 py-1 text-xs rounded bg-red-100 hover:bg-red-200 text-red-700">Delete</button>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {role.permissions.includes('*') ? (
                      <span className="text-xs bg-sacred-700/10 text-sacred-700 px-2 py-0.5 rounded-full font-semibold border border-sacred-700/20">All Permissions (*)</span>
                    ) : role.permissions.length === 0 ? (
                      <span className="text-xs text-stone-400 italic">No permissions assigned</span>
                    ) : role.permissions.map(p => (
                      <span key={p} className="text-xs bg-gold-500/10 text-gold-700 px-2 py-0.5 rounded-full border border-gold-500/20">{p}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* User Management tab */}
      {tab === 'users' && (
        <div>
          <div className="mb-4">
            <h2 className="font-cinzel text-lg font-semibold text-sacred-700">User Management</h2>
            <p className="text-sm text-stone-500">View, create, edit, and manage all frontend user accounts.</p>
          </div>
          <UserManagementPanel />
        </div>
      )}

      {/* Admin Accounts tab */}
      {tab === 'admins' && (
        <div>
          <div className="mb-4">
            <h2 className="font-cinzel text-lg font-semibold text-sacred-700">Admin Accounts</h2>
            <p className="text-sm text-stone-500">Manage administrator accounts, assign roles, and control admin access.</p>
          </div>
          <UserManagementPanel showAdmins />
        </div>
      )}

      {/* Role editor modal */}
      {showEditor && (
        <div className="fixed inset-0 bg-black/50 z-40 flex items-center justify-center p-4" onClick={() => setShowEditor(false)}>
          <div className="sacred-card w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h3 className="font-cinzel text-lg font-bold text-sacred-800">{editingRole ? 'Edit Role' : 'Create New Role'}</h3>
              <button onClick={() => setShowEditor(false)} className="text-stone-400 hover:text-stone-600 text-xl">&times;</button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-sacred-700 mb-1">Role Name *</label>
                <input type="text" value={roleForm.name} onChange={e => setRoleForm(p => ({ ...p, name: e.target.value }))} className="w-full border border-cream-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gold-400 focus:border-gold-500" placeholder="e.g. Content Reviewer" />
              </div>
              <div>
                <label className="block text-sm font-medium text-sacred-700 mb-1">Description</label>
                <textarea value={roleForm.description} onChange={e => setRoleForm(p => ({ ...p, description: e.target.value }))} rows={2} className="w-full border border-cream-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gold-400 focus:border-gold-500" placeholder="What can this role do?" />
              </div>
              <div>
                <label className="block text-sm font-medium text-sacred-700 mb-2">Permissions</label>
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {permissions.map(perm => (
                    <label key={perm.code} className={`flex items-start gap-3 p-2.5 rounded-lg border cursor-pointer transition ${roleForm.permissions.includes(perm.code) ? 'bg-gold-500/10 border-gold-500/40' : 'border-cream-300 hover:bg-cream-100'}`}>
                      <input type="checkbox" checked={roleForm.permissions.includes(perm.code)} onChange={() => togglePermission(perm.code)} className="mt-0.5 accent-gold-600" />
                      <div>
                        <p className="text-sm font-medium text-sacred-800">{perm.code}</p>
                        <p className="text-xs text-stone-500">{perm.description}</p>
                      </div>
                    </label>
                  ))}
                </div>
                <p className="text-xs text-stone-400 mt-1">{roleForm.permissions.length} permission(s) selected</p>
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button onClick={saveRole} disabled={saving} className="flex-1 gold-btn py-2 text-sm">
                {saving ? 'Saving…' : editingRole ? 'Update Role' : 'Create Role'}
              </button>
              <button onClick={() => setShowEditor(false)} className="flex-1 bg-cream-200 hover:bg-cream-300 text-stone-700 rounded-lg py-2 text-sm font-medium border border-cream-300">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  )
}
