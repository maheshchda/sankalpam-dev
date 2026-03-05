import Link from 'next/link'

export default function InvitationsPage() {
  return (
    <section className="min-h-[70vh] bg-gradient-to-b from-orange-50 to-amber-50 px-4 py-16">
      <div className="mx-auto max-w-3xl rounded-2xl bg-white p-10 text-center shadow-md">
        <h1 className="text-3xl font-bold text-orange-900">Invitations</h1>
        <p className="mt-3 text-slate-600">Coming soon. Invitation features will be available here.</p>
        <Link href="/" className="mt-6 inline-block rounded-md bg-orange-600 px-4 py-2 text-white hover:bg-orange-700">
          Back to Home
        </Link>
      </div>
    </section>
  )
}
