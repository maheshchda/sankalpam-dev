import Link from 'next/link'

const LINKS = [
  { label: 'About Us', href: '/about-us' },
  { label: 'About Sankalpam', href: '/about-sankalpam' },
  { label: 'Contact Us', href: '/contact-us' },
  { label: 'Privacy Policy', href: '/privacy-policy' },
]

export default function SiteFooter() {
  return (
    <footer className="sacred-footer">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-center sm:text-left">
            <p className="font-cinzel text-gold-400 font-semibold text-lg">Pooja Sankalpam</p>
            <p className="text-cream-300/60 text-sm mt-1">Sacred traditions, preserved with reverence.</p>
          </div>
          <nav className="flex flex-wrap justify-center gap-x-4 gap-y-2">
            {LINKS.map((item) => (
              <Link key={item.href} href={item.href} className="text-sm text-cream-300/70 hover:text-gold-400 transition-colors">
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="gold-divider mt-6 mb-4" />
        <p className="text-center text-xs text-cream-300/40">
          &copy; {new Date().getFullYear()} Pooja Sankalpam. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
