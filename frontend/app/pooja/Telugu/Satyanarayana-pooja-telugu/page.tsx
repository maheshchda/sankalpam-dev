import Link from 'next/link'
import { PURNIMA_SATYANARAYANA_POOJA_SLUG } from '@/lib/poojaSlugs'

const readinessHref = `/pooja-readiness/${PURNIMA_SATYANARAYANA_POOJA_SLUG}`

export default function SatyanarayanaPoojaTeluguPage() {
  return (
    <div className="page-bg min-h-screen px-4 py-10">
      <div className="mx-auto max-w-2xl">
        <section
          className="sacred-card p-6 border border-cream-300"
          aria-labelledby="readiness-heading"
        >
          <h2 id="readiness-heading" className="font-cinzel text-lg font-semibold text-sacred-800">
            Readiness
          </h2>
          <p className="mt-2 text-sm text-stone-600">
            పౌర్ణిమ పూజ / సత్యనారాయణ పూజ — preparation and readiness details (same as Pooja Calendar →
            Readiness Info).
          </p>
          <div className="mt-4">
            <Link
              href={readinessHref}
              className="inline-flex items-center rounded-md bg-sacred-800 px-4 py-2 text-sm font-semibold text-gold-200 hover:bg-sacred-700 hover:text-gold-100"
            >
              Open readiness info
            </Link>
          </div>
        </section>
      </div>
    </div>
  )
}
