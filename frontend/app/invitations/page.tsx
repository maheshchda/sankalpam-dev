import Link from 'next/link'
import SiteHeader from '@/components/SiteHeader'
import SiteFooter from '@/components/SiteFooter'

export default function InvitationsPage() {
  return (
    <div className="page-bg flex flex-col">
      <SiteHeader />
      <main className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="sacred-card max-w-2xl w-full p-10 text-center">
          <h1 className="font-cinzel text-3xl font-bold text-sacred-800">Invitations</h1>
          <div className="gold-divider mx-auto max-w-xs my-4" />
          <p className="text-stone-600 mt-3">Coming soon. Invitation features will be available here.</p>
          <Link href="/" className="gold-btn inline-block mt-8">
            Back to Home
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  )
}
