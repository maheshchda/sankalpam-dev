'use client'

import Link from 'next/link'

export default function RsvpError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom, #080202, #0f0404)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
    >
      <div style={{ textAlign: 'center', maxWidth: '28rem' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>😔</div>
        <h2 style={{ fontFamily: 'Georgia, serif', fontSize: '1.5rem', color: '#f0b429', marginBottom: '0.5rem' }}>
          Something went wrong
        </h2>
        <p style={{ color: '#edddc8', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
          We couldn&apos;t load your invitation. Please try again or contact your host.
        </p>
        <button
          onClick={reset}
          style={{
            background: '#d4a017',
            color: '#0f0404',
            padding: '0.5rem 1rem',
            borderRadius: '0.375rem',
            fontWeight: 600,
            border: 'none',
            cursor: 'pointer',
            marginRight: '0.5rem',
          }}
        >
          Try again
        </button>
        <Link
          href="/"
          style={{
            display: 'inline-block',
            background: '#d4a017',
            color: '#0f0404',
            padding: '0.5rem 1rem',
            borderRadius: '0.375rem',
            fontWeight: 600,
            textDecoration: 'none',
          }}
        >
          Go to Home
        </Link>
      </div>
    </div>
  )
}
