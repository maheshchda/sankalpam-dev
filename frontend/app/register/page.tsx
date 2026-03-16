'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { toast } from 'react-toastify'
import Link from 'next/link'

const LANGUAGES = [
  { value: 'hindi', label: 'Hindi' },
  { value: 'telugu', label: 'Telugu' },
  { value: 'tamil', label: 'Tamil' },
  { value: 'kannada', label: 'Kannada' },
  { value: 'malayalam', label: 'Malayalam' },
  { value: 'sanskrit', label: 'Sanskrit' },
  { value: 'english', label: 'English' },
  { value: 'marathi', label: 'Marathi' },
  { value: 'gujarati', label: 'Gujarati' },
  { value: 'bengali', label: 'Bengali' },
  { value: 'oriya', label: 'Oriya' },
  { value: 'punjabi', label: 'Punjabi' },
]

const inputCls = 'mt-1 block w-full rounded-md border-cream-300 bg-white shadow-sm focus:border-gold-500 focus:ring-gold-500 focus:ring-1 text-stone-800'

export default function RegisterPage() {
  const router = useRouter()
  const { register, login } = useAuth()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    phone: '',
    first_name: '',
    last_name: '',
    gotram: '',
    birth_city: '',
    birth_state: '',
    birth_country: 'India',
    birth_date: '',
    birth_time: '',
    birth_nakshatra: '',
    birth_rashi: '',
    preferred_language: 'sanskrit',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await register(formData)
      toast.success('Registration successful!')
      try {
        const loggedInUser = await login(formData.username, formData.password)
        toast.success('Logged in successfully!')
        if (returnUrl && returnUrl.startsWith('/')) {
          router.push(returnUrl)
        } else if (loggedInUser?.is_admin) {
          router.push('/admin')
        } else {
          router.push('/dashboard')
        }
      } catch {
        toast.info('Registration successful. Please login.')
        router.push(returnUrl ? `/login?returnUrl=${encodeURIComponent(returnUrl)}` : '/login')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const sectionHeading = (text: string) => (
    <h3 className="font-cinzel text-lg font-semibold text-sacred-700 mb-4 flex items-center gap-2">
      <span className="inline-block h-0.5 w-6 bg-gold-500" />
      {text}
    </h3>
  )

  return (
    <div className="page-bg py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <div className="mx-auto h-14 w-14 rounded-full bg-sacred-800 flex items-center justify-center mb-3">
            <span className="font-cinzel text-gold-400 font-bold">PS</span>
          </div>
          <h2 className="font-cinzel text-3xl font-bold text-sacred-800">Create Your Account</h2>
          <p className="text-stone-500 mt-2">Join the Pooja Sankalpam community</p>
        </div>

        <div className="sacred-card p-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            <div>
              {sectionHeading('Account Information')}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Username *</label>
                  <input type="text" name="username" required autoComplete="username" suppressHydrationWarning className={inputCls} value={formData.username} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Password *</label>
                  <input type="password" name="password" required minLength={8} autoComplete="new-password" suppressHydrationWarning className={inputCls} value={formData.password} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Email *</label>
                  <input type="email" name="email" required autoComplete="email" suppressHydrationWarning className={inputCls} value={formData.email} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Phone *</label>
                  <input type="tel" name="phone" required className={inputCls} value={formData.phone} onChange={handleChange} />
                </div>
              </div>
            </div>

            <div className="gold-divider" />

            <div>
              {sectionHeading('Personal Information')}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-sacred-700">First Name *</label>
                  <input type="text" name="first_name" required className={inputCls} value={formData.first_name} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Last Name *</label>
                  <input type="text" name="last_name" required className={inputCls} value={formData.last_name} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Gotram *</label>
                  <input type="text" name="gotram" required className={inputCls} value={formData.gotram} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Preferred Language *</label>
                  <select name="preferred_language" required className={inputCls} value={formData.preferred_language} onChange={handleChange}>
                    {LANGUAGES.map((lang) => (
                      <option key={lang.value} value={lang.value}>{lang.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="gold-divider" />

            <div>
              {sectionHeading('Birth Information')}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Date of Birth *</label>
                  <input type="date" name="birth_date" required className={inputCls} value={formData.birth_date} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Time of Birth (24hr) *</label>
                  <input type="time" name="birth_time" required className={inputCls} value={formData.birth_time} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Birth City *</label>
                  <input type="text" name="birth_city" required className={inputCls} value={formData.birth_city} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Birth State *</label>
                  <input type="text" name="birth_state" required className={inputCls} value={formData.birth_state} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Birth Country *</label>
                  <input type="text" name="birth_country" required className={inputCls} value={formData.birth_country} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Janma Nakshatra (Birth Star)</label>
                  <input type="text" name="birth_nakshatra" placeholder="e.g., Ashwini, Bharani, Krittika" className={inputCls} value={formData.birth_nakshatra} onChange={handleChange} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-sacred-700">Janma Raasi (Birth Zodiac Sign)</label>
                  <input type="text" name="birth_rashi" placeholder="e.g., Mesha, Vrishabha, Mithuna" className={inputCls} value={formData.birth_rashi} onChange={handleChange} />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              suppressHydrationWarning
              className="gold-btn w-full py-3"
            >
              {loading ? 'Registering...' : 'Create Account'}
            </button>

            <div className="text-center">
              <Link href={returnUrl ? `/login?returnUrl=${encodeURIComponent(returnUrl)}` : '/login'} className="gold-link text-sm">
                Already have an account? Sign in
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
