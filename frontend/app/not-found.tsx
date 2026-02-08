import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">404</h2>
        <p className="text-xl text-gray-600 mb-4">Page Not Found</p>
        <p className="text-gray-500 mb-8">The page you're looking for doesn't exist.</p>
        <Link
          href="/"
          className="px-6 py-3 bg-amber-600 text-white rounded-md hover:bg-amber-700 inline-block"
        >
          Go Home
        </Link>
      </div>
    </div>
  )
}

