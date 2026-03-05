import Link from 'next/link'

type Props = {
  params: { pooja: string }
}

function prettyName(slug: string): string {
  return (slug || '')
    .split('-')
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

export default function PoojaReadinessPage({ params }: Props) {
  const name = prettyName(params.pooja)

  return (
    <section className="min-h-[70vh] bg-gradient-to-b from-indigo-50 to-blue-100 px-4 py-12">
      <div className="mx-auto max-w-3xl rounded-xl bg-white p-8 shadow">
        <h1 className="text-2xl font-bold text-indigo-800">Pooja Readiness Info</h1>
        <p className="mt-3 text-gray-700">
          Placeholder page for <span className="font-semibold">{name || 'selected pooja'}</span>. You can add detailed readiness content later.
        </p>
        <div className="mt-6">
          <Link href="/pooja-calendar" className="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700">
            Back to Pooja Calendar
          </Link>
        </div>
      </div>
    </section>
  )
}
