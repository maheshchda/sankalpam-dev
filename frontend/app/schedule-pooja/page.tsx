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

interface RsvpSummary {
  attending: number
  not_attending: number
  maybe: number
  pending: number
  invitees: {
    id: number
    name: string
    email: string
    status: string
    notes?: string
    rsvp_token?: string
  }[]
}

const EMPTY_INVITEE = (): Invitee => ({ name: '', last_name: '', email: '' })
const INITIAL_ROWS = 5

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
  const [poojaRegionCountry, setPoojaRegionCountry] = useState('IN')  // For filtering pooja list by state
  const [poojaRegionState, setPoojaRegionState] = useState('')
  const [poojas, setPoojas] = useState<Pooja[]>([])
  const [poojaId, setPoojaId] = useState('')
  const [customPooja, setCustomPooja] = useState('')
  const [scheduledDate, setScheduledDate] = useState('')

  const poojaRegionStates = useMemo(
    () => poojaRegionCountry ? State.getStatesOfCountry(poojaRegionCountry) : [],
    [poojaRegionCountry]
  )

  // ── Invite content ───────────────────────────────────────────────────────
  const [inviteMessage, setInviteMessage] = useState('')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // ── Venue ────────────────────────────────────────────────────────────────
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

  // ── Fetch schedules on mount ─────────────────────────────────────────────
  useEffect(() => {
    if (!user) return
    fetchSchedules()
  }, [user])

  // ── Fetch poojas (filtered by state when selected) ───────────────────────
  useEffect(() => {
    if (!user) return
    const stateParam = poojaRegionCountry && poojaRegionState
      ? `?state=${poojaRegionCountry}-${poojaRegionState}`
      : ''
    api.get(`/api/pooja/list${stateParam}`).then(r => setPoojas(r.data)).catch(() => {})
  }, [user, poojaRegionCountry, poojaRegionState])

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
    setInviteMessage(''); setImageFile(null); setImagePreview(null)
    setVenuePlace(''); setVenueStreetNo(''); setVenueStreetName('')
    setVenueCountryCode(''); setVenueStateCode(''); setVenueCity(''); setVenueCoords('')
    setInvitees(Array.from({ length: INITIAL_ROWS }, EMPTY_INVITEE))
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!scheduledDate) { toast.error('Please select a date.'); return }
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
      const { sent, skipped, total } = r.data
      if (skipped.length > 0) {
        toast.warn(`Sent ${sent}/${total}. RSVP links generated — share manually if needed.`)
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
                    min={new Date().toISOString().split('T')[0]}
                    onChange={e => setScheduledDate(e.target.value)} />
                </div>
              </div>
            </div>

            {/* ── Venue ── */}
            <div className="sacred-card p-6">
              <h2 className="font-cinzel text-lg font-bold text-sacred-800 mb-1">Venue</h2>
              <p className="text-xs text-stone-400 mb-4">Where will the Pooja be held?</p>

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

                          {/* RSVP pill counts */}
                          {s.invitees.length > 0 && (
                            <div className="flex flex-wrap gap-1 items-center mt-1">
                              <span className="text-xs text-stone-400 mr-1">{s.invitees.length} invitee(s)</span>
                              {invitesSent && (
                                <>
                                  {(['attending','maybe','not_attending','pending'] as const).map(st => {
                                    const count = s.invitees.filter(i => (i.rsvp_status || 'pending') === st).length
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
                          )}
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-cream-300">
                        <button onClick={() => handleSendInvites(s.id)}
                          disabled={sendingInvites === s.id || s.invitees.length === 0}
                          className="flex items-center gap-1.5 text-sm bg-sacred-800 hover:bg-sacred-700 text-gold-300 px-4 py-2 rounded-lg transition-colors disabled:opacity-50 font-medium">
                          {sendingInvites === s.id ? <span className="animate-pulse">Sending…</span>
                            : <>{invitesSent ? '📨 Resend Invitations' : '📨 Send Invitations'}</>}
                        </button>
                        {invitesSent && (
                          <button onClick={() => loadRsvpSummary(s.id)}
                            className="flex items-center gap-1.5 text-sm border border-sacred-600/40 text-sacred-700 hover:bg-sacred-100 px-4 py-2 rounded-lg transition-colors">
                            {expandedRsvp === s.id ? '▲ Hide RSVP' : '📋 View RSVP'}
                          </button>
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
                          ].map(({ key, label, emoji, cls }) => (
                            <span key={key} className={`text-xs font-medium px-3 py-1 rounded-full border ${cls}`}>
                              {emoji} {label}: {(summary as any)[key] || 0}
                            </span>
                          ))}
                        </div>
                        <div className="space-y-2">
                          {summary.invitees.map(inv => (
                            <div key={inv.id} className="flex items-center justify-between gap-3 bg-white rounded-lg border border-cream-300 px-3 py-2.5">
                              <div className="min-w-0">
                                <p className="text-sm font-medium text-sacred-700 truncate">{inv.name}</p>
                                <p className="text-xs text-stone-400 truncate">{inv.email}</p>
                                {inv.notes && <p className="text-xs italic text-stone-500 mt-0.5">&ldquo;{inv.notes}&rdquo;</p>}
                              </div>
                              <div className="flex items-center gap-2 shrink-0">
                                {inv.rsvp_token && (
                                  <button
                                    onClick={() => { navigator.clipboard.writeText(`${window.location.origin}/rsvp/${inv.rsvp_token}`); toast.success('RSVP link copied!') }}
                                    className="text-xs text-gold-600 hover:text-gold-700 border border-gold-400/30 px-2 py-1 rounded" title="Copy RSVP link">
                                    🔗 Link
                                  </button>
                                )}
                                <span className={`text-xs px-2 py-1 rounded-full font-medium border ${
                                  inv.status === 'attending'     ? 'bg-green-100 text-green-700 border-green-200'   :
                                  inv.status === 'not_attending' ? 'bg-red-100 text-red-600 border-red-200'         :
                                  inv.status === 'maybe'         ? 'bg-blue-100 text-blue-700 border-blue-200'      :
                                  'bg-stone-100 text-stone-500 border-stone-200'
                                }`}>
                                  {inv.status === 'attending' ? '✅ Attending' : inv.status === 'not_attending' ? "❌ Can't attend" : inv.status === 'maybe' ? '🤔 Maybe' : '⏳ Pending'}
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
      </div>
    </div>
  )
}
