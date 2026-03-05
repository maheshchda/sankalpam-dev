'use client'

import React, { useCallback, useEffect, useRef, useState } from 'react'
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
  relationship: string
  is_deceased: boolean
}

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

// ── Main component ────────────────────────────────────────────────────────────
export default function PanchangTicker() {
  const [data, setData]                 = useState<PanchangData | null>(null)
  const [paused, setPaused]             = useState(false)
  const [tip, setTip]                   = useState<TooltipState | null>(null)
  const [members, setMembers]           = useState<FamilyMember[]>([])
  const [selectedId, setSelectedId]     = useState<number | null>(null)  // null = self
  const fetchedRef                      = useRef(false)
  const geoRef                          = useRef<{ lat?: number; lon?: number }>({})

  // Fetch living family members once
  useEffect(() => {
    api.get('/api/family/members')
      .then(res => {
        const list: FamilyMember[] = Array.isArray(res.data) ? res.data : []
        setMembers(list.filter(m => !m.is_deceased))
      })
      .catch(() => {})
  }, [])

  const fetchPanchang = useCallback(async (lat?: number, lon?: number, memberId?: number | null) => {
    try {
      const tzOffset = -new Date().getTimezoneOffset() / 60
      const params: Record<string, string> = { timezone_offset: String(tzOffset) }
      const useLat = lat ?? geoRef.current.lat
      const useLon = lon ?? geoRef.current.lon
      if (useLat !== undefined) params.lat = String(useLat)
      if (useLon !== undefined) params.lon = String(useLon)
      // memberId=null means self; omit param
      const mid = memberId !== undefined ? memberId : selectedId
      if (mid != null) params.member_id = String(mid)
      const res = await api.get('/api/panchang/today', { params })
      setData(res.data)
    } catch (err) {
      console.error('[PanchangTicker] fetch failed', err)
    }
  }, [selectedId])

  // Initial fetch with geolocation
  useEffect(() => {
    if (fetchedRef.current) return
    fetchedRef.current = true
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        pos => {
          geoRef.current = { lat: pos.coords.latitude, lon: pos.coords.longitude }
          fetchPanchang(pos.coords.latitude, pos.coords.longitude)
        },
        () => fetchPanchang(),
        { timeout: 4000, maximumAge: 600000 }
      )
    } else {
      fetchPanchang()
    }
    const id = setInterval(() => fetchPanchang(), 30 * 60 * 1000)
    return () => clearInterval(id)
  }, [fetchPanchang])

  // Re-fetch when selected member changes
  useEffect(() => {
    if (!fetchedRef.current) return  // skip before initial fetch
    fetchPanchang(undefined, undefined, selectedId)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId])

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

        {/* Member selector — fixed right */}
        <div className="flex-none flex items-center gap-1.5 px-3 border-l border-slate-700 bg-slate-900/60">
          <span className="text-slate-400 text-xs whitespace-nowrap">👤 For:</span>
          <select
            value={selectedId ?? ''}
            onChange={e => setSelectedId(e.target.value === '' ? null : Number(e.target.value))}
            className="text-xs bg-slate-800 text-slate-200 border border-slate-600 rounded px-1.5 py-0.5 cursor-pointer focus:outline-none focus:border-amber-500 max-w-[140px]"
            title="Select a family member to see their Taara Balam and Chandra Balam"
          >
            <option value="">Myself</option>
            {members.map(m => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.relationship})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Tooltip */}
      {tip && <Tooltip state={tip} />}
    </>
  )
}
