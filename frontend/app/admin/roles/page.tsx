'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function AdminRolesPage() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/admin/dashboard?tab=roles')
  }, [router])

  return (
    <div className="flex items-center justify-center min-h-[200px]">
      <p className="text-stone-500">Redirecting to dashboard…</p>
    </div>
  )
}
