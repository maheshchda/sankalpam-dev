import Link from 'next/link'

type Props = {
  params: { pooja: string }
  searchParams?: { from?: string }
}

function prettyName(slug: string): string {
  return (slug || '')
    .split('-')
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

export async function generateStaticParams() {
  return [
    { pooja: 'ganesha-pooja' },
    { pooja: 'diwali-lakshmi-pooja' },
    { pooja: 'maha-shivaratri' },
    { pooja: 'navaratri' },
    { pooja: 'purnima-pooja-satyanarayan-pooja' },
    { pooja: 'pradosha-shiva-pooja' },
    { pooja: 'ekadasi-shiva-pooja' },
    { pooja: 'ganesh-chaturthi' },
    { pooja: 'ugadi-gudi-padwa' },
    { pooja: 'makar-sankranti' },
  ]
}

export default function PoojaItemsPage({ params, searchParams }: Props) {
  const name = prettyName(params.pooja)
  const fromCalendar = searchParams?.from === 'calendar'

  return (
    <section className="min-h-[70vh] bg-gradient-to-b from-teal-50 to-cyan-100 px-4 py-12">
      <div className="mx-auto max-w-3xl rounded-xl bg-white p-8 shadow">
        {fromCalendar && (
          <div className="mb-6">
            <Link
              href="/pooja-calendar"
              className="inline-flex items-center rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-teal-800"
            >
              Go Back
            </Link>
          </div>
        )}
        <h1 className="text-2xl font-bold text-teal-800">Pooja Items List</h1>
        <p className="mt-3 text-gray-700">
          Placeholder items page for <span className="font-semibold">{name || 'selected pooja'}</span>. You can add the full items list later.
        </p>
        {!fromCalendar && (
          <div className="mt-6">
            <Link href="/pooja-calendar" className="rounded-md bg-teal-600 px-4 py-2 text-white hover:bg-teal-700">
              Back to Pooja Calendar
            </Link>
          </div>
        )}
      </div>
    </section>
  )
}
