'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import api from './api'

interface User {
  id: number
  unique_id?: string
  username: string
  email: string
  first_name: string
  last_name: string
  gotram?: string
  birth_city?: string
  birth_state?: string
  birth_country?: string
  birth_time?: string
  birth_date?: string
  birth_nakshatra?: string
  birth_rashi?: string
  birth_pada?: string
  current_city?: string
  current_state?: string
  current_country?: string
  email_verified: boolean
  phone_verified: boolean
  is_active: boolean
  is_admin?: boolean
  preferred_language?: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<User | null>
  logout: () => void
  register: (data: any) => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    // Only check localStorage on client side
    if (typeof window === 'undefined') {
      setLoading(false)
      return
    }
    
    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        const response = await api.get('/api/auth/me')
        setUser(response.data)
      } catch (error) {
        localStorage.removeItem('access_token')
      }
    }
    setLoading(false)
  }

  const login = async (username: string, password: string) => {
    // Use URLSearchParams for form-urlencoded data (required by OAuth2PasswordRequestForm)
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    
    const response = await api.post('/api/auth/login', params.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.data.access_token)
    }
    // User is included in login response — no extra /me round trip
    const updatedUser = response.data.user
    setUser(updatedUser)
    return updatedUser
  }

  const register = async (data: any) => {
    await api.post('/api/auth/register', data)
  }

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
    }
    setUser(null)
  }

  const refreshUser = async () => {
    if (typeof window === 'undefined') {
      return
    }
    
    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        const response = await api.get('/api/auth/me')
        setUser(response.data)
      } catch (error) {
        // If refresh fails, user might be logged out
        console.error('Failed to refresh user:', error)
      }
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

