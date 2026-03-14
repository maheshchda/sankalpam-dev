import type { Metadata } from 'next'
import { Inter, Cinzel } from 'next/font/google'
import './globals.css'
import 'react-toastify/dist/ReactToastify.css'
import { Providers } from './providers'
import ToastProvider from '../components/ToastProvider'
import ExtensionCompatibility from '../components/ExtensionCompatibility'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const cinzel = Cinzel({ subsets: ['latin'], variable: '--font-cinzel', weight: ['400', '600', '700', '900'] })

export const metadata: Metadata = {
  title: 'Pooja Sankalpam',
  description: 'Comprehensive pooja management with personalized sankalpam generation',
  icons: {
    icon: '/icon',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${cinzel.variable} ${inter.className}`}>
        <Providers>
          <ExtensionCompatibility />
          {children}
          <ToastProvider />
        </Providers>
      </body>
    </html>
  )
}
