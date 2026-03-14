import axios from 'axios'

// Default to local backend on port 8000 unless overridden by env
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// Handle token expiration (don't redirect on login endpoint 401 so user sees error)
// Don't redirect if already on a public page — avoids recursive refresh on login/register
const PUBLIC_PATHS = ['/login', '/register', '/forgot-password', '/verify', '/admin/login', '/rsvp']
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      const isLoginRequest = error.config?.url?.includes('/api/auth/login')
      const pathname = window.location.pathname
      const isPublicPage = PUBLIC_PATHS.some(p => pathname === p || pathname.startsWith(p + '/'))
      if (!isLoginRequest && !isPublicPage) {
        localStorage.removeItem('access_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api

