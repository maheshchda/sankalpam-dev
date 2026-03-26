'use client'

import type { ReactNode } from 'react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type ColumnMeta = {
  name: string
  sql_type: string
  is_primary_key: boolean
  is_editable: boolean
}

type TableMeta = {
  table: string
  primary_key: string[]
  columns: ColumnMeta[]
}

type RowsResponse = {
  table: string
  primary_key: string[]
  offset: number
  limit: number
  rows: Array<Record<string, any>>
}

function Modal({
  title,
  onClose,
  children,
  wide,
}: {
  title: string
  onClose: () => void
  children: React.ReactNode
  wide?: boolean
}) {
  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className={`bg-white rounded-2xl shadow-2xl w-full my-10 p-6 ${wide ? 'max-w-5xl' : 'max-w-2xl'}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-slate-800">{title}</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 text-2xl leading-none"
            aria-label="Close"
            type="button"
          >
            &times;
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

function safeString(v: any) {
  if (v === null || v === undefined) return ''
  if (typeof v === 'string') return v
  try {
    return JSON.stringify(v)
  } catch {
    return String(v)
  }
}

export default function DatabaseExplorerPanel() {
  const router = useRouter()
  const [token, setToken] = useState<string | null>(null)

  const PAGE_LIMIT = 20

  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)
  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ msg, type })
    window.setTimeout(() => setToast(null), 3500)
  }

  const [tables, setTables] = useState<string[]>([])
  const [tablesLoading, setTablesLoading] = useState(false)

  const [selectedTable, setSelectedTable] = useState<string>('')
  const [meta, setMeta] = useState<TableMeta | null>(null)

  const [rows, setRows] = useState<Array<Record<string, any>>>([])
  const [rowsLoading, setRowsLoading] = useState(false)
  const [offset, setOffset] = useState(0)

  const [editPk, setEditPk] = useState<Record<string, any> | null>(null)
  const [editDraft, setEditDraft] = useState<Record<string, string>>({})
  const [editFullRow, setEditFullRow] = useState<Record<string, any> | null>(null)
  const [editSaving, setEditSaving] = useState(false)
  const [editing, setEditing] = useState(false)

  const apiFetch = useCallback(
    async (path: string, opts: RequestInit = {}) => {
      if (!token) return null
      const res = await fetch(`${API}${path}`, {
        ...opts,
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...(opts.headers as Record<string, string> | undefined),
        },
      })
      if (res.status === 401 || res.status === 403) {
        localStorage.removeItem('admin_token')
        localStorage.removeItem('admin_username')
        router.replace('/admin/login')
        return null
      }
      return res
    },
    [token, router],
  )

  const fetchTables = useCallback(async () => {
    setTablesLoading(true)
    try {
      const res = await apiFetch('/api/admin/db/tables')
      if (!res?.ok) return
      const data = await res.json()
      setTables(Array.isArray(data?.tables) ? data.tables : [])
    } catch (e) {
      showToast('Failed to load tables', 'error')
    } finally {
      setTablesLoading(false)
    }
  }, [apiFetch])

  const fetchMeta = useCallback(
    async (tableName: string) => {
      const res = await apiFetch(`/api/admin/db/tables/${encodeURIComponent(tableName)}/meta`)
      if (!res?.ok) throw new Error('meta fetch failed')
      const data = await res.json()
      setMeta(data)
      setOffset(0)
    },
    [apiFetch],
  )

  const fetchRows = useCallback(
    async (tableName: string, nextOffset: number) => {
      setRowsLoading(true)
      try {
        const res = await apiFetch(
          `/api/admin/db/tables/${encodeURIComponent(tableName)}/rows?limit=${PAGE_LIMIT}&offset=${nextOffset}&max_cell_length=250`,
        )
        if (!res?.ok) return
        const data: RowsResponse = await res.json()
        setRows(Array.isArray(data?.rows) ? data.rows : [])
      } finally {
        setRowsLoading(false)
      }
    },
    [apiFetch],
  )

  useEffect(() => {
    const t = localStorage.getItem('admin_token')
    if (!t) {
      router.replace('/admin/login')
      return
    }
    setToken(t)
  }, [router])

  useEffect(() => {
    if (!token) return
    fetchTables().catch(() => {})
  }, [token, fetchTables])

  useEffect(() => {
    if (!tables.length) return
    if (!selectedTable) setSelectedTable(tables[0])
  }, [tables, selectedTable])

  useEffect(() => {
    if (!selectedTable || !token) return
    setMeta(null)
    fetchMeta(selectedTable)
      .then(() => fetchRows(selectedTable, 0))
      .catch(() => showToast('Failed to load table meta/rows', 'error'))
  }, [selectedTable, token, fetchMeta, fetchRows])

  const selectedColumns = useMemo(() => meta?.columns ?? [], [meta])
  const pkCols = meta?.primary_key ?? []

  const openEdit = async (row: Record<string, any>) => {
    if (!meta) return
    const pk: Record<string, any> = {}
    pkCols.forEach((k) => (pk[k] = row[k]))
    setEditPk(pk)
    setEditing(true)
    setEditSaving(false)
    setEditFullRow(row)
    const res = await apiFetch(
      `/api/admin/db/tables/${encodeURIComponent(selectedTable)}/row`,
      {
        method: 'POST',
        body: JSON.stringify({ pk }),
      },
    )
    if (!res?.ok) {
      showToast('Failed to load full row', 'error')
      setEditing(false)
      return
    }
    const data = await res.json()
    setEditFullRow(data?.values ?? null)
    const draft: Record<string, string> = {}
    const values = data?.values ?? {}
    meta.columns.forEach((c) => {
      if (c.is_primary_key) return
      if (!c.is_editable) return
      draft[c.name] = safeString(values[c.name])
    })
    setEditDraft(draft)
  }

  const saveEdit = async () => {
    if (!meta || !editPk) return
    setEditSaving(true)
    try {
      const values: Record<string, any> = {}
      Object.entries(editDraft).forEach(([k, v]) => {
        values[k] = v
      })
      const res = await apiFetch(
        `/api/admin/db/tables/${encodeURIComponent(selectedTable)}/row`,
        {
          method: 'PATCH',
          body: JSON.stringify({ pk: editPk, values }),
        },
      )
      if (!res?.ok) {
        const err = await res?.json().catch(() => null)
        showToast(err?.detail || 'Update failed', 'error')
        return
      }
      showToast('Row updated')
      setEditing(false)
      setEditPk(null)
      setEditDraft({})
      setEditFullRow(null)
      await fetchRows(selectedTable, offset)
    } finally {
      setEditSaving(false)
    }
  }

  const deleteRow = async (row: Record<string, any>) => {
    if (!meta) return
    const pk: Record<string, any> = {}
    pkCols.forEach((k) => (pk[k] = row[k]))
    const ok = window.confirm(`Delete row from "${selectedTable}"?\n\nPK: ${JSON.stringify(pk, null, 2)}`)
    if (!ok) return
    const res = await apiFetch(
      `/api/admin/db/tables/${encodeURIComponent(selectedTable)}/row/delete`,
      {
        method: 'POST',
        body: JSON.stringify({ pk }),
      },
    )
    if (!res?.ok) {
      const err = await res?.json().catch(() => null)
      showToast(err?.detail || 'Delete failed', 'error')
      return
    }
    showToast('Row deleted')
    // After delete, it’s safe to refetch current page (offset stays).
    await fetchRows(selectedTable, offset)
  }

  const canPagePrev = offset > 0

  return (
    <div className="relative">
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 rounded-lg px-5 py-3 shadow-lg text-white text-sm font-medium ${
            toast.type === 'error' ? 'bg-red-600' : 'bg-emerald-600'
          }`}
        >
          {toast.msg}
        </div>
      )}

      <div className="mb-5 flex items-end gap-3 flex-wrap">
        <div className="flex-1 min-w-[240px]">
          <label className="block text-sm font-medium text-slate-700 mb-2">Table</label>
          <select
            value={selectedTable}
            onChange={(e) => setSelectedTable(e.target.value)}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-orange-300"
            disabled={tablesLoading}
          >
            {tables.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => fetchTables()}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium"
            disabled={!token}
          >
            Refresh tables
          </button>
        </div>
      </div>

      {!meta ? (
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-8">
          <p className="text-slate-500">Select a table to view rows.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between flex-wrap gap-3">
            <div className="min-w-[220px]">
              <div className="text-slate-900 font-semibold">{meta.table}</div>
              <div className="text-xs text-slate-500">
                PK: {meta.primary_key.length ? meta.primary_key.join(', ') : '—'}
              </div>
            </div>
            <div className="flex gap-2 items-center flex-wrap">
              <button
                type="button"
                className="px-3 py-1.5 border border-slate-300 rounded-md text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
                disabled={!canPagePrev || rowsLoading}
                onClick={() => {
                  if (!selectedTable) return
                  const prev = Math.max(0, offset - PAGE_LIMIT)
                  setOffset(prev)
                  fetchRows(selectedTable, prev)
                }}
              >
                ← Prev
              </button>
              <span className="text-xs text-slate-500">Offset: {offset}</span>
              <button
                type="button"
                className="px-3 py-1.5 border border-slate-300 rounded-md text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
                disabled={rowsLoading || rows.length < PAGE_LIMIT}
                onClick={() => {
                  if (!selectedTable) return
                  const next = offset + PAGE_LIMIT
                  setOffset(next)
                  fetchRows(selectedTable, next)
                }}
              >
                Next →
              </button>
            </div>
          </div>

          {rowsLoading ? (
            <div className="flex items-center justify-center py-16 text-slate-400">
              Loading rows…
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    {selectedColumns.map((c) => (
                      <th key={c.name} className="px-4 py-3 whitespace-nowrap">
                        {c.name}
                      </th>
                    ))}
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {rows.map((row, idx) => {
                    const pkLabel = pkCols.map((k) => `${k}=${safeString(row[k])}`).join(', ')
                    return (
                      <tr key={`${pkLabel}-${idx}`} className="hover:bg-orange-50/30 transition-colors">
                        {selectedColumns.map((c) => (
                          <td key={c.name} className="px-4 py-3 whitespace-nowrap max-w-[420px]">
                            <span className="text-xs text-slate-800">
                              {safeString(row[c.name])}
                            </span>
                          </td>
                        ))}
                        <td className="px-4 py-3 text-right whitespace-nowrap">
                          <div className="flex justify-end gap-2 flex-wrap">
                            <button
                              type="button"
                              onClick={() => openEdit(row)}
                              className="px-2 py-1 text-xs rounded bg-blue-100 hover:bg-blue-200 text-blue-700 font-medium"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => deleteRow(row)}
                              className="px-2 py-1 text-xs rounded bg-red-100 hover:bg-red-200 text-red-700 font-medium"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                  {!rows.length && (
                    <tr>
                      <td className="py-16 text-center text-slate-400" colSpan={selectedColumns.length + 1}>
                        No rows found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {editing && meta && editPk && (
        <Modal title={`Edit — ${selectedTable}`} onClose={() => setEditing(false)} wide>
          <div className="mb-4">
            <div className="text-xs text-slate-500">
              PK: {pkCols.map((k) => `${k}=${safeString(editPk[k])}`).join(', ')}
            </div>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {meta.columns
                .filter((c) => !c.is_primary_key && c.is_editable)
                .map((c) => (
                  <div key={c.name}>
                    <label className="block text-xs text-slate-500 font-medium mb-1">{c.name}</label>
                    <textarea
                      value={editDraft[c.name] ?? ''}
                      onChange={(e) => setEditDraft((p) => ({ ...p, [c.name]: e.target.value }))}
                      rows={2}
                      className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-orange-300 font-mono"
                    />
                  </div>
                ))}
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={saveEdit}
                disabled={editSaving}
                className="flex-1 bg-orange-600 hover:bg-orange-700 disabled:opacity-60 text-white rounded-lg py-2 text-sm font-semibold"
              >
                {editSaving ? 'Saving…' : 'Save'}
              </button>
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg py-2 text-sm font-medium border border-slate-100"
              >
                Cancel
              </button>
            </div>

            <div className="text-xs text-slate-500">
              Note: token/password fields are blocked from editing for safety. Datetime/numeric fields accept ISO/text values.
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

