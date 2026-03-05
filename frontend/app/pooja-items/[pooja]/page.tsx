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

export default function PoojaItemsPage({ params }: Props) {
  const name = prettyName(params.pooja)

  return (
    <section className="min-h-[70vh] bg-gradient-to-b from-teal-50 to-cyan-100 px-4 py-12">
      <div className="mx-auto max-w-3xl rounded-xl bg-white p-8 shadow">
        <h1 className="text-2xl font-bold text-teal-800">Pooja Items List</h1>
        <p className="mt-3 text-gray-700">
          Placeholder items page for <span className="font-semibold">{name || 'selected pooja'}</span>. You can add the full items list later.
        </p>
        <div className="mt-6">
          <Link href="/pooja-calendar" className="rounded-md bg-teal-600 px-4 py-2 text-white hover:bg-teal-700">
            Back to Pooja Calendar
          </Link>
        </div>
      </div>
    </section>
  )
}
