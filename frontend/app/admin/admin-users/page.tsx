'use client'

import AdminLayout from '@/components/admin/AdminLayout'
import UserManagementPanel from '@/components/admin/UserManagementPanel'

export default function AdminAdminUsersPage() {
  return (
    <AdminLayout>
      <div className="mb-6">
        <h1 className="font-cinzel text-2xl font-bold text-sacred-800">Admin Accounts</h1>
        <p className="text-stone-500 text-sm mt-1">
          Manage administrator accounts — create new admins, assign roles, and control access.
        </p>
      </div>
      <UserManagementPanel showAdmins />
    </AdminLayout>
  )
}
