'use client'

import AdminLayout from '@/components/admin/AdminLayout'
import DatabaseExplorerPanel from '@/components/admin/DatabaseExplorerPanel'

export default function DbTablesPage() {
  return (
    <AdminLayout>
      <div className="mb-6">
        <h1 className="font-cinzel text-2xl font-bold text-sacred-800">Database Explorer</h1>
        <p className="text-stone-500 text-sm mt-1">
          Browse tables/rows and update/delete rows using primary keys (admin-only).
        </p>
      </div>
      <DatabaseExplorerPanel />
    </AdminLayout>
  )
}

