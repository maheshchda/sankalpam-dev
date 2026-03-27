'use client'

import { Suspense, useMemo } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import { PoojaPageContent } from '../PoojaPageContent'

/**
 * One pooja per URL (e.g. from /pooja-calendar).
 * Use `useParams()` so the slug is always available in a Client Component (the `params`
 * prop is not reliably populated for client pages in some Next.js 14 setups).
 *
 * `useSearchParams()` must run inside a Suspense boundary or query strings like
 * `?from=calendar` are often empty — so "Go Back" to Pooja Calendar would not show.
 */
function PoojaByCalendarSlugInner() {
  const params = useParams()
  const searchParams = useSearchParams()
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

  const fromCalendar = searchParams.get('from') === 'calendar'

  return <PoojaPageContent filterPoojaSlug={filterSlug} fromCalendar={fromCalendar} />
}

export default function PoojaByCalendarSlugPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-100">
          Loading...
        </div>
      }
    >
      <PoojaByCalendarSlugInner />
    </Suspense>
  )
}
