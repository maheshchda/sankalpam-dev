'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import axios from 'axios'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ─── Types ────────────────────────────────────────────────────────────────────

interface Invitation {
  schedule_id: number
  invitee_id: number
  invitee_name: string
  invitee_last_name?: string
  pooja_name: string
  scheduled_date: string   // YYYY-MM-DD
  invite_message?: string
  image_path?: string
  host_name: string
  rsvp_status: string      // pending / attending / not_attending / maybe
  rsvp_notes?: string
  attending_members?: string  // JSON
}

interface MemberInfo {
  unique_id: string
  display_name: string
  relation?: string
}

type RsvpStatus = 'attending' | 'not_attending' | 'maybe'
type UIStep = 'view' | 'rsvp' | 'attending_details' | 'done'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(iso: string) {
  try {
    const d = new Date(iso + 'T00:00:00')
    return d.toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
  } catch { return iso }
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

  const [inv, setInv] = useState<Invitation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // RSVP form state
  const [step, setStep] = useState<UIStep>('view')
  const [chosenStatus, setChosenStatus] = useState<RsvpStatus | null>(null)
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  // Unique ID flow
  const [uidOption, setUidOption] = useState<'new' | 'existing' | null>(null)
  const [uniqueId, setUniqueId] = useState('')
  const [uidLoading, setUidLoading] = useState(false)
  const [uidError, setUidError] = useState('')
  const [members, setMembers] = useState<MemberInfo[]>([])
  const [selectedMembers, setSelectedMembers] = useState<string[]>([])

  // ── Load invitation ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!token) return
    axios.get(`${API}/api/rsvp/view/${token}`)
      .then(r => {
        setInv(r.data)
        if (r.data.rsvp_status !== 'pending') {
          setChosenStatus(r.data.rsvp_status)
          setNotes(r.data.rsvp_notes || '')
          setStep('done')
          setSubmitted(true)
        }
      })
      .catch(() => setError('Invitation not found or the link has expired.'))
      .finally(() => setLoading(false))
  }, [token])

  // ── Lookup Unique ID ───────────────────────────────────────────────────────
  const handleLookupUid = async () => {
    const uid = uniqueId.trim().toUpperCase()
    if (!uid) { setUidError('Please enter your Unique ID.'); return }
    setUidError('')
    setUidLoading(true)
    try {
      const r = await axios.get(`${API}/api/rsvp/members/${uid}`)
      setMembers(r.data)
      setSelectedMembers(r.data.map((m: MemberInfo) => m.unique_id))
    } catch {
      setUidError('No Sankalpam account found with this Unique ID. Please check and try again.')
      setMembers([])
    } finally {
      setUidLoading(false)
    }
  }

  const toggleMember = (uid: string) =>
    setSelectedMembers(prev =>
      prev.includes(uid) ? prev.filter(x => x !== uid) : [...prev, uid]
    )

  // ── Submit RSVP ────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!chosenStatus) return
    setSubmitting(true)
    try {
      await axios.post(`${API}/api/rsvp/view/${token}`, {
        status: chosenStatus,
        notes: notes || null,
        unique_id: uidOption === 'existing' && uniqueId.trim() ? uniqueId.trim().toUpperCase() : null,
        attending_member_ids: uidOption === 'existing' && members.length > 0 ? selectedMembers : null,
      })
      setSubmitted(true)
      setStep('done')
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to submit. Please try again.')
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
              src={`${API}${inv.image_path}`}
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
              <p className="text-cream-400/70 text-xs">Hosted by <span className="text-gold-400">{inv.host_name}</span></p>
            </div>

            {/* Dear invitee */}
            <div className="bg-black/20 border border-gold-500/10 rounded-xl p-5 mb-6">
              <p className="text-cream-200 text-base mb-3">
                Dear <strong className="text-gold-300">{inviteeName}</strong>,
              </p>
              {inv.invite_message ? (
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

            {/* If attending → show Unique ID options */}
            {chosenStatus === 'attending' && (
              <div className="mb-6 rounded-xl border border-gold-500/20 bg-black/20 p-5">
                <p className="text-gold-300 font-semibold text-sm mb-3 font-cinzel">
                  🪔 Connect to your Sankalpam profile
                </p>
                <p className="text-cream-400 text-xs mb-4">
                  Optionally link your attendance to your Sankalpam account and indicate which family members will be joining you.
                </p>

                <div className="grid grid-cols-2 gap-3 mb-4">
                  {[
                    { id: 'existing', label: 'I have a Unique ID', icon: '🔗' },
                    { id: 'new',      label: 'Create a profile',   icon: '✨' },
                  ].map(opt => (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => { setUidOption(opt.id as 'new' | 'existing'); setUidError(''); setMembers([]); setSelectedMembers([]) }}
                      className={`rounded-lg border p-3 text-center text-sm transition-all
                        ${uidOption === opt.id
                          ? 'border-gold-500 bg-gold-500/10 text-gold-300'
                          : 'border-gold-500/20 text-cream-400 hover:border-gold-500/50'}`}
                    >
                      <span className="text-xl block mb-1">{opt.icon}</span>
                      {opt.label}
                    </button>
                  ))}
                </div>

                {/* Existing Unique ID flow */}
                {uidOption === 'existing' && (
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={uniqueId}
                        onChange={e => { setUniqueId(e.target.value.toUpperCase()); setUidError(''); setMembers([]) }}
                        placeholder="PS-XXXXXXXX"
                        className="flex-1 bg-black/30 border border-gold-500/30 rounded-lg px-3 py-2 text-cream-200 text-sm font-mono placeholder-cream-700 focus:outline-none focus:border-gold-400"
                      />
                      <button
                        type="button"
                        onClick={handleLookupUid}
                        disabled={uidLoading}
                        className="px-4 py-2 bg-gold-600 hover:bg-gold-500 text-sacred-950 text-sm font-semibold rounded-lg transition-colors disabled:opacity-50"
                      >
                        {uidLoading ? '…' : 'Find'}
                      </button>
                    </div>
                    {uidError && <p className="text-red-400 text-xs">{uidError}</p>}

                    {members.length > 0 && (
                      <div>
                        <p className="text-cream-400 text-xs mb-2">Select who will be attending:</p>
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
                            </label>
                          ))}
                        </div>
                        <p className="text-xs text-cream-500 mt-2">
                          {selectedMembers.length} member(s) selected
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Create new profile option */}
                {uidOption === 'new' && (
                  <div className="rounded-lg bg-black/30 border border-gold-500/20 p-4 text-center">
                    <p className="text-cream-300 text-sm mb-3">
                      Create your free Sankalpam profile to connect with family and track Pooja attendance.
                    </p>
                    <a
                      href="/register"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block bg-gold-500 hover:bg-gold-400 text-sacred-950 font-bold text-sm px-6 py-2.5 rounded-lg transition-colors"
                    >
                      Create Profile →
                    </a>
                    <p className="text-cream-600 text-xs mt-3">
                      After registering, come back here and use your Unique ID to link your attendance.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Submit button */}
            {chosenStatus && (
              <button
                onClick={handleSubmit}
                disabled={submitting}
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
                {uidOption === 'existing' && selectedMembers.length > 0 && (
                  <p className="text-green-400 text-sm mt-2">
                    ✅ {selectedMembers.length} family member(s) linked to your attendance.
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

            {/* Allow changing response */}
            <button
              onClick={() => { setStep('view'); setSubmitted(false) }}
              className="mt-6 text-sm text-gold-400/70 hover:text-gold-400 underline underline-offset-2"
            >
              Change my response
            </button>
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
