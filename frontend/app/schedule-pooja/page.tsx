'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'react-toastify'
import Link from 'next/link'
import { Country, State, City } from 'country-state-city'

// ─── Types ────────────────────────────────────────────────────────────────────

interface Pooja {
  id: number
  name: string
  description?: string
}

interface Invitee {
  name: string
  last_name: string
  email: string
}

interface ScheduleInvitee {
  id: number
  name: string
  last_name?: string
  email: string
  rsvp_status?: string
  rsvp_token?: string
  cancelled_at?: string | null
  cancelled_reason?: string | null
}

interface Schedule {
  id: number
  pooja_name?: string
  scheduled_date: string
  invite_message?: string
  image_path?: string
  venue_place?: string
  venue_street_number?: string
  venue_street_name?: string
  venue_city?: string
  venue_state?: string
  venue_country?: string
  venue_coordinates?: string
  invitees: ScheduleInvitee[]
  created_at: string
}

interface AttendingMember {
  unique_id?: string
  name?: string
  nakshatra?: string
  gotra?: string
  relation?: string
}

interface RsvpSummary {
  attending: number
  not_attending: number
  maybe: number
  pending: number
  cancelled?: number
  invitees: {
    id: number
    name: string
    email: string
    status: string
    notes?: string
    cancelled_reason?: string
    rsvp_token?: string
    email_delivery_status?: string
    attending_members?: AttendingMember[]
  }[]
}

const EMPTY_INVITEE = (): Invitee => ({ name: '', last_name: '', email: '' })
const INITIAL_ROWS = 5

function todayLocal(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function venueOneLine(s: Schedule): string {
  const parts = [
    s.venue_place,
    [s.venue_street_number, s.venue_street_name].filter(Boolean).join(' '),
    s.venue_city,
    s.venue_state,
    s.venue_country,
  ].filter(Boolean)
  return parts.join(', ')
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function SchedulePoojaPage() {
  const { user, loading: authLoading, logout } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) router.push('/login?next=/schedule-pooja')
  }, [user, authLoading, router])

  // ── Pooja & date ────────────────────────────────────────────────────────
  const [poojaRegionState, setPoojaRegionState] = useState('')
  const [poojas, setPoojas] = useState<Pooja[]>([])
  const [poojaId, setPoojaId] = useState('')
  const [customPooja, setCustomPooja] = useState('')
  const [scheduledDate, setScheduledDate] = useState('')

  const indianStates = useMemo(() => State.getStatesOfCountry('IN'), [])

  // ── Invite content ───────────────────────────────────────────────────────
  const [inviteMessage, setInviteMessage] = useState('')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // ── Venue ────────────────────────────────────────────────────────────────
  const [atMyHome, setAtMyHome] = useState(false)
  const [venuePlace, setVenuePlace] = useState('')
  const [venueStreetNo, setVenueStreetNo] = useState('')
  const [venueStreetName, setVenueStreetName] = useState('')
  const [venueCountryCode, setVenueCountryCode] = useState('')
  const [venueStateCode, setVenueStateCode] = useState('')
  const [venueCity, setVenueCity] = useState('')
  const [venueCoords, setVenueCoords] = useState('')

  const venueCountries = useMemo(() => Country.getAllCountries(), [])
  const venueStates = useMemo(
    () => venueCountryCode ? State.getStatesOfCountry(venueCountryCode) : [],
    [venueCountryCode]
  )
  const venueCities = useMemo(
    () => venueCountryCode && venueStateCode
      ? City.getCitiesOfState(venueCountryCode, venueStateCode)
      : [],
    [venueCountryCode, venueStateCode]
  )

  // ── Invitees ─────────────────────────────────────────────────────────────
  const [invitees, setInvitees] = useState<Invitee[]>(
    Array.from({ length: INITIAL_ROWS }, EMPTY_INVITEE)
  )

  // ── History / RSVP ───────────────────────────────────────────────────────
  const [submitting, setSubmitting] = useState(false)
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [tab, setTab] = useState<'form' | 'history'>('form')
  const [sendingInvites, setSendingInvites] = useState<number | null>(null)
  const [rsvpSummary, setRsvpSummary] = useState<Record<number, RsvpSummary>>({})
  const [expandedRsvp, setExpandedRsvp] = useState<number | null>(null)
  const [editingScheduleId, setEditingScheduleId] = useState<number | null>(null)
  const [addMoreInvitees, setAddMoreInvitees] = useState<Invitee[]>([EMPTY_INVITEE()])
  const [addingInvitees, setAddingInvitees] = useState(false)
  const [cancellingInvitee, setCancellingInvitee] = useState<{ scheduleId: number; inviteeId: number } | null>(null)
  const [resendingInvitee, setResendingInvitee] = useState<{ scheduleId: number; inviteeId: number } | null>(null)
  const [checkingDelivery, setCheckingDelivery] = useState<number | null>(null)
  const [cancelReason, setCancelReason] = useState('')
  const [cancelModal, setCancelModal] = useState<{ scheduleId: number; inviteeId: number; name: string } | null>(null)

  // ── Fetch schedules on mount ─────────────────────────────────────────────
  useEffect(() => {
    if (!user) return
    fetchSchedules()
  }, [user])

  // ── Fetch poojas (filtered by Indian state when selected) ─────────────────
  useEffect(() => {
    if (!user) return
    const stateParam = poojaRegionState ? `?state=IN-${poojaRegionState}` : ''
    api.get(`/api/pooja/list${stateParam}`).then(r => setPoojas(r.data)).catch(() => {})
  }, [user, poojaRegionState])

  const fetchSchedules = async () => {
    try { const r = await api.get('/api/schedule'); setSchedules(r.data) } catch { /* silent */ }
  }

  // ── Dynamic invitees ─────────────────────────────────────────────────────
  const handleInviteeChange = (idx: number, field: keyof Invitee, value: string) => {
    const updated = invitees.map((inv, i) => i === idx ? { ...inv, [field]: value } : inv)
    if (idx === updated.length - 1 && value.trim()) updated.push(EMPTY_INVITEE())
    setInvitees(updated)
  }

  // ── Image ────────────────────────────────────────────────────────────────
  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return
    setImageFile(file)
    const reader = new FileReader()
    reader.onload = ev => setImagePreview(ev.target?.result as string)
    reader.readAsDataURL(file)
  }

  const resetForm = () => {
    setPoojaId(''); setCustomPooja(''); setScheduledDate('')
    setPoojaRegionState('')
    setInviteMessage(''); setImageFile(null); setImagePreview(null)
    setAtMyHome(false)
    setVenuePlace(''); setVenueStreetNo(''); setVenueStreetName('')
    setVenueCountryCode(''); setVenueStateCode(''); setVenueCity(''); setVenueCoords('')
    setInvitees(Array.from({ length: INITIAL_ROWS }, EMPTY_INVITEE))
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // ── At My Home: populate venue from user profile ──────────────────────────
  const handleAtMyHomeChange = (checked: boolean) => {
    setAtMyHome(checked)
    if (checked && user) {
      setVenuePlace('My Home')
      setVenueCity(user.current_city || '')
      const cc = (user.current_country || '').trim()
      if (cc) {
        const countryMatch = Country.getAllCountries().find(
          c => c.name.toLowerCase() === cc.toLowerCase()
        )
        if (countryMatch) {
          setVenueCountryCode(countryMatch.isoCode)
          const states = State.getStatesOfCountry(countryMatch.isoCode)
          const cs = (user.current_state || '').trim()
          if (cs && states.length > 0) {
            const stateMatch = states.find(s => s.name.toLowerCase() === cs.toLowerCase())
            if (stateMatch) setVenueStateCode(stateMatch.isoCode)
            else setVenueStateCode('')
          } else {
            setVenueStateCode('')
          }
        } else {
          setVenueCountryCode('')
          setVenueStateCode('')
        }
      } else {
        setVenueCountryCode('')
        setVenueStateCode('')
      }
    } else if (!checked) {
      setVenuePlace('')
      setVenueStreetNo('')
      setVenueStreetName('')
      setVenueCity('')
      setVenueCountryCode('')
      setVenueStateCode('')
      setVenueCoords('')
    }
  }

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!scheduledDate) { toast.error('Please select a date.'); return }
    if (scheduledDate < todayLocal()) { toast.error('Pooja date cannot be in the past.'); return }
    if (!poojaId && !customPooja.trim()) { toast.error('Please select or enter a Pooja name.'); return }

    const validInvitees = invitees.filter(i => i.name.trim() && i.email.trim())
    setSubmitting(true)
    try {
      const form = new FormData()
      if (poojaId && poojaId !== 'other') form.append('pooja_id', poojaId)
      form.append('pooja_name', (poojaId === 'other' || !poojaId) ? customPooja.trim() : '')
      form.append('scheduled_date', scheduledDate)
      form.append('invite_message', inviteMessage)
      form.append('invitees_json', JSON.stringify(validInvitees))
      if (imageFile) form.append('image', imageFile)
      // Venue
      form.append('venue_place', venuePlace)
      form.append('venue_street_number', venueStreetNo)
      form.append('venue_street_name', venueStreetName)
      form.append('venue_country', venueCountryCode ? Country.getCountryByCode(venueCountryCode)?.name || '' : '')
      form.append('venue_state', venueStateCode ? State.getStateByCodeAndCountry(venueStateCode, venueCountryCode)?.name || '' : '')
      form.append('venue_city', venueCity)
      form.append('venue_coordinates', venueCoords)

      await api.post('/api/schedule', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      toast.success('Pooja scheduled successfully!')
      resetForm()
      fetchSchedules()
      setTab('history')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to schedule pooja.')
    } finally {
      setSubmitting(false)
    }
  }

  // ── Send invitations ──────────────────────────────────────────────────────
  const handleSendInvites = async (scheduleId: number) => {
    setSendingInvites(scheduleId)
    try {
      const r = await api.post(`/api/rsvp/${scheduleId}/send`)
      const { sent, skipped, total, error } = r.data
      if (skipped.length > 0) {
        const msg = error ? `${error}` : `Sent ${sent}/${total}. RSVP links generated — share manually if needed.`
        toast.warn(msg, { autoClose: error ? 8000 : 4000 })
      } else {
        toast.success(`Invitations sent to ${sent} invitee(s)!`)
      }
      fetchSchedules()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to send invitations.')
    } finally { setSendingInvites(null) }
  }

  // ── RSVP summary ─────────────────────────────────────────────────────────
  const loadRsvpSummary = async (scheduleId: number) => {
    if (expandedRsvp === scheduleId) { setExpandedRsvp(null); return }
    try {
      const r = await api.get(`/api/rsvp/summary/${scheduleId}`)
      setRsvpSummary(prev => ({ ...prev, [scheduleId]: r.data }))
      setExpandedRsvp(scheduleId)
    } catch { toast.error('Failed to load RSVP details.') }
  }

  // ── Delete ────────────────────────────────────────────────────────────────
  const handleDelete = async (id: number) => {
    if (!confirm('Delete this scheduled pooja?')) return
    try { await api.delete(`/api/schedule/${id}`); toast.success('Schedule deleted.'); fetchSchedules() }
    catch { toast.error('Failed to delete.') }
  }

  // ── Add more invitees ─────────────────────────────────────────────────────
  const openEditInvitees = (schedule: Schedule) => {
    setEditingScheduleId(schedule.id)
    setAddMoreInvitees([EMPTY_INVITEE()])
  }
  const handleAddMoreInvitees = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingScheduleId) return
    const valid = addMoreInvitees.filter(i => i.name.trim() && i.email.trim())
    if (valid.length === 0) { toast.error('Add at least one invitee.'); return }
    setAddingInvitees(true)
    try {
      await api.patch(`/api/schedule/${editingScheduleId}/invitees`, new URLSearchParams({ invitees_json: JSON.stringify(valid) }), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      toast.success(`Added ${valid.length} invitee(s). Send invitations to notify them.`)
      setEditingScheduleId(null)
      fetchSchedules()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to add invitees.')
    } finally { setAddingInvitees(false) }
  }

  // ── Resend invite (single) ──────────────────────────────────────────────────
  const handleResendInvite = async (scheduleId: number, inviteeId: number) => {
    setResendingInvitee({ scheduleId, inviteeId })
    try {
      const r = await api.post(`/api/rsvp/${scheduleId}/invitees/${inviteeId}/resend`)
      if (r.data.sent) {
        toast.success('Invitation resent!')
      } else {
        const msg = r.data.error || r.data.message || 'Failed to send email.'
        toast.error(msg, { autoClose: 8000 })
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to resend invite.')
    } finally {
      setResendingInvitee(null)
    }
  }

  // ── Check Brevo delivery status ───────────────────────────────────────────
  const handleCheckDelivery = async (scheduleId: number) => {
    setCheckingDelivery(scheduleId)
    try {
      const r = await api.post(`/api/rsvp/${scheduleId}/check-delivery`)
      setRsvpSummary(prev => ({ ...prev, [scheduleId]: r.data.summary }))
      setExpandedRsvp(scheduleId) // Expand to show updated delivery status
      toast.success(r.data.updated > 0 ? `Updated delivery status for ${r.data.updated} invitee(s).` : 'No new delivery updates.')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to check delivery status.')
    } finally {
      setCheckingDelivery(null)
    }
  }

  // ── Cancel invite ─────────────────────────────────────────────────────────
  const openCancelModal = (scheduleId: number, inviteeId: number, name: string) => {
    setCancelModal({ scheduleId, inviteeId, name })
    setCancelReason('')
  }
  const handleCancelInvite = async () => {
    if (!cancelModal) return
    setCancellingInvitee({ scheduleId: cancelModal.scheduleId, inviteeId: cancelModal.inviteeId })
    try {
      await api.post(`/api/rsvp/${cancelModal.scheduleId}/invitees/${cancelModal.inviteeId}/cancel`, { reason: cancelReason })
      toast.success('Invitation cancelled. The invitee has been notified.')
      setCancelModal(null)
      setCancelReason('')
      fetchSchedules()
      if (expandedRsvp === cancelModal.scheduleId) {
        const r = await api.get(`/api/rsvp/summary/${cancelModal.scheduleId}`)
        setRsvpSummary(prev => ({ ...prev, [cancelModal!.scheduleId]: r.data }))
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to cancel invite.')
    } finally { setCancellingInvitee(null) }
  }

  // ── Guards ────────────────────────────────────────────────────────────────
  if (authLoading) {
    return (
      <div className="page-bg flex items-center justify-center min-h-screen">
        <p className="font-cinzel text-sacred-700 text-xl">Loading…</p>
      </div>
    )
  }
  if (!user) return null

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="page-bg min-h-screen">
      {/* Nav */}
      <nav className="sacred-header">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="font-cinzel text-xl font-bold text-gold-400">Pooja Sankalpam</Link>
            <div className="flex items-center gap-3">
              <Link href="/dashboard" className="sacred-pill text-cream-200 border-gold-600/40 hover:text-gold-400">Dashboard</Link>
              <button onClick={() => { logout(); router.push('/login') }}
                className="rounded-md border border-gold-600/40 px-3 py-1.5 text-sm text-cream-300 hover:bg-sacred-700 transition-colors">
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="font-cinzel text-3xl font-bold text-sacred-800 mb-2">Schedule a Pooja</h1>
          <div className="gold-divider mx-auto w-32" />
          <p className="text-stone-500 mt-3 text-sm">Plan your upcoming Pooja and invite family &amp; friends</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-cream-200 rounded-lg p-1 w-fit mx-auto">
          {(['form', 'history'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-5 py-2 rounded-md text-sm font-medium transition-all ${
                tab === t ? 'bg-sacred-800 text-gold-300 shadow' : 'text-stone-600 hover:text-sacred-700'
              }`}>
              {t === 'form' ? '+ Schedule New' : `My Schedules (${schedules.length})`}
            </button>
          ))}
        </div>

        {/* ══ FORM TAB ══ */}
        {tab === 'form' && (
          <form onSubmit={handleSubmit} className="space-y-6">

            {/* ── Pooja & Date ── */}
            <div className="sacred-card p-6">
              <h2 className="font-cinzel text-lg font-bold text-sacred-800 mb-4">Pooja Details</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

                {/* Region / State — filters pooja list by Indian regional tradition */}
                <div>
                  <label className="block text-sm font-semibold text-sacred-700 mb-1">
                    Your preferred region / state in India
                  </label>
                  <p className="text-xs text-stone-400 mb-1">Poojas filtered by regional traditions (home-hosted with guests)</p>
                  <select
                    className="sacred-input w-full"
                    value={poojaRegionState}
                    onChange={e => { setPoojaRegionState(e.target.value); setPoojaId('') }}
                  >
                    <option value="">— All India (common poojas) —</option>
                    {indianStates.map(s => (
                      <option key={s.isoCode} value={s.isoCode}>{s.name}</option>
                    ))}
                  </select>
                </div>

                {/* Pooja dropdown */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-sacred-700 mb-1">
                    Select Pooja <span className="text-red-500">*</span>
                  </label>
                  <select
                    className="sacred-input w-full"
                    value={poojaId}
                    onChange={e => { setPoojaId(e.target.value); setCustomPooja('') }}
                  >
                    <option value="">— Select a Pooja —</option>
                    {poojas.map(p => (
                      <option key={p.id} value={String(p.id)}>{p.name}</option>
                    ))}
                    <option value="other">Other (specify below)</option>
                  </select>
                  {poojas.find(p => String(p.id) === poojaId)?.description && (
                    <p className="text-xs text-stone-400 mt-1 italic">
                      {poojas.find(p => String(p.id) === poojaId)?.description}
                    </p>
                  )}
                </div>

                {/* Custom name */}
                {poojaId === 'other' && (
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-sacred-700 mb-1">
                      Pooja Name <span className="text-red-500">*</span>
                    </label>
                    <input type="text" className="sacred-input w-full"
                      placeholder="e.g. Sundarkand Path"
                      value={customPooja} onChange={e => setCustomPooja(e.target.value)} required />
                  </div>
                )}

                {/* Date */}
                <div>
                  <label className="block text-sm font-semibold text-sacred-700 mb-1">
                    Pooja Date <span className="text-red-500">*</span>
                  </label>
                  <input type="date" required className="sacred-input w-full"
                    value={scheduledDate}
                    min={todayLocal()}
                    onChange={e => setScheduledDate(e.target.value)} />
                </div>
              </div>
            </div>

            {/* ── Venue ── */}
            <div className="sacred-card p-6">
              <h2 className="font-cinzel text-lg font-bold text-sacred-800 mb-1">Venue</h2>
              <p className="text-xs text-stone-400 mb-4">Where will the Pooja be held?</p>

              {/* At My Home checkbox */}
              <label className="flex items-center gap-2 mb-4 cursor-pointer">
                <input
                  type="checkbox"
                  checked={atMyHome}
                  onChange={e => handleAtMyHomeChange(e.target.checked)}
                  className="w-4 h-4 rounded border-gold-500/50 text-gold-600 focus:ring-gold-500/30 accent-gold-500"
                />
                <span className="text-sm font-medium text-sacred-700">At My Home</span>
                <span className="text-xs text-stone-400">— Use address from my profile</span>
              </label>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

                {/* Country */}
                <div>
                  <label className="block text-sm font-semibold text-sacred-700 mb-1">Country</label>
                  <select className="sacred-input w-full" value={venueCountryCode}
                    onChange={e => { setVenueCountryCode(e.target.value); setVenueStateCode(''); setVenueCity('') }}>
                    <option value="">— Select Country —</option>
                    {venueCountries.map(c => (
                      <option key={c.isoCode} value={c.isoCode}>{c.flag} {c.name}</option>
                    ))}
                  </select>
                </div>

                {/* State */}
                <div>
                  <label className="block text-sm font-semibold text-sacred-700 mb-1">State / Province</label>
                  <select className="sacred-input w-full" value={venueStateCode}
                    onChange={e => { setVenueStateCode(e.target.value); setVenueCity('') }}
                    disabled={!venueCountryCode}>
                    <option value="">— Select State —</option>
                    {venueStates.map(s => (
                      <option key={s.isoCode} value={s.isoCode}>{s.name}</option>
                    ))}
                  </select>
                </div>

                {/* City */}
                <div>
                  <label className="block text-sm font-semibold text-sacred-700 mb-1">City</label>
                  {venueCities.length > 0 ? (
                    <select className="sacred-input w-full" value={venueCity}
                      onChange={e => setVenueCity(e.target.value)}>
                      <option value="">— Select City —</option>
                      {venueCities.map(c => (
                        <option key={c.name} value={c.name}>{c.name}</option>
                      ))}
                    </select>
                  ) : (
                    <input type="text" className="sacred-input w-full"
                      placeholder="City / Town / Village"
                      value={venueCity} onChange={e => setVenueCity(e.target.value)} />
                  )}
                </div>

                {/* Street Number */}
                <div>
                  <label className="block text-sm font-semibold text-sacred-700 mb-1">Street / Door Number</label>
                  <input type="text" className="sacred-input w-full"
                    placeholder="e.g. 42-A"
                    value={venueStreetNo} onChange={e => setVenueStreetNo(e.target.value)} />
                </div>

                {/* Street Name */}
                <div>
                  <label className="block text-sm font-semibold text-sacred-700 mb-1">Street Name</label>
                  <input type="text" className="sacred-input w-full"
                    placeholder="e.g. MG Road"
                    value={venueStreetName} onChange={e => setVenueStreetName(e.target.value)} />
                </div>

                {/* Event Place */}
                <div>
                  <label className="block text-sm font-semibold text-sacred-700 mb-1">Event Place / Hall Name</label>
                  <input type="text" className="sacred-input w-full"
                    placeholder="e.g. Sri Rama Temple, Kalyana Mandapam"
                    value={venuePlace} onChange={e => setVenuePlace(e.target.value)} />
                </div>

                {/* Google Coordinates */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-sacred-700 mb-1">
                    Google Maps Link or Coordinates
                    <span className="text-stone-400 font-normal text-xs ml-1">(optional)</span>
                  </label>
                  <input type="text" className="sacred-input w-full"
                    placeholder="https://maps.google.com/... or 17.3850° N, 78.4867° E"
                    value={venueCoords} onChange={e => setVenueCoords(e.target.value)} />
                </div>
              </div>
            </div>

            {/* ── Invite Content ── */}
            <div className="sacred-card p-6">
              <h2 className="font-cinzel text-lg font-bold text-sacred-800 mb-4">Invitation Content</h2>

              <div className="mb-4">
                <label className="block text-sm font-semibold text-sacred-700 mb-1">Invite Message</label>
                <textarea className="sacred-input w-full resize-none" rows={6}
                  placeholder={`Dear family and friends,\n\nWe are pleased to invite you to join us for our upcoming Pooja. Your presence will make this occasion truly special.\n\nWith blessings,`}
                  value={inviteMessage} onChange={e => setInviteMessage(e.target.value)} />
              </div>

              {/* Image upload */}
              <div>
                <label className="block text-sm font-semibold text-sacred-700 mb-1">
                  Pooja Image <span className="text-stone-400 font-normal text-xs">(optional)</span>
                </label>
                <div className="flex items-start gap-4">
                  <div className="flex-1">
                    <label htmlFor="img-upload"
                      className="flex items-center justify-center w-full h-28 border-2 border-dashed border-gold-400/50 rounded-lg cursor-pointer hover:border-gold-500 hover:bg-gold-500/5 transition-all">
                      <div className="text-center">
                        <span className="text-2xl">🖼️</span>
                        <p className="text-sm text-stone-500 mt-1">Click to upload image</p>
                        <p className="text-xs text-stone-400">PNG, JPG, WebP (optional)</p>
                      </div>
                    </label>
                    <input id="img-upload" ref={fileInputRef} type="file" accept="image/*"
                      className="hidden" onChange={handleImageChange} />
                  </div>
                  {imagePreview && (
                    <div className="relative shrink-0">
                      <img src={imagePreview} alt="Preview"
                        className="w-28 h-28 object-cover rounded-lg border border-gold-400" />
                      <button type="button"
                        onClick={() => { setImageFile(null); setImagePreview(null); if (fileInputRef.current) fileInputRef.current.value = '' }}
                        className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center">✕</button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* ── Invitees ── */}
            <div className="sacred-card p-6">
              <h2 className="font-cinzel text-lg font-bold text-sacred-800 mb-1">Invitees</h2>
              <p className="text-xs text-stone-400 mb-4">
                Enter Name and Email for each invitee. A new row is added automatically as you fill the last one.
              </p>
              <div className="hidden md:grid grid-cols-[2fr_2fr_3fr_auto] gap-2 mb-2 px-1">
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wide">First Name *</span>
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wide">Last Name</span>
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wide">Email *</span>
                <span />
              </div>
              <div className="space-y-2">
                {invitees.map((inv, idx) => (
                  <div key={idx} className="grid grid-cols-1 md:grid-cols-[2fr_2fr_3fr_auto] gap-2 items-center">
                    <input type="text" placeholder="First name" value={inv.name}
                      onChange={e => handleInviteeChange(idx, 'name', e.target.value)}
                      className="sacred-input text-sm" />
                    <input type="text" placeholder="Last name (optional)" value={inv.last_name}
                      onChange={e => handleInviteeChange(idx, 'last_name', e.target.value)}
                      className="sacred-input text-sm" />
                    <input type="email" placeholder="email@example.com" value={inv.email}
                      onChange={e => handleInviteeChange(idx, 'email', e.target.value)}
                      className="sacred-input text-sm" />
                    <button type="button"
                      onClick={() => setInvitees(invitees.filter((_, i) => i !== idx))}
                      disabled={invitees.length <= INITIAL_ROWS}
                      className="text-stone-300 hover:text-red-500 disabled:opacity-0 transition-colors text-lg leading-none">✕</button>
                  </div>
                ))}
              </div>
              <p className="text-xs text-stone-400 mt-3">
                {invitees.filter(i => i.name.trim() && i.email.trim()).length} valid invitee(s) entered
              </p>
            </div>

            {/* Submit */}
            <div className="flex justify-center gap-4">
              <button type="button" onClick={resetForm}
                className="sacred-btn px-8 py-2.5 opacity-70">Clear</button>
              <button type="submit" disabled={submitting}
                className="gold-btn px-10 py-2.5 text-base font-semibold disabled:opacity-60">
                {submitting ? 'Scheduling…' : '✓ Schedule Pooja'}
              </button>
            </div>
          </form>
        )}

        {/* ══ HISTORY TAB ══ */}
        {tab === 'history' && (
          <div className="space-y-4">
            {schedules.length === 0 ? (
              <div className="sacred-card p-10 text-center">
                <p className="text-3xl mb-3">🪔</p>
                <p className="text-stone-500">No scheduled poojas yet.</p>
                <button onClick={() => setTab('form')} className="gold-btn mt-4 text-sm">Schedule your first Pooja</button>
              </div>
            ) : (
              schedules.map(s => {
                const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
                const summary = rsvpSummary[s.id]
                const invitesSent = s.invitees.some(i => i.rsvp_token)
                const venue = venueOneLine(s)
                return (
                  <div key={s.id} className="sacred-card overflow-hidden">
                    <div className="p-5">
                      <div className="flex items-start gap-4">
                        {s.image_path && (
                          <img src={`${BASE}${s.image_path}`} alt="Pooja"
                            className="w-20 h-20 rounded-lg object-cover border border-gold-400/40 shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <h3 className="font-cinzel font-bold text-sacred-700 text-lg">
                              {s.pooja_name || 'Unnamed Pooja'}
                            </h3>
                            <span className="text-xs bg-gold-500/15 border border-gold-500/30 text-sacred-700 px-2 py-0.5 rounded-full font-medium">
                              {new Date(s.scheduled_date + 'T00:00:00').toLocaleDateString('en-IN', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}
                            </span>
                          </div>

                          {/* Venue line */}
                          {venue && (
                            <div className="flex items-start gap-1.5 mb-1">
                              <span className="text-stone-400 text-sm mt-0.5">📍</span>
                              <div>
                                <p className="text-sm text-stone-600">{venue}</p>
                                {s.venue_coordinates && (
                                  <a href={s.venue_coordinates.startsWith('http') ? s.venue_coordinates : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(s.venue_coordinates)}`}
                                    target="_blank" rel="noopener noreferrer"
                                    className="text-xs text-gold-600 hover:underline">
                                    Open in Maps →
                                  </a>
                                )}
                              </div>
                            </div>
                          )}

                          {s.invite_message && (
                            <p className="text-sm text-stone-600 line-clamp-2 mb-2 mt-1">{s.invite_message}</p>
                          )}

                          {/* RSVP pill counts — exclude cancelled invitees */}
                          {(() => {
                            const activeInvitees = s.invitees.filter(i => !i.cancelled_at)
                            if (activeInvitees.length === 0) return null
                            return (
                            <div className="flex flex-wrap gap-1 items-center mt-1">
                              <span className="text-xs text-stone-400 mr-1">{activeInvitees.length} invitee(s)</span>
                              {invitesSent && (
                                <>
                                  {(['attending','maybe','not_attending','pending'] as const).map(st => {
                                    const count = activeInvitees.filter(i => (i.rsvp_status || 'pending') === st).length
                                    if (!count) return null
                                    const colors: Record<string,string> = {
                                      attending: 'bg-green-100 text-green-700 border-green-200',
                                      maybe: 'bg-blue-100 text-blue-700 border-blue-200',
                                      not_attending: 'bg-red-100 text-red-600 border-red-200',
                                      pending: 'bg-stone-100 text-stone-500 border-stone-200',
                                    }
                                    const labels: Record<string,string> = { attending:'✅', maybe:'🤔', not_attending:'❌', pending:'⏳' }
                                    return (
                                      <span key={st} className={`text-xs px-2 py-0.5 rounded-full border ${colors[st]}`}>
                                        {labels[st]} {count}
                                      </span>
                                    )
                                  })}
                                </>
                              )}
                            </div>
                            )
                          })()}
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-cream-300">
                        <button onClick={() => handleSendInvites(s.id)}
                          disabled={sendingInvites === s.id || s.invitees.filter(i => !i.cancelled_at).length === 0}
                          className="flex items-center gap-1.5 text-sm bg-sacred-800 hover:bg-sacred-700 text-gold-300 px-4 py-2 rounded-lg transition-colors disabled:opacity-50 font-medium">
                          {sendingInvites === s.id ? <span className="animate-pulse">Sending…</span>
                            : <>{invitesSent ? '📨 Resend Invitations' : '📨 Send Invitations'}</>}
                        </button>
                        <button onClick={() => openEditInvitees(s)}
                          className="flex items-center gap-1.5 text-sm border border-sacred-600/40 text-sacred-700 hover:bg-sacred-100 px-4 py-2 rounded-lg transition-colors">
                          ✏️ Add More Invitees
                        </button>
                        {invitesSent && (
                          <>
                            <button onClick={() => loadRsvpSummary(s.id)}
                              className="flex items-center gap-1.5 text-sm border border-sacred-600/40 text-sacred-700 hover:bg-sacred-100 px-4 py-2 rounded-lg transition-colors">
                              {expandedRsvp === s.id ? '▲ Hide RSVP' : '📋 View RSVP'}
                            </button>
                            <button onClick={() => handleCheckDelivery(s.id)}
                              disabled={checkingDelivery === s.id}
                              className="flex items-center gap-1.5 text-sm border border-gold-500/50 text-sacred-700 hover:bg-gold-50 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                              title="Check Brevo for email delivery status">
                              {checkingDelivery === s.id ? 'Checking…' : '📬 Check delivery'}
                            </button>
                          </>
                        )}
                        <button onClick={() => handleDelete(s.id)}
                          className="ml-auto text-sm text-red-400 hover:text-red-600 border border-red-200 hover:border-red-400 px-3 py-2 rounded-lg transition-colors">
                          Delete
                        </button>
                      </div>
                    </div>

                    {/* RSVP summary panel */}
                    {expandedRsvp === s.id && summary && (
                      <div className="border-t border-cream-300 bg-cream-100 p-5">
                        <h4 className="font-cinzel font-bold text-sacred-700 text-sm mb-3">RSVP Status</h4>
                        <div className="flex flex-wrap gap-2 mb-4">
                          {[
                            { key:'attending',     label:'Attending',    emoji:'✅', cls:'bg-green-100 text-green-700 border-green-200' },
                            { key:'maybe',         label:'Maybe',        emoji:'🤔', cls:'bg-blue-100 text-blue-700 border-blue-200'   },
                            { key:'not_attending', label:"Can't attend", emoji:'❌', cls:'bg-red-100 text-red-600 border-red-200'      },
                            { key:'pending',       label:'Pending',      emoji:'⏳', cls:'bg-stone-100 text-stone-600 border-stone-200' },
                            { key:'cancelled',     label:'Cancelled',    emoji:'🚫', cls:'bg-stone-200 text-stone-600 border-stone-300' },
                          ].map(({ key, label, emoji, cls }) => ((summary as any)[key] || 0) > 0 ? (
                            <span key={key} className={`text-xs font-medium px-3 py-1 rounded-full border ${cls}`}>
                              {emoji} {label}: {(summary as any)[key]}
                            </span>
                          ) : null)}
                        </div>
                        {summary.invitees.some(i => i.email_delivery_status === 'sent') && (
                          <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-3">
                            💡 If invitees don&apos;t see the email, ask them to check <strong>Spam</strong>. Ensure your sender domain is verified in Brevo (Senders &amp; IP).
                          </p>
                        )}
                        <div className="space-y-2">
                          {summary.invitees.map(inv => (
                            <div key={inv.id} className={`flex items-center justify-between gap-3 rounded-lg border px-3 py-2.5 ${
                              inv.status === 'cancelled' ? 'bg-stone-100 border-stone-300 opacity-75' : 'bg-white border-cream-300'
                            }`}>
                              <div className="min-w-0">
                                <p className={`text-sm font-medium truncate ${inv.status === 'cancelled' ? 'text-stone-500 line-through' : 'text-sacred-700'} ${inv.email_delivery_status === 'delivered' ? 'font-bold' : ''}`}>
                                  {inv.name}
                                  {inv.email_delivery_status === 'delivered' && <span className="ml-1 text-xs text-green-600 font-normal">✓ Delivered</span>}
                                  {inv.email_delivery_status === 'sent' && <span className="ml-1 text-xs text-amber-600 font-normal" title="Brevo accepted the email. If not received, ask recipient to check spam.">Sent</span>}
                                </p>
                                <p className="text-xs text-stone-400 truncate">{inv.email}</p>
                                {inv.notes && inv.status !== 'cancelled' && <p className="text-xs italic text-stone-500 mt-0.5">&ldquo;{inv.notes}&rdquo;</p>}
                                {inv.status === 'cancelled' && inv.cancelled_reason && <p className="text-xs italic text-stone-500 mt-0.5">Reason: {inv.cancelled_reason}</p>}
                                {inv.status === 'attending' && inv.attending_members && inv.attending_members.length > 0 && (
                                  <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs">
                                    <p className="font-medium text-green-800 mb-1">Attendees (for recitation):</p>
                                    {inv.attending_members.map((m, i) => (
                                      <p key={i} className="text-green-700">
                                        {m.name || m.unique_id}{m.nakshatra ? ` — ${m.nakshatra}` : ''}{m.gotra ? ` (${m.gotra})` : ''}
                                      </p>
                                    ))}
                                  </div>
                                )}
                              </div>
                              <div className="flex items-center gap-2 shrink-0">
                                {inv.status !== 'cancelled' && inv.rsvp_token && (
                                  <button
                                    onClick={() => { navigator.clipboard.writeText(`${window.location.origin}/rsvp/${inv.rsvp_token}`); toast.success('RSVP link copied!') }}
                                    className="text-xs text-gold-600 hover:text-gold-700 border border-gold-400/30 px-2 py-1 rounded" title="Copy RSVP link">
                                    🔗 Link
                                  </button>
                                )}
                                {inv.status !== 'cancelled' && (
                                  <button
                                    onClick={() => handleResendInvite(s.id, inv.id)}
                                    disabled={!!resendingInvitee}
                                    className="text-xs text-sacred-700 hover:text-sacred-900 border border-sacred-400/40 px-2 py-1 rounded disabled:opacity-50" title="Resend invite">
                                    {resendingInvitee?.scheduleId === s.id && resendingInvitee?.inviteeId === inv.id ? 'Sending…' : '📨 Resend'}
                                  </button>
                                )}
                                {inv.status !== 'cancelled' && (
                                  <button
                                    onClick={() => openCancelModal(s.id, inv.id, inv.name)}
                                    className="text-xs text-red-500 hover:text-red-700 border border-red-200 px-2 py-1 rounded" title="Cancel invite">
                                    Cancel
                                  </button>
                                )}
                                <span className={`text-xs px-2 py-1 rounded-full font-medium border ${
                                  inv.status === 'attending'     ? 'bg-green-100 text-green-700 border-green-200'   :
                                  inv.status === 'not_attending' ? 'bg-red-100 text-red-600 border-red-200'         :
                                  inv.status === 'maybe'         ? 'bg-blue-100 text-blue-700 border-blue-200'      :
                                  inv.status === 'cancelled'     ? 'bg-stone-200 text-stone-600 border-stone-300'   :
                                  'bg-stone-100 text-stone-500 border-stone-200'
                                }`}>
                                  {inv.status === 'attending' ? '✅ Attending' : inv.status === 'not_attending' ? "❌ Can't attend" : inv.status === 'maybe' ? '🤔 Maybe' : inv.status === 'cancelled' ? '🚫 Cancelled' : '⏳ Pending'}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })
            )}
          </div>
        )}

        {/* Add More Invitees Modal */}
        {editingScheduleId && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="sacred-card p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <h3 className="font-cinzel text-xl font-bold text-sacred-800 mb-4">Add More Invitees</h3>
              <form onSubmit={handleAddMoreInvitees} className="space-y-4">
                <div className="space-y-2">
                  {addMoreInvitees.map((inv, idx) => (
                    <div key={idx} className="grid grid-cols-1 md:grid-cols-[2fr_2fr_3fr_auto] gap-2 items-center">
                      <input type="text" placeholder="First name" value={inv.name}
                        onChange={e => {
                          const u = addMoreInvitees.map((i, j) => j === idx ? { ...i, name: e.target.value } : i)
                          if (idx === u.length - 1 && e.target.value.trim()) u.push(EMPTY_INVITEE())
                          setAddMoreInvitees(u)
                        }}
                        className="sacred-input text-sm" />
                      <input type="text" placeholder="Last name" value={inv.last_name}
                        onChange={e => setAddMoreInvitees(addMoreInvitees.map((i, j) => j === idx ? { ...i, last_name: e.target.value } : i))}
                        className="sacred-input text-sm" />
                      <input type="email" placeholder="email@example.com" value={inv.email}
                        onChange={e => {
                          const u = addMoreInvitees.map((i, j) => j === idx ? { ...i, email: e.target.value } : i)
                          if (idx === u.length - 1 && e.target.value.trim()) u.push(EMPTY_INVITEE())
                          setAddMoreInvitees(u)
                        }}
                        className="sacred-input text-sm" />
                      <button type="button"
                        onClick={() => setAddMoreInvitees(addMoreInvitees.filter((_, i) => i !== idx))}
                        disabled={addMoreInvitees.length <= 1}
                        className="text-stone-300 hover:text-red-500 disabled:opacity-0 text-lg">✕</button>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2 pt-2">
                  <button type="button" onClick={() => setEditingScheduleId(null)}
                    className="sacred-btn px-4 py-2">Cancel</button>
                  <button type="submit" disabled={addingInvitees}
                    className="gold-btn px-4 py-2 disabled:opacity-60">
                    {addingInvitees ? 'Adding…' : 'Add Invitees'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Cancel Invite Modal */}
        {cancelModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="sacred-card p-6 max-w-md w-full">
              <h3 className="font-cinzel text-xl font-bold text-sacred-800 mb-2">Cancel Invitation</h3>
              <p className="text-sm text-stone-600 mb-4">Cancel invitation for <strong>{cancelModal.name}</strong>? They will receive an email notification.</p>
              <div className="mb-4">
                <label className="block text-sm font-medium text-sacred-700 mb-1">Reason (optional)</label>
                <textarea
                  value={cancelReason}
                  onChange={e => setCancelReason(e.target.value)}
                  placeholder="e.g. Event postponed, venue change..."
                  className="sacred-input w-full resize-none" rows={3}
                />
              </div>
              <div className="flex gap-2">
                <button type="button" onClick={() => { setCancelModal(null); setCancelReason('') }}
                  className="sacred-btn px-4 py-2">Keep Invitation</button>
                <button
                  onClick={handleCancelInvite}
                  disabled={!!cancellingInvitee}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md font-medium disabled:opacity-60">
                  {cancellingInvitee ? 'Cancelling…' : 'Cancel Invitation'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
