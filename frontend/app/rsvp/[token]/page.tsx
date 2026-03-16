'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import axios from 'axios'
import Link from 'next/link'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'

function getApiUrl(): string {
  if (typeof window !== 'undefined') {
    const host = window.location.hostname
    if (host.includes('poojasankalp.org')) return 'https://api.poojasankalp.org'
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface Invitation {
  schedule_id: number
  invitee_id: number
  invitee_name: string
  invitee_last_name?: string
  pooja_name: string
  scheduled_date: string
  invite_message?: string
  image_path?: string
  host_name: string
  rsvp_status: string
  rsvp_notes?: string
  attending_members?: string
  venue_place?: string
  venue_street_number?: string
  venue_street_name?: string
  venue_city?: string
  venue_state?: string
  venue_country?: string
  venue_coordinates?: string
}

interface MemberInfo {
  unique_id: string
  display_name: string
  relation?: string
  nakshatra?: string
  gotra?: string
}

type RsvpStatus = 'attending' | 'not_attending' | 'maybe'
type UIStep = 'view' | 'rsvp' | 'attending_details' | 'done'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(iso: string) {
  try {
    if (!iso || typeof iso !== 'string') return String(iso ?? '')
    const dateStr = iso.includes('T') ? iso : iso + 'T00:00:00'
    const d = new Date(dateStr)
    return isNaN(d.getTime()) ? iso : d.toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
  } catch { return String(iso ?? '') }
}

/** Parse attending_members JSON. Supports [{unique_id,name,...}] and [uid,...]. */
function parseAttendingMembers(raw: string | undefined): string[] {
  if (!raw || typeof raw !== 'string') return []
  try {
    const data = JSON.parse(raw)
    if (!Array.isArray(data)) return []
    return data.map((item: unknown) =>
      typeof item === 'object' && item !== null && 'unique_id' in item
        ? String((item as { unique_id: string }).unique_id)
        : String(item)
    )
  } catch {
    return []
  }
}

const STATUS_META: Record<string, { label: string; emoji: string; color: string }> = {
  pending:        { label: 'Awaiting your response', emoji: '⏳', color: 'text-amber-600' },
  attending:      { label: 'You are attending',      emoji: '✅', color: 'text-green-600' },
  not_attending:  { label: 'Unable to attend',       emoji: '❌', color: 'text-red-500'   },
  maybe:          { label: 'Maybe attending',        emoji: '🤔', color: 'text-blue-500'  },
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function RsvpPage() {
  const { token } = useParams<{ token: string }>()
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()

  const [inv, setInv] = useState<Invitation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // RSVP form state
  const [step, setStep] = useState<UIStep>('view')
  const [chosenStatus, setChosenStatus] = useState<RsvpStatus | null>(null)
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  // Family selection (for attending) — uses logged-in user's family
  const [members, setMembers] = useState<MemberInfo[]>([])
  const [membersLoading, setMembersLoading] = useState(false)
  const [selectedMembers, setSelectedMembers] = useState<string[]>([])

  // ── Load invitation ────────────────────────────────────────────────────────
  useEffect(() => {
    const t = typeof token === 'string' ? token : Array.isArray(token) ? token[0] : ''
    if (!t) {
      setError('Invalid invitation link.')
      setLoading(false)
      return
    }
    const apiUrl = getApiUrl()
    axios.get(`${apiUrl}/api/rsvp/view/${t}`)
      .then(r => {
        setInv(r.data)
        if (r.data.rsvp_status !== 'pending') {
          setChosenStatus(r.data.rsvp_status)
          setNotes(r.data.rsvp_notes || '')
          setStep('done')
          setSubmitted(true)
        }
      })
      .catch((err) => {
        const msg = err.response?.status === 404
          ? 'Invitation not found or the link has expired.'
          : err.response?.data?.detail || 'Could not load invitation. Please check your connection.'
        setError(msg)
      })
      .finally(() => setLoading(false))
  }, [token])

  // ── Load family when user selects "Attending" and is logged in ───────────────
  // When returning to change response, pre-select previously saved attending members
  const existingAttendingIds = inv ? parseAttendingMembers(inv.attending_members) : []
  useEffect(() => {
    if (chosenStatus === 'attending' && user && members.length === 0 && !membersLoading) {
      setMembersLoading(true)
      api.get('/api/rsvp/my-family')
        .then(r => {
          const family = r.data as MemberInfo[]
          setMembers(family)
          const ids = existingAttendingIds.length > 0
            ? existingAttendingIds.filter(id => family.some(m => m.unique_id === id))
            : []
          setSelectedMembers(ids.length > 0 ? ids : family.map(m => m.unique_id))
        })
        .catch(() => setMembers([]))
        .finally(() => setMembersLoading(false))
    } else if (chosenStatus !== 'attending') {
      setMembers([])
      setSelectedMembers([])
    }
  }, [chosenStatus, user, existingAttendingIds.join(',')])

  const toggleMember = (uid: string) =>
    setSelectedMembers(prev =>
      prev.includes(uid) ? prev.filter(x => x !== uid) : [...prev, uid]
    )

  // ── Submit RSVP (requires login) ────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!chosenStatus) return
    if (!user) {
      alert('Please log in or create an account to accept this invitation.')
      return
    }
    if (chosenStatus === 'attending' && selectedMembers.length === 0) {
      alert('Please select at least one family member who will be attending.')
      return
    }
    setSubmitting(true)
    try {
      const t = typeof token === 'string' ? token : Array.isArray(token) ? token[0] : ''
      const attending_members = chosenStatus === 'attending' && selectedMembers.length > 0
        ? members
            .filter(m => selectedMembers.includes(m.unique_id))
            .map(m => ({
              unique_id: m.unique_id,
              name: m.display_name,
              nakshatra: m.nakshatra || null,
              gotra: m.gotra || null,
              relation: m.relation || null,
            }))
        : null
      await api.post(`/api/rsvp/view/${t}`, {
        status: chosenStatus,
        notes: notes || null,
        attending_members,
      })
      setSubmitted(true)
      setStep('done')
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'Failed to submit. Please try again.'
      if (e.response?.status === 401) {
        alert('Please log in to accept this invitation.')
      } else {
        alert(msg)
      }
    } finally {
      setSubmitting(false)
    }
  }

  // ── Loading / error states ─────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sacred-950 via-sacred-900 to-sacred-950 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4 animate-pulse">🪔</div>
          <p className="text-gold-400 font-cinzel text-lg">Loading your invitation…</p>
        </div>
      </div>
    )
  }

  if (error || !inv) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sacred-950 to-sacred-900 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="text-5xl mb-4">😔</div>
          <h2 className="font-cinzel text-2xl text-gold-400 mb-2">Invitation Not Found</h2>
          <p className="text-cream-300">{error}</p>
          <Link href="/" className="mt-6 inline-block gold-btn text-sm">Go to Home</Link>
        </div>
      </div>
    )
  }

  const statusMeta = STATUS_META[inv.rsvp_status] || STATUS_META.pending
  const inviteeName = `${inv.invitee_name}${inv.invitee_last_name ? ' ' + inv.invitee_last_name : ''}`

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#1a0e06] via-[#231208] to-[#1a0e06]">

      {/* ── Decorative header ── */}
      <div className="text-center pt-10 pb-2 px-4">
        <p className="text-gold-400/70 text-xs tracking-widest uppercase mb-1 font-cinzel">Pooja Sankalpam</p>
        <div className="flex items-center justify-center gap-3">
          <span className="text-gold-500/40 text-2xl">—✦—</span>
          <h1 className="font-cinzel text-3xl md:text-4xl font-bold text-gold-300">
            You&apos;re Invited
          </h1>
          <span className="text-gold-500/40 text-2xl">—✦—</span>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">

        {/* ── Invitation card ── */}
        <div className="rounded-2xl overflow-hidden border border-gold-500/30 shadow-2xl"
             style={{ background: 'linear-gradient(145deg,#2d1b0e,#3a2010)' }}>

          {/* Image */}
          {inv.image_path && (
            <img
              src={`${getApiUrl()}${inv.image_path}`}
              alt="Pooja"
              className="w-full max-h-64 object-cover"
            />
          )}

          {/* Pooja info */}
          <div className="p-6 md:p-8">
            <div className="text-center mb-6">
              <div className="inline-flex items-center gap-2 bg-gold-500/10 border border-gold-500/30 rounded-full px-4 py-1.5 mb-3">
                <span className="text-gold-400 text-sm font-semibold font-cinzel">{inv.pooja_name}</span>
              </div>
              <div className="flex items-center justify-center gap-2 text-cream-300 text-sm mb-1">
                <span>📅</span>
                <span className="font-medium">{formatDate(inv.scheduled_date)}</span>
              </div>
              <p className="text-cream-400/70 text-xs mb-2">Hosted by <span className="text-gold-400">{inv.host_name}</span></p>
              {/* Venue */}
              {(inv.venue_place || inv.venue_city || inv.venue_country) && (
                <div className="inline-flex items-start gap-1.5 text-xs text-cream-400/80 bg-black/20 rounded-lg px-3 py-2 mt-1">
                  <span className="mt-0.5">📍</span>
                  <div className="text-left">
                    {inv.venue_place && <p className="font-medium text-cream-300">{inv.venue_place}</p>}
                    {(inv.venue_street_number || inv.venue_street_name) && (
                      <p>{[inv.venue_street_number, inv.venue_street_name].filter(Boolean).join(' ')}</p>
                    )}
                    {(inv.venue_city || inv.venue_state || inv.venue_country) && (
                      <p>{[inv.venue_city, inv.venue_state, inv.venue_country].filter(Boolean).join(', ')}</p>
                    )}
                    {inv.venue_coordinates && (
                      <a href={String(inv.venue_coordinates).startsWith('http') ? inv.venue_coordinates : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(inv.venue_coordinates)}`}
                        target="_blank" rel="noopener noreferrer"
                        className="text-gold-400 hover:text-gold-300 underline underline-offset-2">
                        Open in Maps →
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Dear invitee */}
            <div className="bg-black/20 border border-gold-500/10 rounded-xl p-5 mb-6">
              <p className="text-cream-200 text-base mb-3">
                Dear <strong className="text-gold-300">{inviteeName}</strong>,
              </p>
              {inv.invite_message && typeof inv.invite_message === 'string' ? (
                inv.invite_message.split('\n').filter(l => l.trim()).map((line, i) => (
                  <p key={i} className="text-cream-300 text-sm leading-relaxed mb-2">{line}</p>
                ))
              ) : (
                <p className="text-cream-400 text-sm italic">
                  You have been cordially invited to attend this sacred ceremony.
                </p>
              )}
            </div>

            {/* Current RSVP status badge */}
            {inv.rsvp_status !== 'pending' && (
              <div className="flex items-center gap-2 justify-center mb-4">
                <span className={`text-sm font-semibold ${statusMeta.color}`}>
                  {statusMeta.emoji} {statusMeta.label}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* ── STEP: View → pick response ── */}
        {(step === 'view' || step === 'rsvp') && (
          <div className="rounded-2xl border border-gold-500/20 p-6 md:p-8"
               style={{ background: 'linear-gradient(145deg,#2d1b0e,#3a2010)' }}>
            <h2 className="font-cinzel text-xl font-bold text-gold-300 text-center mb-6">
              Will you be attending?
            </h2>

            <div className="grid grid-cols-3 gap-3 mb-6">
              {[
                { status: 'attending',      label: "Yes, I'll attend!",  emoji: '✅', bg: 'hover:bg-green-900/40 hover:border-green-500', selected: 'bg-green-900/60 border-green-500 ring-2 ring-green-500/30' },
                { status: 'maybe',          label: "Maybe",              emoji: '🤔', bg: 'hover:bg-blue-900/40 hover:border-blue-500',  selected: 'bg-blue-900/60 border-blue-500 ring-2 ring-blue-500/30'   },
                { status: 'not_attending',  label: "Can't make it",      emoji: '❌', bg: 'hover:bg-red-900/40 hover:border-red-500',    selected: 'bg-red-900/60 border-red-500 ring-2 ring-red-500/30'     },
              ].map(opt => (
                <button
                  key={opt.status}
                  onClick={() => { setChosenStatus(opt.status as RsvpStatus); setStep('rsvp') }}
                  className={`flex flex-col items-center justify-center gap-2 rounded-xl border p-4 transition-all cursor-pointer
                    ${chosenStatus === opt.status ? opt.selected : `border-gold-500/20 ${opt.bg}`}`}
                >
                  <span className="text-3xl">{opt.emoji}</span>
                  <span className="text-xs text-cream-300 text-center leading-tight">{opt.label}</span>
                </button>
              ))}
            </div>

            {/* Notes */}
            {chosenStatus && (
              <div className="mb-5">
                <label className="block text-sm text-cream-400 mb-1">Message to host (optional)</label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                  placeholder="Add a personal note…"
                  className="w-full bg-black/30 border border-gold-500/20 rounded-lg px-3 py-2 text-cream-200 text-sm placeholder-cream-600 focus:outline-none focus:border-gold-500/50 resize-none"
                />
              </div>
            )}

            {/* If attending → select family members (Names, Nakshatra, Gothra for recitation) */}
            {chosenStatus === 'attending' && (
              <div className="mb-6 rounded-xl border border-gold-500/20 bg-black/20 p-5">
                <p className="text-gold-300 font-semibold text-sm mb-3 font-cinzel">
                  🪔 Who will be attending?
                </p>
                <p className="text-cream-400 text-xs mb-4">
                  Select family members so the host can plan and recite Names, Nakshatra & Gothra during the pooja.
                </p>

                {!user ? (
                  <div className="rounded-lg bg-amber-900/30 border border-amber-500/30 p-4 text-center">
                    <p className="text-amber-200 text-sm mb-3">Please log in or create an account to accept this invitation.</p>
                    <div className="flex gap-3 justify-center flex-wrap">
                      <Link
                        href={`/login?returnUrl=${encodeURIComponent(`/rsvp/${typeof token === 'string' ? token : Array.isArray(token) ? token[0] : ''}`)}`}
                        className="inline-block bg-gold-500 hover:bg-gold-400 text-sacred-950 font-bold text-sm px-5 py-2 rounded-lg"
                      >
                        Log in
                      </Link>
                      <Link
                        href={`/register?returnUrl=${encodeURIComponent(`/rsvp/${typeof token === 'string' ? token : Array.isArray(token) ? token[0] : ''}`)}`}
                        className="inline-block bg-sacred-600 hover:bg-sacred-500 text-cream-100 font-bold text-sm px-5 py-2 rounded-lg"
                      >
                        Create account
                      </Link>
                    </div>
                  </div>
                ) : membersLoading ? (
                  <p className="text-cream-400 text-sm">Loading your family…</p>
                ) : members.length > 0 ? (
                  <div>
                    <p className="text-cream-400 text-xs mb-2">Select who will be attending (required):</p>
                    <div className="space-y-2">
                      {members.map(m => (
                        <label key={m.unique_id}
                          className="flex items-center gap-3 cursor-pointer rounded-lg border border-gold-500/10 hover:border-gold-500/30 bg-black/20 px-3 py-2.5 transition-colors">
                          <input
                            type="checkbox"
                            checked={selectedMembers.includes(m.unique_id)}
                            onChange={() => toggleMember(m.unique_id)}
                            className="accent-gold-500 w-4 h-4 cursor-pointer"
                          />
                          <span className="flex-1 text-cream-200 text-sm">{m.display_name}</span>
                          {m.relation && (
                            <span className="text-xs text-gold-500/70 bg-gold-500/10 px-2 py-0.5 rounded-full">{m.relation}</span>
                          )}
                          {(m.nakshatra || m.gotra) && (
                            <span className="text-xs text-cream-500">
                              {[m.nakshatra, m.gotra].filter(Boolean).join(' • ')}
                            </span>
                          )}
                        </label>
                      ))}
                    </div>
                    <p className="text-xs text-cream-500 mt-2">
                      {selectedMembers.length} member(s) selected — Names, Nakshatra & Gothra will be shared with the host for recitation.
                    </p>
                  </div>
                ) : (
                  <p className="text-cream-400 text-sm">Add family members in your profile to select attendees.</p>
                )}
              </div>
            )}

            {/* Submit button — hide when attending but not logged in */}
            {chosenStatus && !(chosenStatus === 'attending' && !user) && (
              <button
                onClick={handleSubmit}
                disabled={submitting || (chosenStatus === 'attending' && selectedMembers.length === 0)}
                className="w-full py-3 rounded-xl font-cinzel font-bold text-base transition-all disabled:opacity-60
                  bg-gradient-to-r from-gold-600 to-gold-500 hover:from-gold-500 hover:to-gold-400 text-sacred-950"
              >
                {submitting ? 'Submitting…' : 'Confirm RSVP →'}
              </button>
            )}
          </div>
        )}

        {/* ── STEP: Done ── */}
        {step === 'done' && submitted && (
          <div className="rounded-2xl border border-gold-500/20 p-8 text-center"
               style={{ background: 'linear-gradient(145deg,#2d1b0e,#3a2010)' }}>
            {chosenStatus === 'attending' && (
              <>
                <div className="text-5xl mb-4">🙏</div>
                <h3 className="font-cinzel text-2xl text-gold-300 font-bold mb-2">See you there!</h3>
                <p className="text-cream-300 text-sm mb-1">Your RSVP has been recorded.</p>
                {selectedMembers.length > 0 && (
                  <p className="text-green-400 text-sm mt-2">
                    ✅ {selectedMembers.length} family member(s) — Names, Nakshatra & Gothra shared with the host for recitation.
                  </p>
                )}
              </>
            )}
            {chosenStatus === 'not_attending' && (
              <>
                <div className="text-5xl mb-4">🙏</div>
                <h3 className="font-cinzel text-2xl text-gold-300 font-bold mb-2">Thank you for responding</h3>
                <p className="text-cream-300 text-sm">We&apos;re sorry you can&apos;t make it. You&apos;ll be missed!</p>
              </>
            )}
            {chosenStatus === 'maybe' && (
              <>
                <div className="text-5xl mb-4">🤔</div>
                <h3 className="font-cinzel text-2xl text-gold-300 font-bold mb-2">No worries!</h3>
                <p className="text-cream-300 text-sm">We hope to see you there. You can update your RSVP any time.</p>
              </>
            )}
            {notes && (
              <div className="mt-4 bg-black/20 rounded-lg p-3 text-left">
                <p className="text-xs text-cream-500 mb-1">Your message:</p>
                <p className="text-cream-300 text-sm italic">&ldquo;{notes}&rdquo;</p>
              </div>
            )}

            {/* Allow changing response or updating family members */}
            <div className="mt-6 pt-4 border-t border-gold-500/20">
              <p className="text-cream-400 text-sm mb-2">Need to update?</p>
              <button
                onClick={() => { setStep('view'); setSubmitted(false) }}
                className="text-gold-400 hover:text-gold-300 font-medium underline underline-offset-2"
              >
                Change my response or update family members →
              </button>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center pb-6">
          <div className="flex items-center justify-center gap-2 text-gold-500/30 text-lg mb-2">
            <span>—✦—</span>
          </div>
          <p className="text-cream-600 text-xs">
            Powered by{' '}
            <a href="/" className="text-gold-500/60 hover:text-gold-400 transition-colors">Pooja Sankalpam</a>
          </p>
        </div>
      </div>
    </div>
  )
}
