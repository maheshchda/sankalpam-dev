'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'react-toastify'
import Link from 'next/link'
import HomeButton from '@/components/HomeButton'
import Select from 'react-select'
import { Country, State, City } from 'country-state-city'
import {
  SANKALPAM_LANGUAGES,
  preferredLanguageToCode,
  backendLanguageFromIso,
  normalizeTemplateLanguage,
  t,
  getStateLevelLabelKey,
  getStateLevelPlaceholderKey,
} from '@/lib/sankalpamUiLabels'

interface Template {
  id: number
  name: string
  description: string
  language: string
  variables: string
}

interface FamilyMemberRow {
  id: number
  name: string
  relation: string
  is_deceased?: boolean
}

function isSankalpaProfileReady(u: {
  gotram?: string
  birth_nakshatra?: string
  birth_rashi?: string
} | null): boolean {
  if (!u) return false
  const g = (u.gotram || '').trim()
  const nak = (u.birth_nakshatra || '').trim()
  const rashi = (u.birth_rashi || '').trim()
  return Boolean(g && (nak || rashi))
}

export default function SankalpamPage() {
  const { user, loading: authLoading, logout } = useAuth()
  const router = useRouter()
  const [wantAutoGenerate, setWantAutoGenerate] = useState(false)
  const autoGenerateStartedRef = useRef(false)

  useEffect(() => {
    setWantAutoGenerate(new URLSearchParams(window.location.search).get('autoGenerate') === '1')
  }, [])

  const [templates, setTemplates] = useState<Template[]>([])
  const [templatesLoading, setTemplatesLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [locationBusy, setLocationBusy] = useState(false)

  const [sankalpamLanguageCode, setSankalpamLanguageCode] = useState<string>('en')

  const [location, setLocation] = useState({
    city: '',
    state: '',
    country: '',
    latitude: '',
    longitude: '',
  })
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>('')
  const [selectedStateCode, setSelectedStateCode] = useState<string>('')
  const [geocodeLoading, setGeocodeLoading] = useState(false)

  const statesForCountry = useMemo(
    () => (selectedCountryCode ? State.getStatesOfCountry(selectedCountryCode) : []),
    [selectedCountryCode]
  )
  const hasStates = statesForCountry.length > 0

  const [generatedSankalpam, setGeneratedSankalpam] = useState<{
    text: string
    audioUrl: string
  } | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentLine, setCurrentLine] = useState(0)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const profileInitDoneRef = useRef(false)
  const placeKeyRef = useRef<string>('')
  const familyHydratedRef = useRef(false)

  const [familyMembers, setFamilyMembers] = useState<FamilyMemberRow[] | null>(null)
  const [participantIds, setParticipantIds] = useState<number[] | null>(null)
  const [sankalpaIntent, setSankalpaIntent] = useState('general')
  const [showGotraNakEdit, setShowGotraNakEdit] = useState(false)
  const [gotraOverride, setGotraOverride] = useState('')
  const [nakshatraOverride, setNakshatraOverride] = useState('')

  const [userProfileForLocation, setUserProfileForLocation] = useState<{
    current_city?: string
    current_state?: string
    current_country?: string
    birth_city?: string
    birth_state?: string
    birth_country?: string
    preferred_language?: string
  } | null>(null)

  const templateForLanguage = useMemo(() => {
    if (!templates.length || !sankalpamLanguageCode) return null
    const want = backendLanguageFromIso(sankalpamLanguageCode)
    const byLang = (lang: string) =>
      templates.filter((tm) => normalizeTemplateLanguage(tm.language) === lang)

    const matches = byLang(want)
    if (matches.length === 0) return null
    return [...matches].sort((a, b) => a.id - b.id)[0]
  }, [templates, sankalpamLanguageCode])

  const needStateForCountry = useMemo(
    () => State.getStatesOfCountry(selectedCountryCode || '').length > 0,
    [selectedCountryCode]
  )

  const canGenerate = useMemo(
    () =>
      Boolean(templateForLanguage) &&
      Boolean(location.city?.trim()) &&
      Boolean(location.country?.trim()) &&
      (!needStateForCountry || Boolean(location.state?.trim())),
    [templateForLanguage, location.city, location.country, location.state, needStateForCountry]
  )

  const fetchTemplates = useCallback(async () => {
    setTemplatesLoading(true)
    try {
      const response = await api.get('/api/templates/templates')
      const templatesData = Array.isArray(response.data) ? response.data : []
      const uniqueTemplates = templatesData.filter(
        (template: Template, index: number, self: Template[]) =>
          index === self.findIndex((x: Template) => x.id === template.id)
      )
      setTemplates(uniqueTemplates)
      if (uniqueTemplates.length === 0) {
        toast.warning('No templates available. Please contact admin to upload templates.')
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string }
      console.error('Error fetching templates:', error)
      toast.error(`Failed to load templates: ${err.response?.data?.detail || err.message}`)
    } finally {
      setTemplatesLoading(false)
    }
  }, [])

  useEffect(() => {
    if (authLoading || !user) return
    api
      .get('/api/auth/me')
      .then((res) => setUserProfileForLocation(res.data))
      .catch(() => {})
  }, [authLoading, user])

  useEffect(() => {
    if (authLoading || !user) return
    api
      .get('/api/family/members')
      .then((res) => {
        const list = Array.isArray(res.data) ? res.data : []
        setFamilyMembers(
          list.map((m: { id: number; name: string; relation: string; is_deceased?: boolean }) => ({
            id: m.id,
            name: m.name,
            relation: m.relation,
            is_deceased: m.is_deceased,
          }))
        )
      })
      .catch(() => setFamilyMembers([]))
  }, [authLoading, user])

  useEffect(() => {
    if (familyMembers === null || familyHydratedRef.current) return
    familyHydratedRef.current = true
    const alive = familyMembers.filter((m) => !m.is_deceased)
    if (alive.length === 0) {
      setParticipantIds([])
      return
    }
    setParticipantIds(alive.map((m) => m.id))
  }, [familyMembers])

  useEffect(() => {
    if (!userProfileForLocation || profileInitDoneRef.current) return
    profileInitDoneRef.current = true

    const birthCity = userProfileForLocation.birth_city?.trim()
    const birthState = userProfileForLocation.birth_state?.trim()
    const birthCountry = userProfileForLocation.birth_country?.trim()
    const currentCity = userProfileForLocation.current_city?.trim()
    const currentState = userProfileForLocation.current_state?.trim()
    const currentCountry = userProfileForLocation.current_country?.trim()
    const city = currentCity || birthCity
    const state = currentState || birthState
    const country = currentCountry || birthCountry
    const prefLang = userProfileForLocation.preferred_language

    if (country || state || city) {
      let countryCode = ''
      let stateCode = ''
      if (country) {
        const match = Country.getAllCountries().find((c) => c.name.toLowerCase() === country.toLowerCase())
        if (match) {
          countryCode = match.isoCode
          const states = State.getStatesOfCountry(match.isoCode)
          if (state && states.length > 0) {
            const stateMatch = states.find((s) => s.name.toLowerCase() === state.toLowerCase())
            if (stateMatch) stateCode = stateMatch.isoCode
          }
        }
      }
      setLocation((prev) => ({
        ...prev,
        city: city || prev.city,
        state: state || prev.state,
        country: country || prev.country,
        latitude: '',
        longitude: '',
      }))
      if (countryCode) setSelectedCountryCode(countryCode)
      if (stateCode) setSelectedStateCode(stateCode)
    }

    const langCode = preferredLanguageToCode(prefLang)
    setSankalpamLanguageCode(langCode || 'en')
  }, [userProfileForLocation])

  useEffect(() => {
    if (location.country && !selectedCountryCode) {
      const match = Country.getAllCountries().find(
        (c) => c.name.toLowerCase() === location.country.trim().toLowerCase()
      )
      if (match) setSelectedCountryCode(match.isoCode)
    }
  }, [location.country, selectedCountryCode])

  useEffect(() => {
    if (location.state && selectedCountryCode && !selectedStateCode) {
      const match = State.getStatesOfCountry(selectedCountryCode).find(
        (s) => s.name.toLowerCase() === location.state.trim().toLowerCase()
      )
      if (match) setSelectedStateCode(match.isoCode)
    }
  }, [location.state, selectedCountryCode, selectedStateCode])

  useEffect(() => {
    if (authLoading || !user) return
    fetchTemplates()
  }, [authLoading, user, fetchTemplates])

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [authLoading, user, router])

  const fetchLatLonFromPlace = async (city: string, state: string, country: string) => {
    const c = city?.trim()
    const s = state?.trim()
    const co = country?.trim()
    if (!c || !co) return
    setGeocodeLoading(true)
    try {
      const response = await api.get('/api/templates/forward-geocode', {
        params: { city: c, state: s, country: co },
      })
      const lat = response.data?.latitude ?? ''
      const lon = response.data?.longitude ?? ''
      setLocation((prev) => ({ ...prev, latitude: lat, longitude: lon }))
      if (lat && lon) {
        toast.success('Coordinates updated for selected place.')
      } else {
        toast.warning('Could not resolve coordinates for this place. Sankalpam may use default location.')
      }
    } catch (err) {
      console.error('Forward geocode failed:', err)
      toast.error('Could not get coordinates for this place.')
      setLocation((prev) => ({ ...prev, latitude: '', longitude: '' }))
    } finally {
      setGeocodeLoading(false)
    }
  }

  useEffect(() => {
    const city = location.city?.trim()
    const state = location.state?.trim()
    const country = location.country?.trim()
    const key = `${country}|${state}|${city}`
    const placeComplete = Boolean(city && country && (hasStates ? state : true))
    if (placeComplete && key !== placeKeyRef.current) {
      placeKeyRef.current = key
      if (!location.latitude || !location.longitude) {
        fetchLatLonFromPlace(city, state || '', country)
      }
    }
    if (!city || !country) placeKeyRef.current = ''
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.country, location.state, location.city, location.latitude, location.longitude, hasStates])

  const getApproximateLocationFromIP = async () => {
    toast.info('Getting approximate location from your internet connection…')
    setLocationBusy(true)
    try {
      const res = await fetch('https://ipapi.co/json/')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const city = data.city || ''
      const state = data.region || data.region_code || ''
      const country = data.country_name || data.country_code || ''
      const lat = data.latitude != null ? String(data.latitude) : ''
      const lon = data.longitude != null ? String(data.longitude) : ''
      setLocation({
        city,
        state,
        country,
        latitude: lat,
        longitude: lon,
      })
      toast.success('Approximate location set from your IP. You can edit the fields if needed.')
    } catch (err) {
      console.error('[Sankalpam Location] IP lookup failed:', err)
      toast.error('Could not get location from IP. Please enter city, state, and country manually.')
    } finally {
      setLocationBusy(false)
    }
  }

  const getCurrentLocation = async () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported by your browser. Use "Use approximate location" below.')
      return
    }

    if ('permissions' in navigator && 'query' in navigator.permissions) {
      try {
        const result = await navigator.permissions.query({ name: 'geolocation' as PermissionName })
        if (result.state === 'denied') {
          toast.error('Location is blocked for this site. Use "Use approximate location" or allow location in site settings.')
          return
        }
      } catch {
        // continue
      }
    }

    toast.info('Getting your location… Allow when your browser asks.')
    try {
      setLocationBusy(true)

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const lat = position.coords.latitude.toString()
            const lon = position.coords.longitude.toString()

            setLocation({
              city: '',
              state: '',
              country: '',
              latitude: lat,
              longitude: lon,
            })

            try {
              const response = await api.get('/api/templates/reverse-geocode', {
                params: { latitude: lat, longitude: lon },
              })

              if (response.data.city || response.data.state || response.data.country) {
                setLocation({
                  city: response.data.city || '',
                  state: response.data.state || '',
                  country: response.data.country || '',
                  latitude: lat,
                  longitude: lon,
                })
                toast.success('Location detected from coordinates!')
              } else {
                toast.warning('Coordinates obtained. Enter city, state, and country manually if needed.')
              }
            } catch (err: unknown) {
              const e = err as { response?: { status?: number; data?: { detail?: string } } }
              console.error('[Sankalpam Location] Reverse geocode failed:', err)
              const status = e.response?.status
              const detail = e.response?.data?.detail
              if (status === 401) {
                toast.error('Please log in again, then try Get Location.')
              } else if (detail && typeof detail === 'string') {
                toast.error(`Address lookup failed: ${detail}`)
              } else {
                toast.error('Could not get address from coordinates. Enter city, state, and country manually.')
              }
            }
          } catch (error) {
            console.error('[Sankalpam Location] Process error:', error)
            toast.error('Error processing location data. Please enter manually.')
          } finally {
            setLocationBusy(false)
          }
        },
        (error) => {
          console.error('[Sankalpam Location] Geolocation error:', error.code, error.message)
          let errorMessage = 'Could not get your location. '
          switch (error.code) {
            case 1:
              errorMessage += 'Use "Use approximate location" below or allow location in site settings.'
              break
            case 2:
              errorMessage += 'Use "Use approximate location" below or enter address manually.'
              break
            case 3:
              errorMessage += 'Use "Use approximate location" below or try again.'
              break
            default:
              errorMessage += 'Use "Use approximate location" below or enter manually.'
          }
          toast.error(errorMessage)
          setLocationBusy(false)
        },
        {
          enableHighAccuracy: false,
          timeout: 20000,
          maximumAge: 120000,
        }
      )
    } catch (error) {
      console.error('[Sankalpam Location] getCurrentLocation error:', error)
      toast.error('An error occurred. Try "Use approximate location" or enter manually.')
      setLocationBusy(false)
    }
  }

  useEffect(() => {
    if (generatedSankalpam) {
      setTimeout(() => {
        const playbackSection = document.getElementById('sankalpam-playback')
        if (playbackSection) {
          playbackSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 100)

      if (audioRef.current) {
        const audio = audioRef.current
        const handleCanPlay = () => {
          audio
            .play()
            .then(() => {
              setIsPlaying(true)
              startTextAnimation()
            })
            .catch((err) => {
              console.error('Error auto-playing audio:', err)
              toast.info('Click play button to start Sankalpam playback')
            })
          audio.removeEventListener('canplay', handleCanPlay)
        }
        audio.addEventListener('canplay', handleCanPlay)
        if (audio.readyState >= 2) {
          handleCanPlay()
        }
        return () => {
          audio.removeEventListener('canplay', handleCanPlay)
        }
      }
    }
  }, [generatedSankalpam])

  const toggleParticipant = (memberId: number) => {
    setParticipantIds((prev) => {
      if (prev === null) return prev
      if (prev.includes(memberId)) return prev.filter((x) => x !== memberId)
      return [...prev, memberId]
    })
  }

  const startTextAnimation = () => {
    if (!generatedSankalpam || !audioRef.current) return

    const lines = generatedSankalpam.text.split('\n').filter((line) => line.trim())
    if (lines.length === 0) return

    const audio = audioRef.current
    const checkDuration = setInterval(() => {
      if (audio.duration && audio.duration > 0) {
        clearInterval(checkDuration)
        const durationPerLine = audio.duration / lines.length
        let lineIndex = 0

        const interval = setInterval(() => {
          if (lineIndex < lines.length && audio && !audio.paused) {
            setCurrentLine(lineIndex)
            lineIndex++
          } else {
            clearInterval(interval)
          }
        }, durationPerLine * 1000)

        audio.onended = () => {
          clearInterval(interval)
          setIsPlaying(false)
          setCurrentLine(0)
        }
      }
    }, 100)

    return () => {
      clearInterval(checkDuration)
    }
  }

  const handleGenerate = useCallback(async () => {
    if (!templateForLanguage) {
      toast.error(t('noTemplateForLang', sankalpamLanguageCode))
      return
    }

    const city = location.city?.trim()
    const state = location.state?.trim()
    const country = location.country?.trim()

    if (!city || !country || (needStateForCountry && !state)) {
      toast.error(
        needStateForCountry ? 'Please select Country, State, and City.' : 'Please select Country and City.'
      )
      return
    }

    setGenerating(true)
    try {
      const requestData = {
        template_id: templateForLanguage.id,
        location_city: city,
        location_state: state || '',
        location_country: country,
        latitude: location.latitude || null,
        longitude: location.longitude || null,
        date: new Date().toISOString(),
        participant_member_ids: participantIds === null ? undefined : participantIds,
        sankalpam_language_code: sankalpamLanguageCode,
        sankalpa_intent: sankalpaIntent,
        override_gotram:
          showGotraNakEdit && gotraOverride.trim() ? gotraOverride.trim() : undefined,
        override_birth_nakshatra:
          showGotraNakEdit && nakshatraOverride.trim() ? nakshatraOverride.trim() : undefined,
      }

      const response = await api.post('/api/templates/generate', requestData)

      if (response.data.audio_url) {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const audioUrl = `${baseUrl}${response.data.audio_url}`
        setGeneratedSankalpam({
          text: response.data.text,
          audioUrl,
        })
        toast.success('Sankalpam generated successfully! Starting playback...')
        if (wantAutoGenerate) {
          router.replace('/sankalpam', { scroll: false })
        }
        setTimeout(() => {
          const playbackSection = document.getElementById('sankalpam-playback')
          if (playbackSection) {
            playbackSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        }, 100)
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string }
      console.error('Error generating Sankalpam:', error)
      toast.error(err.response?.data?.detail || err.message || 'Failed to generate Sankalpam')
    } finally {
      setGenerating(false)
    }
  }, [
    templateForLanguage,
    location.city,
    location.state,
    location.country,
    location.latitude,
    location.longitude,
    needStateForCountry,
    sankalpamLanguageCode,
    wantAutoGenerate,
    router,
    participantIds,
    sankalpaIntent,
    showGotraNakEdit,
    gotraOverride,
    nakshatraOverride,
  ])

  const handlePlay = () => {
    if (audioRef.current) {
      audioRef.current.play()
      setIsPlaying(true)
      startTextAnimation()
    }
  }

  const handlePause = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      setIsPlaying(false)
    }
  }

  useEffect(() => {
    if (!wantAutoGenerate || authLoading || templatesLoading) return
    if (autoGenerateStartedRef.current) return
    if (!canGenerate || generating || locationBusy) return
    autoGenerateStartedRef.current = true
    toast.info('Generating your Sankalpam…')
    void handleGenerate()
  }, [
    wantAutoGenerate,
    authLoading,
    templatesLoading,
    canGenerate,
    generating,
    locationBusy,
    handleGenerate,
  ])

  if (authLoading || templatesLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-100">
        <p className="text-amber-900 text-lg">Loading…</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="text-2xl font-bold text-amber-600">
              {t('appName', sankalpamLanguageCode)}
            </Link>
            <div className="flex flex-wrap items-center gap-2 sm:gap-4">
              <HomeButton variant="light" />
              <Link href="/dashboard" className="px-4 py-2 text-gray-700 hover:text-amber-600">
                {t('backToDashboard', sankalpamLanguageCode)}
              </Link>
              <button
                type="button"
                onClick={() => {
                  logout()
                  router.push('/login')
                }}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                {t('logout', sankalpamLanguageCode)}
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('pageTitle', sankalpamLanguageCode)}</h1>
          <p className="text-gray-600 mb-6 text-sm">{t('pageIntro', sankalpamLanguageCode)}</p>

          {/* Location — same pattern as Pooja calendar flow */}
          <div className="bg-white rounded-lg border border-amber-100 p-6 mb-6">
            <div className="flex flex-wrap justify-between items-center gap-2 mb-2">
              <h2 className="text-2xl font-bold">{t('location', sankalpamLanguageCode)}</h2>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={getCurrentLocation}
                  disabled={locationBusy}
                  className="px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 disabled:opacity-50"
                >
                  📍 {t('getCurrentLocation', sankalpamLanguageCode)}
                </button>
                <button
                  type="button"
                  onClick={getApproximateLocationFromIP}
                  disabled={locationBusy}
                  className="px-3 py-1.5 text-sm bg-slate-100 text-slate-700 rounded-md hover:bg-slate-200 disabled:opacity-50"
                >
                  🌐 {t('useApproxLocation', sankalpamLanguageCode)}
                </button>
              </div>
            </div>
            <p className="text-gray-600 mb-4 text-sm">{t('locationDesc', sankalpamLanguageCode)}</p>

            <div className={`grid grid-cols-1 gap-4 mb-4 ${hasStates ? 'md:grid-cols-3' : 'md:grid-cols-2'}`}>
              <div>
                <label className="block text-xs text-gray-600 mb-1">{t('country', sankalpamLanguageCode)}</label>
                <Select<{ value: string; label: string }>
                  options={Country.getAllCountries().map((c) => ({ value: c.isoCode, label: c.name }))}
                  value={location.country ? { value: selectedCountryCode, label: location.country } : null}
                  onChange={(opt) => {
                    const code = opt?.value ?? ''
                    const name = opt?.label ?? ''
                    setSelectedCountryCode(code)
                    setSelectedStateCode('')
                    setLocation((prev) => ({
                      ...prev,
                      country: name,
                      state: '',
                      city: '',
                      latitude: '',
                      longitude: '',
                    }))
                  }}
                  placeholder={t('selectCountry', sankalpamLanguageCode)}
                  isClearable
                  isSearchable
                  className="react-select-container"
                  classNamePrefix="react-select"
                />
              </div>
              {hasStates && (
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    {t(getStateLevelLabelKey(selectedCountryCode), sankalpamLanguageCode)}
                  </label>
                  <Select<{ value: string; label: string }>
                    options={statesForCountry.map((s) => ({ value: s.isoCode, label: s.name }))}
                    value={location.state ? { value: selectedStateCode, label: location.state } : null}
                    onChange={(opt) => {
                      const code = opt?.value ?? ''
                      const name = opt?.label ?? ''
                      setSelectedStateCode(code)
                      setLocation((prev) => ({
                        ...prev,
                        state: name,
                        city: '',
                        latitude: '',
                        longitude: '',
                      }))
                    }}
                    placeholder={t(getStateLevelPlaceholderKey(selectedCountryCode), sankalpamLanguageCode)}
                    isClearable
                    isSearchable
                    isDisabled={!selectedCountryCode}
                    className="react-select-container"
                    classNamePrefix="react-select"
                  />
                </div>
              )}
              <div>
                <label className="block text-xs text-gray-600 mb-1">{t('city', sankalpamLanguageCode)}</label>
                <Select<{ value: string; label: string; latitude?: string | null; longitude?: string | null }>
                  options={
                    hasStates
                      ? (City.getCitiesOfState(selectedCountryCode, selectedStateCode) || []).map((c) => ({
                          value: c.name,
                          label: c.name,
                          latitude: c.latitude ?? undefined,
                          longitude: c.longitude ?? undefined,
                        }))
                      : (City.getCitiesOfCountry(selectedCountryCode) || []).map((c) => ({
                          value: c.name,
                          label: c.name,
                          latitude: c.latitude ?? undefined,
                          longitude: c.longitude ?? undefined,
                        }))
                  }
                  value={location.city ? { value: location.city, label: location.city } : null}
                  onChange={(opt) => {
                    const city = opt?.value ?? ''
                    const lat = opt?.latitude != null && opt?.latitude !== '' ? String(opt.latitude) : ''
                    const lon = opt?.longitude != null && opt?.longitude !== '' ? String(opt.longitude) : ''
                    setLocation((prev) => ({
                      ...prev,
                      city,
                      latitude: lat,
                      longitude: lon,
                    }))
                  }}
                  placeholder={t('selectCity', sankalpamLanguageCode)}
                  isClearable
                  isSearchable
                  isDisabled={!selectedCountryCode || (hasStates && !selectedStateCode)}
                  className="react-select-container"
                  classNamePrefix="react-select"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-600 mb-1">{t('latitude', sankalpamLanguageCode)}</label>
                <input
                  type="text"
                  readOnly
                  value={location.latitude || (geocodeLoading ? '…' : '')}
                  className="w-full rounded-md border-gray-200 bg-gray-50 text-gray-700"
                  placeholder="—"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">{t('longitude', sankalpamLanguageCode)}</label>
                <input
                  type="text"
                  readOnly
                  value={location.longitude || (geocodeLoading ? '…' : '')}
                  className="w-full rounded-md border-gray-200 bg-gray-50 text-gray-700"
                  placeholder="—"
                />
              </div>
            </div>
            <p className="text-gray-500 text-xs mt-1">{t('latitudeLongitudeDesc', sankalpamLanguageCode)}</p>
          </div>

          {/* Sankalpam language — overrides profile for this flow */}
          <div className="bg-white rounded-lg border border-amber-100 p-6 mb-6">
            <h2 className="text-2xl font-bold mb-2">{t('sankalpamLanguage', sankalpamLanguageCode)}</h2>
            <p className="text-gray-600 mb-4 text-sm">{t('languageDesc', sankalpamLanguageCode)}</p>
            <div className="max-w-xs">
              <label htmlFor="sankalpam-language" className="block text-xs text-gray-600 mb-1">
                {t('language', sankalpamLanguageCode)}
              </label>
              <select
                id="sankalpam-language"
                value={sankalpamLanguageCode}
                onChange={(e) => setSankalpamLanguageCode(e.target.value)}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
              >
                <option value="">{t('selectLanguage', sankalpamLanguageCode)}</option>
                {SANKALPAM_LANGUAGES.map(({ code, label }) => (
                  <option key={code} value={code}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            {sankalpamLanguageCode && !templateForLanguage && templates.length > 0 && (
              <p className="text-amber-800 text-sm mt-3">{t('noTemplateForLang', sankalpamLanguageCode)}</p>
            )}
          </div>

          {sankalpamLanguageCode ? (
            <div className="bg-white rounded-lg border border-amber-100 p-6 mb-6 space-y-6">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="text-2xl font-bold">{t('sankalpaSetupTitle', sankalpamLanguageCode)}</h2>
                {isSankalpaProfileReady(user) ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-800">
                    <span aria-hidden>✓</span> {t('profileReadyBadge', sankalpamLanguageCode)}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-900">
                    {t('profileIncompleteBadge', sankalpamLanguageCode)}
                  </span>
                )}
              </div>

              <div>
                <p className="text-gray-600 mb-3 text-sm">{t('sankalpaSetupParticipants', sankalpamLanguageCode)}</p>
                {familyMembers === null ? (
                  <p className="text-gray-500 text-sm">…</p>
                ) : familyMembers.filter((m) => !m.is_deceased).length === 0 ? (
                  <p className="text-gray-500 text-sm">
                    {sankalpamLanguageCode === 'te'
                      ? 'కుటుంబ సభ్యులను డాష్‌బోర్డ్‌లో జోడించండి.'
                      : 'Add family members from your dashboard to include them here.'}
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {familyMembers
                      .filter((m) => !m.is_deceased)
                      .map((m) => (
                        <li key={m.id} className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            id={`generic-participant-${m.id}`}
                            checked={participantIds?.includes(m.id) ?? false}
                            onChange={() => toggleParticipant(m.id)}
                            className="h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
                          />
                          <label htmlFor={`generic-participant-${m.id}`} className="text-gray-800 cursor-pointer">
                            <span className="font-medium">{m.name}</span>
                            <span className="text-gray-500 text-sm"> ({m.relation})</span>
                          </label>
                        </li>
                      ))}
                  </ul>
                )}
              </div>

              {sankalpamLanguageCode === 'te' && (
                <div>
                  <label htmlFor="generic-sankalpa-intent" className="block text-xs text-gray-600 mb-1">
                    {t('sankalpaIntentLabel', sankalpamLanguageCode)}
                  </label>
                  <select
                    id="generic-sankalpa-intent"
                    value={sankalpaIntent}
                    onChange={(e) => setSankalpaIntent(e.target.value)}
                    className="max-w-md w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                  >
                    <option value="general">{t('intentGeneral', sankalpamLanguageCode)}</option>
                    <option value="health">{t('intentHealth', sankalpamLanguageCode)}</option>
                    <option value="wealth">{t('intentWealth', sankalpamLanguageCode)}</option>
                    <option value="papam">{t('intentPapam', sankalpamLanguageCode)}</option>
                    <option value="business">{t('intentBusiness', sankalpamLanguageCode)}</option>
                  </select>
                </div>
              )}

              <div className="flex flex-col sm:flex-row sm:items-start gap-4 rounded-xl border border-amber-100 bg-amber-50/60 p-4">
                <div className="text-5xl leading-none select-none" aria-hidden>
                  🪷
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <h3 className="font-semibold text-gray-900">{t('gotraNakshatraSection', sankalpamLanguageCode)}</h3>
                    <button
                      type="button"
                      onClick={() => {
                        setShowGotraNakEdit((open) => {
                          const next = !open
                          if (next && user) {
                            setGotraOverride(user.gotram || '')
                            setNakshatraOverride(user.birth_nakshatra || '')
                          }
                          return next
                        })
                      }}
                      className="text-sm text-amber-700 underline hover:text-amber-900"
                    >
                      {t('editRitualDetails', sankalpamLanguageCode)}
                    </button>
                  </div>
                  {!showGotraNakEdit ? (
                    <p className="text-gray-800 break-words">
                      <span className="font-medium">{user?.gotram || '—'}</span>
                      {user?.birth_nakshatra ? (
                        <span className="text-gray-600"> · {user.birth_nakshatra}</span>
                      ) : null}
                      {user?.birth_rashi ? (
                        <span className="text-gray-600"> · {user.birth_rashi}</span>
                      ) : null}
                    </p>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          {t('gotraFieldLabel', sankalpamLanguageCode)}
                        </label>
                        <input
                          type="text"
                          value={gotraOverride}
                          onChange={(e) => setGotraOverride(e.target.value)}
                          className="w-full rounded-md border-gray-300 shadow-sm text-sm"
                          placeholder={user?.gotram || ''}
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          {t('janmaNakshatraFieldLabel', sankalpamLanguageCode)}
                        </label>
                        <input
                          type="text"
                          value={nakshatraOverride}
                          onChange={(e) => setNakshatraOverride(e.target.value)}
                          className="w-full rounded-md border-gray-300 shadow-sm text-sm"
                          placeholder={user?.birth_nakshatra || ''}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : null}

          <button
            type="button"
            onClick={() => void handleGenerate()}
            disabled={!canGenerate || generating || locationBusy}
            className="w-full py-3 rounded-lg font-semibold text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? t('generatingSankalpam', sankalpamLanguageCode) : t('generateButton', sankalpamLanguageCode)}
          </button>
        </div>

        {generatedSankalpam && (
          <div id="sankalpam-playback" className="bg-white rounded-lg shadow p-6 mt-6">
            <div className="mb-6 text-center">
              <h2 className="font-cinzel text-3xl font-bold text-amber-950 mb-2">Sankalpam</h2>
              <p className="text-stone-500">Your personalized Sankalpam</p>
            </div>

            <div className="mb-6 text-center">
              <audio
                ref={audioRef}
                src={generatedSankalpam.audioUrl}
                preload="auto"
                id="sankalpam-audio"
                onEnded={() => {
                  setIsPlaying(false)
                  setCurrentLine(0)
                }}
              />
              <div className="flex justify-center gap-4">
                <button
                  type="button"
                  onClick={handlePlay}
                  disabled={isPlaying}
                  className="px-6 py-3 rounded-lg font-semibold bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50"
                >
                  ▶️ {isPlaying ? t('playing', sankalpamLanguageCode) : t('playSankalpam', sankalpamLanguageCode)}
                </button>
                {isPlaying && (
                  <button
                    type="button"
                    onClick={handlePause}
                    className="px-6 py-3 rounded-lg font-semibold border border-gray-300 text-gray-800 hover:bg-gray-50"
                  >
                    ⏸️ {t('pause', sankalpamLanguageCode)}
                  </button>
                )}
              </div>
            </div>

            <div className="bg-amber-50/50 rounded-lg p-6 min-h-[300px] max-h-[600px] overflow-y-auto border border-amber-100">
              <AnimatePresence mode="wait">
                {generatedSankalpam.text
                  .split('\n')
                  .filter((line) => line.trim())
                  .map((line, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{
                        opacity: currentLine === index ? 1 : 0.5,
                        y: 0,
                        scale: currentLine === index ? 1.02 : 1,
                      }}
                      transition={{ duration: 0.3 }}
                      className={`mb-3 text-lg ${
                        currentLine === index
                          ? 'text-amber-950 font-semibold bg-amber-100 border border-amber-200 p-3 rounded-lg'
                          : 'text-stone-600'
                      }`}
                    >
                      {line}
                    </motion.div>
                  ))}
              </AnimatePresence>
            </div>

            <div className="mt-6 text-center">
              <button
                type="button"
                onClick={() => {
                  setGeneratedSankalpam(null)
                  setIsPlaying(false)
                  setCurrentLine(0)
                  if (audioRef.current) {
                    audioRef.current.pause()
                    audioRef.current.currentTime = 0
                  }
                }}
                className="px-4 py-2 bg-gray-100 text-stone-700 rounded-md hover:bg-gray-200 border border-gray-200"
              >
                Generate another Sankalpam
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
