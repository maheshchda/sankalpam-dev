'use client'

import { useEffect, useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'react-toastify'
import Link from 'next/link'
import Select from 'react-select'
import { Country, State, City } from 'country-state-city'

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

const NAKSHATRAS = [
  'Ashwini',
  'Bharani',
  'Krittika',
  'Rohini',
  'Mrigashira',
  'Ardra',
  'Punarvasu',
  'Pushya',
  'Ashlesha',
  'Magha',
  'Purva Phalguni',
  'Uttara Phalguni',
  'Hasta',
  'Chitra',
  'Swati',
  'Vishakha',
  'Anuradha',
  'Jyeshtha',
  'Mula',
  'Purva Ashadha',
  'Uttara Ashadha',
  'Shravana',
  'Dhanishta',
  'Shatabhisha',
  'Purva Bhadrapada',
  'Uttara Bhadrapada',
  'Revati',
]

const RAASIS = [
  'Mesha',
  'Vrishabha',
  'Mithuna',
  'Karka',
  'Simha',
  'Kanya',
  'Tula',
  'Vrischika',
  'Dhanu',
  'Makara',
  'Kumbha',
  'Meena',
]

const PADAS = ['1', '2', '3', '4']

// Current Address: same labels as Pooja page (State / Province / Region by country)
const CURRENT_ADDRESS_LABELS = {
  country: 'Country *',
  state: 'State *',
  province: 'Province *',
  stateProvince: 'State / Province *',
  selectCountry: 'Select country...',
  selectState: 'Select state...',
  selectProvince: 'Select province...',
  city: 'City *',
  selectCity: 'Select city...',
}
const STATE_LEVEL_LABEL_BY_COUNTRY: Record<string, keyof typeof CURRENT_ADDRESS_LABELS> = {
  US: 'state',
  IN: 'state',
  AU: 'state',
  CA: 'province',
  GB: 'stateProvince',
}
function getCurrentAddressStateLabelKey(countryCode: string): keyof typeof CURRENT_ADDRESS_LABELS {
  return STATE_LEVEL_LABEL_BY_COUNTRY[countryCode] || 'stateProvince'
}
function getCurrentAddressStatePlaceholderKey(countryCode: string): keyof typeof CURRENT_ADDRESS_LABELS {
  return countryCode === 'CA' ? 'selectProvince' : 'selectState'
}

export default function ProfilePage() {
  const { user, logout, refreshUser } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    gotram: '',
    birth_city: '',
    birth_state: '',
    birth_country: '',
    birth_date: '',
    birth_time: '',
    birth_nakshatra: '',
    birth_rashi: '',
    birth_pada: '',
    preferred_language: 'sanskrit',
    current_city: '',
    current_state: '',
    current_country: '',
  })
  // Current address dropdowns (country-state-city)
  const [currentCountryCode, setCurrentCountryCode] = useState('')
  const [currentStateCode, setCurrentStateCode] = useState('')
  const currentStates = useMemo(
    () => (currentCountryCode ? State.getStatesOfCountry(currentCountryCode) : []),
    [currentCountryCode]
  )
  const hasCurrentStates = currentStates.length > 0

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!user && mounted) {
      router.push('/login')
      return
    }
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        gotram: user.gotram || '',
        birth_city: user.birth_city || '',
        birth_state: user.birth_state || '',
        birth_country: user.birth_country || '',
        birth_date: user.birth_date ? user.birth_date.slice(0, 10) : '',
        birth_time: user.birth_time || '',
        birth_nakshatra: user.birth_nakshatra || '',
        birth_rashi: user.birth_rashi || '',
        birth_pada: user.birth_pada || '',
        preferred_language: user.preferred_language || 'sanskrit',
        current_city: user.current_city || '',
        current_state: user.current_state || '',
        current_country: user.current_country || '',
      })
      // Sync current-address dropdown codes from profile
      const cc = (user.current_country || '').trim()
      if (cc) {
        const match = Country.getAllCountries().find((c) => c.name.toLowerCase() === cc.toLowerCase())
        if (match) {
          setCurrentCountryCode(match.isoCode)
          const states = State.getStatesOfCountry(match.isoCode)
          const cs = (user.current_state || '').trim()
          if (cs && states.length > 0) {
            const sm = states.find((s) => s.name.toLowerCase() === cs.toLowerCase())
            if (sm) setCurrentStateCode(sm.isoCode)
          }
        }
      }
    }
  }, [user, mounted, router])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.put('/api/users/me', {
        ...formData,
        birth_nakshatra: formData.birth_nakshatra || null,
        birth_rashi: formData.birth_rashi || null,
        birth_pada: formData.birth_pada || null,
        current_city: formData.current_city || null,
        current_state: formData.current_state || null,
        current_country: formData.current_country || null,
      })

      // Refresh user from backend so UI reflects latest data
      try {
        const res = await api.get('/api/auth/me')
        const updated = res.data
        setFormData({
          first_name: updated.first_name || '',
          last_name: updated.last_name || '',
          gotram: updated.gotram || '',
          birth_city: updated.birth_city || '',
          birth_state: updated.birth_state || '',
          birth_country: updated.birth_country || '',
          birth_date: updated.birth_date ? updated.birth_date.slice(0, 10) : '',
          birth_time: updated.birth_time || '',
          birth_nakshatra: updated.birth_nakshatra || '',
          birth_rashi: updated.birth_rashi || '',
          birth_pada: updated.birth_pada || '',
          preferred_language: updated.preferred_language || 'sanskrit',
          current_city: updated.current_city || '',
          current_state: updated.current_state || '',
          current_country: updated.current_country || '',
        })
        if (updated.current_country) {
          const m = Country.getAllCountries().find((c) => c.name.toLowerCase() === (updated.current_country || '').toLowerCase())
          if (m) {
            setCurrentCountryCode(m.isoCode)
            const st = State.getStatesOfCountry(m.isoCode)
            if (updated.current_state && st.length > 0) {
              const sm = st.find((s) => s.name.toLowerCase() === (updated.current_state || '').toLowerCase())
              if (sm) setCurrentStateCode(sm.isoCode)
            }
          }
        }
      } catch {
        // ignore, form already saved
      }
      toast.success('Profile updated successfully')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAccount = async () => {
    const confirmed = confirm(
      'Are you sure you want to delete your account? This will delete all your family members and sessions.'
    )
    if (!confirmed) return

    try {
      await api.delete('/api/users/me')
      toast.success('Account deleted successfully')
      logout()
      router.push('/login')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete account')
    }
  }

  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-100">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Loading...</h2>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="page-bg">
      <nav className="sacred-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="font-cinzel text-xl font-bold text-gold-400">Pooja Sankalpam</Link>
            <div className="flex items-center gap-3">
              <Link href="/dashboard" className="sacred-pill text-cream-200 border-gold-600/40 hover:text-gold-400">Back to Dashboard</Link>
              <button onClick={() => { logout(); router.push('/login') }} className="rounded-md border border-gold-600/40 px-3 py-1.5 text-sm text-cream-300 hover:bg-sacred-700 transition-colors">Logout</button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="sacred-card p-6 space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="font-cinzel text-2xl font-bold text-sacred-800">Your Profile</h2>
            <div className="text-sm text-stone-500 text-right space-y-1">
              <div>Username: {user.username}</div>
              <div>Email: {user.email}</div>
              <div className="flex items-center gap-2 justify-end">
                <span>Unique ID: {user.unique_id || '—'}</span>
                {user.unique_id && (
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(user.unique_id!)
                      toast.info('Copied!')
                    }}
                    className="px-2 py-0.5 text-xs bg-gold-500/20 text-sacred-700 rounded hover:bg-gold-500/30"
                  >
                    Copy
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Verification Status */}
          {(!user.email_verified || !user.phone_verified) && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="text-lg font-medium text-yellow-800 mb-2">Account Verification</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-yellow-700">
                    Email: {user.email_verified ? (
                      <span className="text-green-600 font-medium">✓ Verified</span>
                    ) : (
                      <span className="text-red-600 font-medium">✗ Not Verified</span>
                    )}
                  </span>
                  {!user.email_verified && (
                    <button
                      type="button"
                      onClick={async () => {
                        try {
                          const res = await api.post('/api/auth/resend-verification-email')
                          if (res.data.token) {
                            toast.success(
                              `Development mode: Your email verification token is ${res.data.token}. Use it on the verify page.`,
                              { autoClose: 10000 }
                            )
                          } else {
                            toast.success(res.data.message || 'Verification email sent')
                          }
                          // Refresh user data
                          if (refreshUser) {
                            await refreshUser()
                          }
                        } catch (error: any) {
                          toast.error(error.response?.data?.detail || 'Failed to send verification email')
                        }
                      }}
                      className="px-3 py-1 bg-yellow-600 text-white rounded text-xs hover:bg-yellow-700"
                    >
                      Resend Email
                    </button>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-yellow-700">
                    Phone: {user.phone_verified ? (
                      <span className="text-green-600 font-medium">✓ Verified</span>
                    ) : (
                      <span className="text-red-600 font-medium">✗ Not Verified</span>
                    )}
                  </span>
                  {!user.phone_verified && (
                    <button
                      type="button"
                      onClick={async () => {
                        try {
                          const res = await api.post('/api/auth/resend-verification-phone')
                          if (res.data.otp) {
                            toast.success(
                              `Development mode: Your phone OTP is ${res.data.otp}. Use it on the verify page.`,
                              { autoClose: 10000 }
                            )
                          } else {
                            toast.success(res.data.message || 'Verification code sent')
                          }
                          // Refresh user data
                          if (refreshUser) {
                            await refreshUser()
                          }
                        } catch (error: any) {
                          toast.error(error.response?.data?.detail || 'Failed to send verification code')
                        }
                      }}
                      className="px-3 py-1 bg-yellow-600 text-white rounded text-xs hover:bg-yellow-700"
                    >
                      Resend OTP
                    </button>
                  )}
                </div>
                <div className="mt-3 pt-3 border-t border-yellow-200">
                  <Link
                    href="/verify"
                    className="text-yellow-700 hover:text-yellow-900 underline text-sm"
                  >
                    Go to Verification Page →
                  </Link>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Personal Information */}
            <div className="border-b pb-4">
              <h3 className="text-lg font-medium mb-4">Personal Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">First Name *</label>
                  <input
                    type="text"
                    name="first_name"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.first_name}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Last Name *</label>
                  <input
                    type="text"
                    name="last_name"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.last_name}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Gotram *</label>
                  <input
                    type="text"
                    name="gotram"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.gotram}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Preferred Language *</label>
                  <select
                    name="preferred_language"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.preferred_language}
                    onChange={handleChange}
                  >
                    {LANGUAGES.map((lang) => (
                      <option key={lang.value} value={lang.value}>
                        {lang.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Birth Information */}
            <div className="border-b pb-4">
              <h3 className="text-lg font-medium mb-4">Birth Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Date of Birth *</label>
                  <input
                    type="date"
                    name="birth_date"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_date}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Time of Birth (24hr) *</label>
                  <input
                    type="time"
                    name="birth_time"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_time}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Birth City *</label>
                  <input
                    type="text"
                    name="birth_city"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_city}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Birth State *</label>
                  <input
                    type="text"
                    name="birth_state"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_state}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Birth Country *</label>
                  <input
                    type="text"
                    name="birth_country"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_country}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Janma Nakshatra (Birth Star)
                  </label>
                  <select
                    name="birth_nakshatra"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_nakshatra}
                    onChange={handleChange}
                  >
                    <option value="">Select Nakshatra (optional)</option>
                    {NAKSHATRAS.map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Janma Raasi (Birth Zodiac Sign)
                  </label>
                  <select
                    name="birth_rashi"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_rashi}
                    onChange={handleChange}
                  >
                    <option value="">Select Raasi (optional)</option>
                    {RAASIS.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Janma Pada (1–4)</label>
                  <select
                    name="birth_pada"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_pada}
                    onChange={handleChange}
                  >
                    <option value="">Select Pada (optional)</option>
                    {PADAS.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Current Address - same Country → State/Province → City as Pooja page */}
            <div className="border-b pb-4">
              <h3 className="text-lg font-medium mb-4">Current Address</h3>
              <p className="text-sm text-gray-600 mb-4">
                Where you currently live. This can be used as the default location for Pooja and Sankalpam.
              </p>
              <div className={`grid grid-cols-1 gap-4 mb-4 ${hasCurrentStates ? 'md:grid-cols-3' : 'md:grid-cols-2'}`}>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">{CURRENT_ADDRESS_LABELS.country}</label>
                  <Select<{ value: string; label: string }>
                    options={Country.getAllCountries().map((c) => ({ value: c.isoCode, label: c.name }))}
                    value={
                      formData.current_country
                        ? { value: currentCountryCode, label: formData.current_country }
                        : null
                    }
                    onChange={(opt) => {
                      const code = opt?.value ?? ''
                      const name = opt?.label ?? ''
                      setCurrentCountryCode(code)
                      setCurrentStateCode('')
                      setFormData((prev) => ({
                        ...prev,
                        current_country: name,
                        current_state: '',
                        current_city: '',
                      }))
                    }}
                    placeholder={CURRENT_ADDRESS_LABELS.selectCountry}
                    isClearable
                    isSearchable
                    className="react-select-container"
                    classNamePrefix="react-select"
                  />
                </div>
                {hasCurrentStates && (
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">
                      {CURRENT_ADDRESS_LABELS[getCurrentAddressStateLabelKey(currentCountryCode)]}
                    </label>
                    <Select<{ value: string; label: string }>
                      options={currentStates.map((s) => ({ value: s.isoCode, label: s.name }))}
                      value={
                        formData.current_state
                          ? { value: currentStateCode, label: formData.current_state }
                          : null
                      }
                      onChange={(opt) => {
                        const code = opt?.value ?? ''
                        const name = opt?.label ?? ''
                        setCurrentStateCode(code)
                        setFormData((prev) => ({
                          ...prev,
                          current_state: name,
                          current_city: '',
                        }))
                      }}
                      placeholder={CURRENT_ADDRESS_LABELS[getCurrentAddressStatePlaceholderKey(currentCountryCode)]}
                      isClearable
                      isSearchable
                      isDisabled={!currentCountryCode}
                      className="react-select-container"
                      classNamePrefix="react-select"
                    />
                  </div>
                )}
                <div>
                  <label className="block text-xs text-gray-600 mb-1">{CURRENT_ADDRESS_LABELS.city}</label>
                  <Select<{ value: string; label: string }>
                    options={
                      hasCurrentStates
                        ? (City.getCitiesOfState(currentCountryCode, currentStateCode) || []).map((c) => ({
                            value: c.name,
                            label: c.name,
                          }))
                        : (City.getCitiesOfCountry(currentCountryCode) || []).map((c) => ({
                            value: c.name,
                            label: c.name,
                          }))
                    }
                    value={
                      formData.current_city
                        ? { value: formData.current_city, label: formData.current_city }
                        : null
                    }
                    onChange={(opt) => {
                      const city = opt?.value ?? ''
                      setFormData((prev) => ({ ...prev, current_city: city }))
                    }}
                    placeholder={CURRENT_ADDRESS_LABELS.selectCity}
                    isClearable
                    isSearchable
                    isDisabled={!currentCountryCode || (hasCurrentStates && !currentStateCode)}
                    className="react-select-container"
                    classNamePrefix="react-select"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <button type="submit" disabled={loading} className="gold-btn">
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
              <button type="button" onClick={handleDeleteAccount} className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm">
                Delete Account
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

