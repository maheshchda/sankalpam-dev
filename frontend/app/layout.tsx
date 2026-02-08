import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import 'react-toastify/dist/ReactToastify.css'
import { Providers } from './providers'
import ToastProvider from '../components/ToastProvider'
import ExtensionCompatibility from '../components/ExtensionCompatibility'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Sankalpam - Pooja Management',
  description: 'Comprehensive pooja management with personalized sankalpam generation',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <ExtensionCompatibility />
          {children}
          <ToastProvider />
        </Providers>
      </body>
    </html>
  )
}

