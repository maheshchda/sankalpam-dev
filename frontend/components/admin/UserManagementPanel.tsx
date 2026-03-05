'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ── Types ─────────────────────────────────────────────────────────────────────
export type AdminUser = {
  id: number
  username: string
  email: string
  phone: string
  first_name: string
  last_name: string
  is_active: boolean
  is_admin: boolean
  email_verified: boolean
  phone_verified: boolean
  preferred_language: string
  created_at: string
  birth_city: string | null
  birth_state: string | null
  birth_country: string | null
  current_city: string | null
  current_state: string | null
  current_country: string | null
  assigned_roles: string[]
}

type Role = { id: number; name: string }

const LANGUAGES = [
  'english','hindi','telugu','tamil','kannada','malayalam',
  'marathi','gujarati','bengali','punjabi','oriya','sanskrit',
]

const EMPTY_CREATE = {
  username: '', password: '', email: '', phone: '',
  first_name: '', last_name: '',
  gotram: 'N/A', birth_date: '1990-01-01', birth_time: '00:00',
  birth_city: 'N/A', birth_state: 'N/A', birth_country: 'India',
  preferred_language: 'english',
  is_admin: false, is_active: true, auto_verify: true,
}

const PAGE_SIZE = 20

// ── Modal helper ──────────────────────────────────────────────────────────────
function Modal({
  title, onClose, children, wide,
}: {
  title: string; onClose: () => void; children: React.ReactNode; wide?: boolean
}) {
  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className={`bg-white rounded-2xl shadow-2xl w-full my-8 p-6 ${wide ? 'max-w-2xl' : 'max-w-lg'}`}
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-bold text-slate-800">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
        </div>
        {children}
      </div>
    </div>
  )
}

// ── Main panel ────────────────────────────────────────────────────────────────
export default function UserManagementPanel({ showAdmins = false }: { showAdmins?: boolean }) {
  const router = useRouter()
  const [token, setToken] = useState<string | null>(null)

  const [users, setUsers] = useState<AdminUser[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(false)

  const [search, setSearch] = useState('')
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'inactive'>('all')
  const [page, setPage] = useState(0)

  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

  // Modals
  const [detailUser,    setDetailUser]    = useState<AdminUser | null>(null)
  const [editUser,      setEditUser]      = useState<AdminUser | null>(null)
  const [editForm,      setEditForm]      = useState<Record<string, string | boolean>>({})
  const [showCreate,    setShowCreate]    = useState(false)
  const [createForm,    setCreateForm]    = useState({ ...EMPTY_CREATE })
  const [resetResult,   setResetResult]   = useState<{ username: string; password: string; email: string } | null>(null)
  const [assigningUser, setAssigningUser] = useState<AdminUser | null>(null)
  const [assignRoleId,  setAssignRoleId]  = useState<number | ''>('')
  const [saving, setSaving] = useState(false)

  // ── Auth ──────────────────────────────────────────────────────────────────
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

  // ── Fetch ─────────────────────────────────────────────────────────────────
  const fetchUsers = useCallback(async () => {
    if (!token) return
    setLoading(true)
    try {
      const params = new URLSearchParams({ skip: String(page * PAGE_SIZE), limit: String(PAGE_SIZE) })
      if (search.trim())               params.set('search',    search.trim())
      if (filterActive === 'active')   params.set('is_active', 'true')
      if (filterActive === 'inactive') params.set('is_active', 'false')
      params.set('is_admin', showAdmins ? 'true' : 'false')
      const res = await apiFetch(`/api/admin/users?${params}`)
      if (res?.ok) setUsers(await res.json())
    } finally { setLoading(false) }
  }, [token, apiFetch, search, filterActive, page, showAdmins])

  const fetchRoles = useCallback(async () => {
    const res = await apiFetch('/api/admin/roles')
    if (res?.ok) {
      const data = await res.json()
      setRoles(data.map((r: Role) => ({ id: r.id, name: r.name })))
    }
  }, [apiFetch])

  useEffect(() => {
    if (token) { fetchUsers(); fetchRoles() }
  }, [token, fetchUsers, fetchRoles])

  // ── Actions ───────────────────────────────────────────────────────────────
  const toggleActive = async (user: AdminUser) => {
    const path = user.is_active
      ? `/api/admin/users/${user.id}/deactivate`
      : `/api/admin/users/${user.id}/activate`
    const res = await apiFetch(path, { method: 'PATCH' })
    if (res?.ok) { showToast((await res.json()).message); fetchUsers() }
    else showToast((await res?.json())?.detail || 'Failed', 'error')
  }

  const resetPassword = async (user: AdminUser) => {
    if (!window.confirm(
      `Reset password for "${user.username}"?\nA new temporary password will be emailed to ${user.email}.`
    )) return
    const res = await apiFetch(`/api/admin/users/${user.id}/reset-password`, { method: 'POST' })
    if (res?.ok) {
      const d = await res.json()
      setResetResult({ username: user.username, password: d.temp_password, email: user.email })
    } else showToast((await res?.json())?.detail || 'Reset failed', 'error')
  }

  const deleteUser = async (user: AdminUser) => {
    if (!window.confirm(`Permanently delete "${user.username}"?\n\nThis cannot be undone.`)) return
    const res = await apiFetch(`/api/admin/users/${user.id}`, { method: 'DELETE' })
    if (res?.status === 204) { showToast(`Deleted "${user.username}"`); fetchUsers() }
    else showToast((await res?.json())?.detail || 'Delete failed', 'error')
  }

  const verifyEmail = async (userId: number) => {
    const res = await apiFetch(`/api/admin/users/${userId}/verify-email`, { method: 'PATCH' })
    if (res?.ok) { showToast('Email verified'); fetchUsers() }
  }

  const verifyPhone = async (userId: number) => {
    const res = await apiFetch(`/api/admin/users/${userId}/verify-phone`, { method: 'PATCH' })
    if (res?.ok) { showToast('Phone verified'); fetchUsers() }
  }

  // ── Edit ──────────────────────────────────────────────────────────────────
  const openEdit = (user: AdminUser) => {
    setEditUser(user)
    setEditForm({
      first_name: user.first_name, last_name: user.last_name,
      email: user.email, phone: user.phone,
      gotram: '',
      birth_city: user.birth_city || '', birth_state: user.birth_state || '',
      birth_country: user.birth_country || '',
      current_city: user.current_city || '', current_state: user.current_state || '',
      current_country: user.current_country || '',
      preferred_language: user.preferred_language,
      is_active: user.is_active, is_admin: user.is_admin,
      email_verified: user.email_verified, phone_verified: user.phone_verified,
    })
  }

  const saveEdit = async () => {
    if (!editUser) return
    setSaving(true)
    const res = await apiFetch(`/api/admin/users/${editUser.id}/update`, {
      method: 'PATCH', body: JSON.stringify(editForm),
    })
    setSaving(false)
    if (res?.ok) { showToast('User updated'); setEditUser(null); fetchUsers() }
    else showToast((await res?.json())?.detail || 'Update failed', 'error')
  }

  // ── Create ────────────────────────────────────────────────────────────────
  const submitCreate = async () => {
    if (!createForm.username || !createForm.password || !createForm.email ||
        !createForm.phone || !createForm.first_name || !createForm.last_name) {
      showToast('Please fill in all required fields (*)', 'error')
      return
    }
    setSaving(true)
    const res = await apiFetch('/api/admin/users', {
      method: 'POST', body: JSON.stringify(createForm),
    })
    setSaving(false)
    if (res?.ok) {
      showToast(`User "${createForm.username}" created`)
      setShowCreate(false)
      setCreateForm({ ...EMPTY_CREATE })
      fetchUsers()
    } else showToast((await res?.json())?.detail || 'Create failed', 'error')
  }

  // ── Role assignment ───────────────────────────────────────────────────────
  const assignRole = async () => {
    if (!assigningUser || !assignRoleId) return
    const res = await apiFetch(`/api/admin/users/${assigningUser.id}/assign-role`, {
      method: 'PATCH', body: JSON.stringify({ role_id: assignRoleId }),
    })
    if (res?.ok) {
      showToast((await res.json()).message)
      setAssigningUser(null); setAssignRoleId('')
      fetchUsers()
    } else showToast((await res?.json())?.detail || 'Failed', 'error')
  }

  const removeRole = async (userId: number, roleName: string) => {
    const role = roles.find(r => r.name === roleName)
    if (!role) return
    const res = await apiFetch(`/api/admin/users/${userId}/roles/${role.id}`, { method: 'DELETE' })
    if (res?.status === 204) { showToast('Role removed'); fetchUsers() }
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="relative">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 rounded-lg px-5 py-3 shadow-lg text-white text-sm font-medium ${toast.type === 'error' ? 'bg-red-600' : 'bg-emerald-600'}`}>
          {toast.msg}
        </div>
      )}

      {/* Header row */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div className="flex flex-wrap gap-2 text-sm items-center">
          {showAdmins ? (
            <span className="inline-flex items-center gap-1.5 bg-purple-50 text-purple-700 border border-purple-200 px-3 py-1.5 rounded-lg text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-purple-500 inline-block" />
              Admin Users Only
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 bg-blue-50 text-blue-700 border border-blue-200 px-3 py-1.5 rounded-lg text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
              Frontend Users Only
            </span>
          )}
          <span className="bg-white px-3 py-1.5 rounded-lg border border-slate-100 shadow-sm text-slate-600">
            <span className="font-semibold text-slate-800">{users.length}</span> shown
          </span>
          <span className="bg-green-50 px-3 py-1.5 rounded-lg border border-green-100 text-green-700">
            <span className="font-semibold">{users.filter(u => u.is_active).length}</span> active
          </span>
          <span className="bg-red-50 px-3 py-1.5 rounded-lg border border-red-100 text-red-600">
            <span className="font-semibold">{users.filter(u => !u.is_active).length}</span> inactive
          </span>
          <span className="bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-100 text-amber-700 hidden sm:inline-flex">
            <span className="font-semibold">{users.filter(u => !u.email_verified || !u.phone_verified).length}</span> unverified
          </span>
        </div>
        <button
          onClick={() => {
            setCreateForm({ ...EMPTY_CREATE, is_admin: showAdmins, auto_verify: true })
            setShowCreate(true)
          }}
          className="flex items-center gap-1.5 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-semibold shadow-sm"
        >
          <span className="text-base leading-none">+</span> {showAdmins ? 'New Admin' : 'New User'}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-3 mb-4 flex flex-wrap gap-2 items-end">
        <input
          type="text"
          placeholder="Search username, email, name…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { setPage(0); fetchUsers() } }}
          className="flex-1 min-w-[180px] border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300"
        />
        <select
          value={filterActive}
          onChange={e => { setFilterActive(e.target.value as 'all' | 'active' | 'inactive'); setPage(0) }}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <button
          onClick={() => { setPage(0); fetchUsers() }}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium"
        >
          Search
        </button>
        <button
          onClick={() => { setSearch(''); setFilterActive('all'); setPage(0) }}
          className="px-3 py-2 border border-slate-300 text-slate-600 rounded-lg text-sm hover:bg-slate-50"
        >
          Clear
        </button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-16 text-slate-400">
          <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-orange-600 mr-3" />
          Loading users…
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Contact</th>
                  <th className="px-4 py-3">Location</th>
                  <th className="px-4 py-3">Verified</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Admin Roles</th>
                  <th className="px-4 py-3">Joined</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {users.map(user => (
                  <tr key={user.id} className="hover:bg-orange-50/30 transition-colors">
                    {/* User */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-full bg-orange-100 text-orange-700 flex items-center justify-center text-xs font-bold shrink-0">
                          {user.first_name[0]}{user.last_name[0]}
                        </div>
                        <div>
                          <p className="font-semibold text-slate-800 leading-tight">{user.username}</p>
                          <p className="text-slate-500 text-xs">{user.first_name} {user.last_name}</p>
                        </div>
                      </div>
                    </td>
                    {/* Contact */}
                    <td className="px-4 py-3">
                      <p className="text-slate-700 text-xs">{user.email}</p>
                      <p className="text-slate-500 text-xs">{user.phone}</p>
                    </td>
                    {/* Location */}
                    <td className="px-4 py-3 text-xs text-slate-500 max-w-[130px]">
                      {[
                        user.current_city  || user.birth_city,
                        user.current_state || user.birth_state,
                        user.current_country || user.birth_country,
                      ].filter(Boolean).join(', ') || '—'}
                    </td>
                    {/* Verified */}
                    <td className="px-4 py-3">
                      <div className="space-y-1">
                        {user.email_verified
                          ? <span className="block text-xs text-green-600 font-medium">✓ Email</span>
                          : <button onClick={() => verifyEmail(user.id)} className="block text-xs text-red-500 hover:text-red-700 underline text-left">✗ Verify Email</button>
                        }
                        {user.phone_verified
                          ? <span className="block text-xs text-green-600 font-medium">✓ Phone</span>
                          : <button onClick={() => verifyPhone(user.id)} className="block text-xs text-red-500 hover:text-red-700 underline text-left">✗ Verify Phone</button>
                        }
                      </div>
                    </td>
                    {/* Status */}
                    <td className="px-4 py-3">
                      <button
                        onClick={() => toggleActive(user)}
                        title="Click to toggle active/inactive"
                        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold cursor-pointer transition ${
                          user.is_active
                            ? 'bg-green-100 text-green-700 hover:bg-green-200'
                            : 'bg-red-100 text-red-600 hover:bg-red-200'
                        }`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-green-500' : 'bg-red-500'}`} />
                        {user.is_active ? 'Active' : 'Inactive'}
                      </button>
                      {user.is_admin && (
                        <span className="block mt-1 text-xs bg-purple-100 text-purple-700 rounded-full px-2 py-0.5 w-fit font-medium">Admin</span>
                      )}
                    </td>
                    {/* Roles */}
                    <td className="px-4 py-3 max-w-[160px]">
                      <div className="flex flex-wrap gap-1">
                        {user.assigned_roles.length === 0
                          ? <span className="text-xs text-slate-400 italic">—</span>
                          : user.assigned_roles.map(rn => (
                              <span key={rn} className="inline-flex items-center gap-0.5 text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full">
                                {rn}
                                <button onClick={() => removeRole(user.id, rn)} className="text-blue-400 hover:text-red-500 font-bold ml-0.5 leading-none">&times;</button>
                              </span>
                            ))
                        }
                      </div>
                      {user.is_admin && (
                        <button
                          onClick={() => { setAssigningUser(user); setAssignRoleId('') }}
                          className="text-xs text-orange-500 hover:underline mt-1"
                        >
                          + assign role
                        </button>
                      )}
                    </td>
                    {/* Joined */}
                    <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    {/* Actions */}
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1 flex-wrap">
                        <button onClick={() => setDetailUser(user)}
                          className="px-2 py-1.5 text-xs rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium">
                          View
                        </button>
                        <button onClick={() => openEdit(user)}
                          className="px-2 py-1.5 text-xs rounded-md bg-blue-100 hover:bg-blue-200 text-blue-700 font-medium">
                          Edit
                        </button>
                        <button onClick={() => resetPassword(user)}
                          className="px-2 py-1.5 text-xs rounded-md bg-amber-100 hover:bg-amber-200 text-amber-700 font-medium">
                          Reset Pwd
                        </button>
                        <button onClick={() => deleteUser(user)}
                          className="px-2 py-1.5 text-xs rounded-md bg-red-100 hover:bg-red-200 text-red-700 font-medium">
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && !loading && (
                  <tr>
                    <td colSpan={8} className="py-16 text-center text-slate-400">
                      <p className="text-4xl mb-3">👥</p>
                      <p className="font-medium">No users found</p>
                      <p className="text-sm mt-1">Try adjusting your search or filters</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {(users.length === PAGE_SIZE || page > 0) && (
            <div className="px-4 py-3 border-t border-slate-100 flex items-center justify-between text-sm">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-3 py-1.5 border border-slate-300 rounded-md text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                ← Previous
              </button>
              <span className="text-slate-500 text-xs">Page {page + 1}</span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={users.length < PAGE_SIZE}
                className="px-3 py-1.5 border border-slate-300 rounded-md text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next →
              </button>
            </div>
          )}
        </div>
      )}

      {/* ── View Details Modal ─────────────────────────────────────────────── */}
      {detailUser && (
        <Modal title="User Details" onClose={() => setDetailUser(null)}>
          <div className="space-y-0 text-sm divide-y divide-slate-50">
            {([
              ['ID',               String(detailUser.id)],
              ['Username',         detailUser.username],
              ['Full Name',        `${detailUser.first_name} ${detailUser.last_name}`],
              ['Email',            detailUser.email],
              ['Phone',            detailUser.phone],
              ['Language',         detailUser.preferred_language],
              ['Birth Place',      [detailUser.birth_city, detailUser.birth_state, detailUser.birth_country].filter(Boolean).join(', ')],
              ['Current Location', [detailUser.current_city, detailUser.current_state, detailUser.current_country].filter(Boolean).join(', ')],
              ['Email Verified',   detailUser.email_verified ? '✓ Yes' : '✗ No'],
              ['Phone Verified',   detailUser.phone_verified ? '✓ Yes' : '✗ No'],
              ['Account Active',   detailUser.is_active ? '✓ Yes' : '✗ No'],
              ['Admin Access',     detailUser.is_admin ? '✓ Yes' : 'No'],
              ['Admin Roles',      detailUser.assigned_roles.join(', ') || '—'],
              ['Member Since',     new Date(detailUser.created_at).toLocaleString()],
            ] as [string, string][]).map(([label, value]) => (
              <div key={label} className="flex gap-2 py-2">
                <span className="w-36 shrink-0 font-medium text-slate-500 text-xs uppercase tracking-wide">{label}</span>
                <span className="text-slate-800 text-sm font-medium">{value || '—'}</span>
              </div>
            ))}
          </div>
          <div className="mt-5 flex gap-2">
            <button
              onClick={() => { setDetailUser(null); openEdit(detailUser) }}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 text-sm font-semibold"
            >
              Edit User
            </button>
            <button
              onClick={() => setDetailUser(null)}
              className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg py-2 text-sm font-medium"
            >
              Close
            </button>
          </div>
        </Modal>
      )}

      {/* ── Edit User Modal ────────────────────────────────────────────────── */}
      {editUser && (
        <Modal title={`Edit — ${editUser.username}`} onClose={() => setEditUser(null)} wide>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            {([
              ['first_name',    'First Name',    'text'],
              ['last_name',     'Last Name',     'text'],
              ['email',         'Email',         'email'],
              ['phone',         'Phone',         'text'],
              ['birth_city',    'Birth City',    'text'],
              ['birth_state',   'Birth State',   'text'],
              ['birth_country', 'Birth Country', 'text'],
              ['birth_date',    'Birth Date',    'date'],
              ['current_city',    'Current City',    'text'],
              ['current_state',   'Current State',   'text'],
              ['current_country', 'Current Country', 'text'],
            ] as [string, string, string][]).map(([key, label, type]) => (
              <div key={key}>
                <label className="block text-xs text-slate-500 font-medium mb-1">{label}</label>
                <input
                  type={type}
                  value={String(editForm[key] ?? '')}
                  onChange={e => setEditForm(p => ({ ...p, [key]: e.target.value }))}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300"
                />
              </div>
            ))}
            <div>
              <label className="block text-xs text-slate-500 font-medium mb-1">Language</label>
              <select
                value={String(editForm.preferred_language ?? '')}
                onChange={e => setEditForm(p => ({ ...p, preferred_language: e.target.value }))}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none"
              >
                {LANGUAGES.map(l => (
                  <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {([
              ['is_active',      'Account Active'],
              ['is_admin',       'Admin Access'],
              ['email_verified', 'Email Verified'],
              ['phone_verified', 'Phone Verified'],
            ] as [string, string][]).map(([key, label]) => (
              <label
                key={key}
                className={`flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer select-none text-sm transition ${
                  editForm[key]
                    ? 'border-orange-300 bg-orange-50 text-orange-800'
                    : 'border-slate-200 hover:bg-slate-50 text-slate-600'
                }`}
              >
                <input
                  type="checkbox"
                  checked={Boolean(editForm[key])}
                  onChange={e => setEditForm(p => ({ ...p, [key]: e.target.checked }))}
                  className="accent-orange-600"
                />
                {label}
              </label>
            ))}
          </div>

          <div className="mt-5 flex gap-2">
            <button
              onClick={saveEdit}
              disabled={saving}
              className="flex-1 bg-orange-600 hover:bg-orange-700 disabled:opacity-60 text-white rounded-lg py-2 text-sm font-semibold"
            >
              {saving ? 'Saving…' : 'Save Changes'}
            </button>
            <button
              onClick={() => setEditUser(null)}
              className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg py-2 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </Modal>
      )}

      {/* ── Create User Modal ──────────────────────────────────────────────── */}
      {showCreate && (
        <Modal title={showAdmins ? 'Create New Admin Account' : 'Create New User'} onClose={() => setShowCreate(false)} wide>
          <div className="space-y-5">
            {/* Credentials */}
            <div>
              <p className="text-xs font-semibold text-orange-600 uppercase tracking-wide mb-3">Account Credentials</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {([
                  ['username',   'Username *',  'text'],
                  ['password',   'Password *',  'password'],
                  ['email',      'Email *',     'email'],
                  ['phone',      'Phone *',     'tel'],
                ] as [keyof typeof createForm, string, string][]).map(([key, label, type]) => (
                  <div key={key}>
                    <label className="block text-xs text-slate-500 font-medium mb-1">{label}</label>
                    <input
                      type={type}
                      value={String(createForm[key])}
                      onChange={e => setCreateForm(p => ({ ...p, [key]: e.target.value }))}
                      className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Personal */}
            <div className="border-t border-slate-100 pt-4">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Personal Information</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {([
                  ['first_name',    'First Name *', 'text'],
                  ['last_name',     'Last Name *',  'text'],
                  ['gotram',        'Gotram',        'text'],
                  ['birth_date',    'Birth Date',   'date'],
                  ['birth_time',    'Birth Time',   'text'],
                  ['birth_city',    'Birth City',   'text'],
                  ['birth_state',   'Birth State',  'text'],
                  ['birth_country', 'Birth Country','text'],
                ] as [keyof typeof createForm, string, string][]).map(([key, label, type]) => (
                  <div key={key}>
                    <label className="block text-xs text-slate-500 font-medium mb-1">{label}</label>
                    <input
                      type={type}
                      value={String(createForm[key])}
                      onChange={e => setCreateForm(p => ({ ...p, [key]: e.target.value }))}
                      className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300"
                    />
                  </div>
                ))}
                <div>
                  <label className="block text-xs text-slate-500 font-medium mb-1">Language</label>
                  <select
                    value={createForm.preferred_language}
                    onChange={e => setCreateForm(p => ({ ...p, preferred_language: e.target.value }))}
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none"
                  >
                    {LANGUAGES.map(l => (
                      <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Settings */}
            <div className="border-t border-slate-100 pt-4">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Account Settings</p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {([
                  ['is_active', 'Account Active'],
                  ['is_admin',  'Admin Access'],
                  ['auto_verify', 'Skip Email/Phone Verification'],
                ] as [keyof typeof createForm, string][]).map(([key, label]) => (
                  <label
                    key={key}
                    className={`flex items-center gap-2 rounded-lg border px-3 py-2.5 cursor-pointer select-none text-xs transition ${
                      createForm[key]
                        ? 'border-orange-300 bg-orange-50 text-orange-800'
                        : 'border-slate-200 hover:bg-slate-50 text-slate-600'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={Boolean(createForm[key])}
                      onChange={e => setCreateForm(p => ({ ...p, [key]: e.target.checked }))}
                      className="accent-orange-600"
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6 flex gap-2">
            <button
              onClick={submitCreate}
              disabled={saving}
              className="flex-1 bg-orange-600 hover:bg-orange-700 disabled:opacity-60 text-white rounded-lg py-2.5 text-sm font-semibold"
            >
              {saving ? 'Creating…' : showAdmins ? 'Create Admin' : 'Create User'}
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg py-2.5 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </Modal>
      )}

      {/* ── Password Reset Result Modal ────────────────────────────────────── */}
      {resetResult && (
        <Modal title="Password Reset Successful" onClose={() => setResetResult(null)}>
          <div className="text-center mb-4">
            <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-3 text-3xl">🔑</div>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex gap-2 py-1 border-b border-slate-100">
              <span className="w-28 text-slate-500 font-medium shrink-0">Username</span>
              <span className="font-bold text-slate-800">{resetResult.username}</span>
            </div>
            <div className="flex gap-2 py-1 border-b border-slate-100">
              <span className="w-28 text-slate-500 font-medium shrink-0">Emailed To</span>
              <span>{resetResult.email}</span>
            </div>
            <div>
              <p className="text-slate-500 font-medium text-xs uppercase tracking-wide mb-2">Temporary Password</p>
              <div className="bg-slate-900 text-green-400 font-mono text-xl tracking-widest px-4 py-4 rounded-xl text-center select-all">
                {resetResult.password}
              </div>
            </div>
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 p-3 rounded-lg">
              An email has been sent. Ask the user to change this password immediately after logging in.
            </p>
          </div>
          <button
            onClick={() => setResetResult(null)}
            className="mt-5 w-full bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg py-2 text-sm font-medium"
          >
            Close
          </button>
        </Modal>
      )}

      {/* ── Assign Role Modal ──────────────────────────────────────────────── */}
      {assigningUser && (
        <Modal title={`Assign Role — ${assigningUser.username}`} onClose={() => setAssigningUser(null)}>
          <select
            value={assignRoleId}
            onChange={e => setAssignRoleId(Number(e.target.value) || '')}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300 mb-4"
          >
            <option value="">— Select a role —</option>
            {roles
              .filter(r => !assigningUser.assigned_roles.includes(r.name))
              .map(r => <option key={r.id} value={r.id}>{r.name}</option>)
            }
          </select>
          <div className="flex gap-2">
            <button
              onClick={assignRole}
              disabled={!assignRoleId}
              className="flex-1 bg-orange-600 hover:bg-orange-700 disabled:opacity-50 text-white rounded-lg py-2 text-sm font-semibold"
            >
              Assign
            </button>
            <button
              onClick={() => setAssigningUser(null)}
              className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg py-2 text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </Modal>
      )}
    </div>
  )
}
