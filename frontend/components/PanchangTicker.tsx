'use client'

import React, { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import api from '@/lib/api'

// ── Types ─────────────────────────────────────────────────────────────────────
type Score = 'green' | 'yellow' | 'red'

interface Segment {
  label: string
  value: string
  score: Score
  detail: string
}

interface Durmuhurta {
  in_durmuhurta: boolean
  in_rahu_kala: boolean
  durmuhurta_windows: string[]
  rahu_kala_window: string | null
  next_durmuhurta: string | null
}

interface ChandraBalam {
  position: number
  score: Score
  label: string
  today_rasi: string
  janma_rasi: string
}

interface PanchangData {
  date: string
  weekday: string
  tithi: string
  tithi_end_time: string
  nakshatra: string
  nakshatra_end_time: string
  yoga: string
  karana: string
  overall: Score
  segments: Segment[]
  durmuhurta: Durmuhurta
  is_janma_day: boolean
  personalized: boolean
  subject_name: string
  subject_is_self: boolean
  janma_nakshatra: string
  janma_rasi: string
  today_rasi: string
  chandra_balam: ChandraBalam | null
}

interface FamilyMember {
  id: number
  name: string
  relation: string
  is_deceased: boolean
}

// Only these relations are eligible for personalised Panchang (Taara Balam, Chandra Balam)
const PANCHANG_ALLOWED_RELATIONS = new Set([
  'Wife', 'Husband',           // Spouse
  'Son', 'Daughter',           // Children
  'Father', 'Mother',          // Parents
  'Brother', 'Sister',         // Siblings (unmarried; married siblings excluded by convention)
])

// ── Color maps ────────────────────────────────────────────────────────────────
const TEXT: Record<Score, string> = {
  green:  'text-green-400',
  yellow: 'text-yellow-300',
  red:    'text-red-400',
}
const GLOW: Record<Score, string> = {
  green:  'drop-shadow-[0_0_6px_rgba(74,222,128,0.8)]',
  yellow: 'drop-shadow-[0_0_6px_rgba(253,224,71,0.8)]',
  red:    'drop-shadow-[0_0_6px_rgba(248,113,113,0.8)]',
}
const DOT: Record<Score, string> = {
  green:  '🟢',
  yellow: '🟡',
  red:    '🔴',
}
const BORDER: Record<Score, string> = {
  green:  'border-green-800',
  yellow: 'border-yellow-800',
  red:    'border-red-900',
}
const BG: Record<Score, string> = {
  green:  'bg-green-950',
  yellow: 'bg-yellow-950',
  red:    'bg-red-950',
}
const SCORE_LABEL: Record<Score, string> = {
  green:  'Auspicious',
  yellow: 'Moderate',
  red:    'Inauspicious',
}

// ── Tooltip ───────────────────────────────────────────────────────────────────
interface TooltipState {
  lines: string[]
  x: number
  y: number
}

function Tooltip({ state }: { state: TooltipState }) {
  return (
    <div
      className="fixed z-50 bg-slate-900 border border-slate-600 text-slate-200 text-xs rounded-xl px-4 py-3 shadow-2xl pointer-events-none max-w-xs space-y-1"
      style={{ left: state.x + 14, top: state.y + 14 }}
    >
      {state.lines.map((line, i) => (
        <p key={i} className={i === 0 ? 'font-semibold text-slate-100' : 'text-slate-300 leading-snug'}>
          {line}
        </p>
      ))}
    </div>
  )
}

// ── Fallback data when API fails ─────────────────────────────────────────────
function buildFallbackData(): PanchangData {
  const now = new Date()
  const weekday = now.toLocaleDateString('en-US', { weekday: 'long' })
  const date = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
  return {
    date,
    weekday,
    tithi: '—',
    tithi_end_time: '',
    nakshatra: '—',
    nakshatra_end_time: '',
    yoga: '—',
    karana: '—',
    overall: 'yellow',
    segments: [
      { label: 'Vara', value: weekday, score: 'yellow', detail: '' },
      { label: 'Tithi', value: '—', score: 'yellow', detail: 'Panchang unavailable' },
      { label: 'Nakshatra', value: '—', score: 'yellow', detail: '' },
    ],
    durmuhurta: {
      in_durmuhurta: false,
      in_rahu_kala: false,
      durmuhurta_windows: [],
      rahu_kala_window: null,
      next_durmuhurta: null,
    },
    is_janma_day: false,
    personalized: false,
    subject_name: '',
    subject_is_self: true,
    janma_nakshatra: '',
    janma_rasi: '',
    today_rasi: '',
    chandra_balam: null,
  }
}

const LOCATION_MODE_KEY = 'panchang_location_mode'
function readLocationMode(): 'current' | 'resident' {
  if (typeof window === 'undefined') return 'resident'
  try {
    const stored = localStorage.getItem(LOCATION_MODE_KEY)
    return stored === 'resident' ? 'resident' : 'current'
  } catch {
    return 'resident'
  }
}

/** Check if geolocation is allowed. False when explicitly denied; true when granted or prompt. */
async function checkGeolocationAllowed(): Promise<boolean> {
  if (typeof navigator === 'undefined' || !('geolocation' in navigator)) return false
  try {
    if ('permissions' in navigator && typeof navigator.permissions?.query === 'function') {
      const result = await navigator.permissions.query({ name: 'geolocation' as PermissionName })
      return result.state !== 'denied'
    }
    return true // Permissions API not available; allow trying (will prompt on use)
  } catch {
    return true
  }
}

// ── Main component ────────────────────────────────────────────────────────────
interface PanchangTickerProps {
  visible?: boolean
  locationToggleSlotRef?: React.RefObject<HTMLDivElement | null>
  locationSlotReady?: boolean
}

export default function PanchangTicker({ visible = true, locationToggleSlotRef, locationSlotReady = false }: PanchangTickerProps) {
  const [data, setData]                 = useState<PanchangData | null>(null)
  const [loading, setLoading]           = useState(true)
  const [paused, setPaused]             = useState(false)
  const [tip, setTip]                   = useState<TooltipState | null>(null)
  const [members, setMembers]           = useState<FamilyMember[]>([])
  const [selectedId, setSelectedId]     = useState<number | null>(null)  // null = self
  const [locationMode, setLocationMode] = useState<'current' | 'resident'>(readLocationMode)
  const [canUseCurrentLocation, setCanUseCurrentLocation] = useState<boolean | null>(null)
  const fetchedRef                      = useRef(false)
  const geoRef                          = useRef<{ lat?: number; lon?: number }>({})

  // Check geolocation permission on mount — if denied, do not enable Current Location
  useEffect(() => {
    let cancelled = false
    checkGeolocationAllowed().then(allowed => {
      if (cancelled) return
      setCanUseCurrentLocation(allowed)
      if (!allowed) {
        setLocationMode('resident')
        try {
          localStorage.setItem(LOCATION_MODE_KEY, 'resident')
        } catch { /* ignore */ }
      }
    })
    return () => { cancelled = true }
  }, [])

  // Fetch family members once — only those eligible for personalised Panchang
  useEffect(() => {
    api.get('/api/family/members')
      .then(res => {
        const list: FamilyMember[] = Array.isArray(res.data) ? res.data : []
        setMembers(
          list.filter(
            m => !m.is_deceased && PANCHANG_ALLOWED_RELATIONS.has(m.relation)
          )
        )
      })
      .catch(() => {})
  }, [])

  const fetchPanchang = useCallback(async (lat?: number, lon?: number, memberId?: number | null, forceLocationMode?: 'current' | 'resident') => {
    try {
      const tzOffset = -new Date().getTimezoneOffset() / 60
      const params: Record<string, string> = { timezone_offset: String(tzOffset) }
      let mode = forceLocationMode ?? locationMode
      if (mode === 'current' && canUseCurrentLocation === false) mode = 'resident'
      if (mode === 'current') {
        const useLat = lat ?? geoRef.current.lat
        const useLon = lon ?? geoRef.current.lon
        if (useLat !== undefined) params.lat = String(useLat)
        if (useLon !== undefined) params.lon = String(useLon)
      }
      // memberId=null means self; omit param
      const mid = memberId !== undefined ? memberId : selectedId
      if (mid != null) params.member_id = String(mid)
      const res = await api.get('/api/panchang/today', { params })
      setData(res.data)
    } catch (err) {
      console.error('[PanchangTicker] fetch failed', err)
      setData(buildFallbackData())
    } finally {
      setLoading(false)
    }
  }, [selectedId, locationMode, canUseCurrentLocation])

  // Initial fetch — use geolocation only when Current Location is selected and allowed
  useEffect(() => {
    if (fetchedRef.current) return
    fetchedRef.current = true
    const useCurrent = locationMode === 'current' && canUseCurrentLocation !== false
    if (useCurrent && 'geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        pos => {
          geoRef.current = { lat: pos.coords.latitude, lon: pos.coords.longitude }
          fetchPanchang(pos.coords.latitude, pos.coords.longitude)
        },
        err => {
          if (err?.code === 1) {
            setCanUseCurrentLocation(false)
            setLocationMode('resident')
            try { localStorage.setItem(LOCATION_MODE_KEY, 'resident') } catch { /* ignore */ }
          }
          fetchPanchang()
        },
        { timeout: 4000, maximumAge: 600000 }
      )
    } else {
      fetchPanchang()
    }
    const id = setInterval(() => fetchPanchang(), 30 * 60 * 1000)
    return () => clearInterval(id)
  }, [fetchPanchang, locationMode, canUseCurrentLocation])

  // Re-fetch when selected member or location mode changes
  useEffect(() => {
    if (!fetchedRef.current) return  // skip before initial fetch
    fetchPanchang(undefined, undefined, selectedId)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, locationMode])

  const handleLocationModeChange = (mode: 'current' | 'resident') => {
    if (mode === 'current' && canUseCurrentLocation === false) return
    setLocationMode(mode)
    try {
      localStorage.setItem(LOCATION_MODE_KEY, mode)
    } catch { /* ignore */ }
    if (mode === 'current' && 'geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        pos => {
          geoRef.current = { lat: pos.coords.latitude, lon: pos.coords.longitude }
          fetchPanchang(pos.coords.latitude, pos.coords.longitude, undefined, mode)
        },
        err => {
          if (err?.code === 1) {
            setCanUseCurrentLocation(false)
            setLocationMode('resident')
            try { localStorage.setItem(LOCATION_MODE_KEY, 'resident') } catch { /* ignore */ }
          }
          fetchPanchang(undefined, undefined, undefined, 'resident')
        },
        { timeout: 4000, maximumAge: 600000 }
      )
    } else {
      fetchPanchang(undefined, undefined, undefined, mode)
    }
  }

  // Show loading ticker while fetching (keeps bar visible and scrolling)
  if (loading && !data) {
    const loadingNodes = [
      <span key="l0" className="text-slate-400 mr-4">🕉️ Loading today&apos;s Panchang...</span>,
      <span key="l1" className="text-slate-600 mr-4">•</span>,
      <span key="l2" className="text-slate-500 mr-4">{new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'short' })}</span>,
    ]
    const loadingAll = [...loadingNodes, ...loadingNodes]
    return (
      <>
        <style>{`
          @keyframes ticker-scroll {
            0%   { transform: translateX(0); }
            100% { transform: translateX(-50%); }
          }
          .ticker-track {
            display: inline-flex;
            white-space: nowrap;
            animation: ticker-scroll 60s linear infinite;
          }
          .ticker-track.paused { animation-play-state: paused; }
        `}</style>
        <div className="relative w-full flex items-stretch border-b border-yellow-800 bg-yellow-950 text-sm z-40 select-none">
          <div className="flex-none flex items-center px-2 border-r border-slate-700">
            <span className="text-lg leading-none">🟡</span>
          </div>
          <div className="flex-1 overflow-hidden py-1.5">
            <div className="ticker-track">{loadingAll}</div>
          </div>
          <div className="flex-none flex items-center px-3 border-l border-slate-700 bg-slate-900/60">
            <span className="text-slate-400 text-xs">Loading...</span>
          </div>
        </div>
      </>
    )
  }

  if (!data) return null

  const overall = data.overall

  // Build hover text lines for each segment
  const hoverLines = (seg: Segment): string[] => {
    const lines: string[] = [
      `${seg.label}: ${seg.value}  ${DOT[seg.score]}  ${SCORE_LABEL[seg.score]}`,
    ]

    if (seg.detail) {
      seg.detail.split(' · ').forEach(part => part.trim() && lines.push(part.trim()))
    }

    if (seg.label === 'Tithi') {
      if (data.tithi_end_time) lines.push(`⏱ Tithi ends at: ${data.tithi_end_time}`)
      if (data.janma_rasi)     lines.push(`Janma Rasi: ${data.janma_rasi}`)
      const dm = data.durmuhurta
      if (dm) {
        if (dm.in_durmuhurta)        lines.push('⚠️ Durmuhurta is ACTIVE now — avoid new starts')
        else if (dm.in_rahu_kala)    lines.push('⚠️ Rahu Kala is ACTIVE now — avoid new starts')
        else {
          if (dm.durmuhurta_windows.length) lines.push(`Durmuhurta today: ${dm.durmuhurta_windows.join(', ')}`)
          if (dm.rahu_kala_window)          lines.push(`Rahu Kala: ${dm.rahu_kala_window}`)
          if (dm.next_durmuhurta)           lines.push(`Next Durmuhurta: ${dm.next_durmuhurta}`)
        }
      }
    }

    if (seg.label === 'Nakshatra') {
      if (data.nakshatra_end_time) lines.push(`⏱ Nakshatra ends at: ${data.nakshatra_end_time}`)
      if (data.janma_nakshatra) {
        if (data.is_janma_day) {
          lines.push(`⭐ Janma Nakshatra day (${data.janma_nakshatra})`)
          lines.push('Good for spiritual practice; proceed carefully for worldly matters.')
        } else {
          lines.push(`Janma Nakshatra: ${data.janma_nakshatra}`)
        }
      }
    }

    if (seg.label === 'Vara') {
      const dm = data.durmuhurta
      if (dm) {
        if (dm.in_durmuhurta)    lines.push('⚠️ Durmuhurta is ACTIVE right now')
        else if (dm.in_rahu_kala) lines.push('⚠️ Rahu Kala is ACTIVE right now')
        if (dm.rahu_kala_window)           lines.push(`Rahu Kala: ${dm.rahu_kala_window}`)
        if (dm.durmuhurta_windows.length)  lines.push(`Durmuhurta: ${dm.durmuhurta_windows.join(', ')}`)
      }
    }

    if (seg.label === 'Taara Balam' && data.janma_nakshatra) {
      lines.push(`Counted from Janma Nakshatra: ${data.janma_nakshatra}`)
    }

    if (seg.label === 'Chandra Balam' && data.chandra_balam) {
      const cb = data.chandra_balam
      lines.push(`Moon is in ${cb.today_rasi} today`)
      lines.push(`Janma Rasi: ${cb.janma_rasi}  →  ${cb.position}th position`)
    }

    return lines
  }

  // Build ticker nodes
  const nodes: React.ReactNode[] = [
    <span key="date" className="text-slate-300 font-semibold mr-4">🕉️ &nbsp;{data.date}</span>,
    <span key="sep0" className="text-slate-600 mr-4">•</span>,
  ]

  data.segments.forEach((seg, i) => {
    const lines = hoverLines(seg)
    nodes.push(
      <span
        key={`seg-${i}`}
        className="inline-flex items-center gap-1.5 mr-5 cursor-help"
        onMouseEnter={e => setTip({ lines, x: e.clientX, y: e.clientY })}
        onMouseMove={e  => setTip(t => t ? { ...t, x: e.clientX, y: e.clientY } : null)}
        onMouseLeave={() => setTip(null)}
      >
        <span className="text-slate-400 text-xs uppercase tracking-wide">{seg.label}</span>
        <span className={`font-semibold ${TEXT[seg.score as Score]} ${GLOW[seg.score as Score]}`}>
          {seg.value}
        </span>
        <span className="text-base leading-none">{DOT[seg.score as Score]}</span>
      </span>
    )
    if (i < data.segments.length - 1) {
      nodes.push(<span key={`sep-${i}`} className="text-slate-600 mr-4">|</span>)
    }
  })

  if (data.personalized) {
    nodes.push(
      <span key="personal" className="ml-4 text-xs text-slate-500 italic">
        personalised · {data.janma_nakshatra || data.janma_rasi}
      </span>
    )
  }

  const allNodes = [
    ...nodes.map((n, i) =>
      React.isValidElement(n) ? React.cloneElement(n as React.ReactElement, { key: `a-${(n as React.ReactElement).key ?? i}` }) : n
    ),
    ...nodes.map((n, i) =>
      React.isValidElement(n) ? React.cloneElement(n as React.ReactElement, { key: `b-${(n as React.ReactElement).key ?? i}` }) : n
    ),
  ]

  const locationToggle = (
    <div className="flex items-center gap-0.5">
      <button
        type="button"
        onClick={() => handleLocationModeChange('current')}
        disabled={canUseCurrentLocation === false}
        className={`text-xs px-1.5 sm:px-2 py-1 rounded transition-colors touch-manipulation ${
          canUseCurrentLocation === false
            ? 'text-slate-600 cursor-not-allowed border border-transparent'
            : locationMode === 'current'
              ? 'bg-amber-600/40 text-amber-200 border border-amber-500/50 font-medium'
              : 'text-cream-300/80 hover:text-cream-200 border border-transparent'
        }`}
        title={canUseCurrentLocation === false
          ? 'Location access denied — using registered address'
          : 'Panchang for your current location (GPS)'}
      >
        📍 Current
      </button>
      <button
        type="button"
        onClick={() => handleLocationModeChange('resident')}
        className={`text-xs px-1.5 sm:px-2 py-1 rounded transition-colors touch-manipulation ${
          locationMode === 'resident'
            ? 'bg-amber-600/40 text-amber-200 border border-amber-500/50 font-medium'
            : 'text-cream-300/80 hover:text-cream-200 border border-transparent'
        }`}
        title="Panchang for your resident location (profile address)"
      >
        🏠 Resident
      </button>
    </div>
  )

  return (
    <>
      {/* Location toggle — rendered into shell bar via portal */}
      {locationSlotReady && locationToggleSlotRef?.current &&
        createPortal(locationToggle, locationToggleSlotRef.current)}

      {visible && (
      <>
      <style>{`
        @keyframes ticker-scroll {
          0%   { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .ticker-track {
          display: inline-flex;
          white-space: nowrap;
          animation: ticker-scroll 60s linear infinite;
        }
        .ticker-track.paused { animation-play-state: paused; }
      `}</style>

      {/* Ticker bar */}
      <div
        className={`relative w-full flex items-stretch border-b ${BORDER[overall]} ${BG[overall]} text-sm z-40 select-none`}
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => { setPaused(false); setTip(null) }}
      >
        {/* Overall dot — fixed left */}
        <div
          className="flex-none flex items-center px-2 border-r border-slate-700 cursor-help"
          onMouseEnter={e => {
            const dm = data.durmuhurta
            const lines = [
              `Overall: ${SCORE_LABEL[overall]}`,
              overall === 'green'  ? 'Today is generally auspicious for new work and rituals.' :
              overall === 'yellow' ? 'Today is moderate — proceed with awareness.' :
                                     'Today has inauspicious elements — avoid new starts.',
            ]
            if (dm?.in_durmuhurta) lines.push('⚠️ Durmuhurta is currently active')
            if (dm?.in_rahu_kala)  lines.push('⚠️ Rahu Kala is currently active')
            if (!data.subject_is_self)
              lines.push(`Showing panchang for: ${data.subject_name}`)
            setTip({ lines, x: e.clientX, y: e.clientY })
          }}
          onMouseLeave={() => setTip(null)}
        >
          <span className="text-lg leading-none">{DOT[overall]}</span>
        </div>

        {/* Scrolling track — takes remaining space */}
        <div className="flex-1 overflow-hidden py-1.5">
          <div className={`ticker-track${paused ? ' paused' : ''}`}>
            {allNodes}
          </div>
        </div>

        {/* Location toggle — in ticker bar when not using portal (fallback) */}
        {!locationToggleSlotRef && (
          <div className="flex-none flex items-center gap-0.5 px-2 sm:px-3 border-l border-slate-700 bg-slate-900/60">
            {locationToggle}
          </div>
        )}

        {/* Member selector — fixed right, responsive */}
        <div className="flex-none flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 border-l border-slate-700 bg-slate-900/60 min-w-0">
          <span className="text-slate-400 text-xs whitespace-nowrap hidden sm:inline">👤 For:</span>
          <select
            value={selectedId ?? ''}
            onChange={e => setSelectedId(e.target.value === '' ? null : Number(e.target.value))}
            className="text-xs bg-slate-800 text-slate-200 border border-slate-600 rounded px-1.5 py-2 sm:py-1 cursor-pointer focus:outline-none focus:border-amber-500 max-w-[100px] sm:max-w-[140px] min-h-[44px] sm:min-h-[36px] touch-manipulation"
            title="Select a family member to see their Taara Balam and Chandra Balam"
          >
            <option value="">Myself</option>
            {members.map(m => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.relation})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Tooltip */}
      {tip && <Tooltip state={tip} />}
      </>
      )}
    </>
  )
}
