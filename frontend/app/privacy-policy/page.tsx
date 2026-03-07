import SiteHeader from '@/components/SiteHeader'
import SiteFooter from '@/components/SiteFooter'

export default function PrivacyPolicyPage() {
  return (
    <div className="page-bg flex flex-col">
      <SiteHeader />
      <main className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="sacred-card max-w-3xl w-full p-10 text-center">
          <h1 className="font-cinzel text-3xl font-bold text-sacred-800">Privacy Policy</h1>
          <div className="gold-divider mx-auto max-w-xs my-4" />
          <p className="text-stone-600">Placeholder page. You can add your privacy policy here.</p>
        </div>
      </main>
      <SiteFooter />
    </div>
  )
}
