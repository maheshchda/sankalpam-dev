'use client'

import { useParams } from 'next/navigation'
import { useMemo } from 'react'
import { PoojaPageContent } from '../PoojaPageContent'

/**
 * One pooja per URL (e.g. from /pooja-calendar).
 * Use `useParams()` so the slug is always available in a Client Component (the `params`
 * prop is not reliably populated for client pages in some Next.js 14 setups).
 */
export default function PoojaByCalendarSlugPage() {
  const params = useParams()
  const filterSlug = useMemo(() => {
    const raw = params?.poojaSlug
    const segment = Array.isArray(raw) ? raw[0] : raw
    if (segment == null || segment === '') return null
    try {
      return decodeURIComponent(String(segment))
    } catch {
      return String(segment)
    }
  }, [params])

  return <PoojaPageContent filterPoojaSlug={filterSlug} />
}
