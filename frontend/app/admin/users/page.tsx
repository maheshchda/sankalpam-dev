'use client'

import AdminLayout from '@/components/admin/AdminLayout'
import UserManagementPanel from '@/components/admin/UserManagementPanel'

export default function AdminUsersPage() {
  return (
    <AdminLayout>
      <div className="mb-6">
        <h1 className="font-cinzel text-2xl font-bold text-sacred-800">User Management</h1>
        <p className="text-stone-500 text-sm mt-1">
          View, create, edit, and manage all frontend user accounts.
        </p>
      </div>
      <UserManagementPanel />
    </AdminLayout>
  )
}
