'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuth } from '@/lib/auth'
import PanchangTicker from './PanchangTicker'

const STORAGE_KEY = 'panchang_ticker_visible'
function readVisible(): boolean {
  if (typeof window === 'undefined') return true
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored !== '0'  // default on when not set
  } catch {
    return true
  }
}

export default function PanchangTickerShell() {
  const { user, loading } = useAuth()
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    setVisible(readVisible())
  }, [])

  const toggle = useCallback(() => {
    setVisible(v => {
      const next = !v
      try {
        localStorage.setItem(STORAGE_KEY, next ? '1' : '0')
      } catch { /* ignore */ }
      return next
    })
  }, [])

  const locationToggleRef = useRef<HTMLDivElement | null>(null)
  const [locationSlotReady, setLocationSlotReady] = useState(false)
  const setLocationRef = useCallback((el: HTMLDivElement | null) => {
    locationToggleRef.current = el
    setLocationSlotReady(!!el)
  }, [])

  // Only show when user is logged in (auth done and user exists)
  if (loading || !user) return null

  return (
    <div className="sticky top-0 z-50 pt-[env(safe-area-inset-top)]">
      {/* Toggle bar — minimal */}
      <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3 py-2 sm:py-1.5 px-3 sm:px-4 bg-sacred-800/95 border-b border-gold-600/30 backdrop-blur-sm min-h-[44px]">
        <span className="text-xs sm:text-sm font-medium text-cream-200 text-center truncate max-w-[calc(100vw-5rem)] sm:max-w-none">
          Welcome, <span className="text-gold-400 font-semibold">{user.first_name}</span>
          <span className="hidden sm:inline"> — Panchangam Today</span>
        </span>
        <div ref={setLocationRef} className="flex items-center gap-0.5 shrink-0" />
        <button
          type="button"
          onClick={toggle}
          className={`
            w-11 h-6 rounded-full transition-colors relative
            ${visible ? 'bg-gold-600' : 'bg-slate-600'}
          `}
          aria-label={visible ? 'Hide Today\'s Panchangam' : 'Show Today\'s Panchangam'}
          title={visible ? 'Hide Panchangam' : 'Show Panchangam'}
        >
          <span
            className={`
              absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-all
              ${visible ? 'right-1 left-auto' : 'left-1'}
            `}
          />
        </button>
      </div>

      {/* Ticker — shown when toggled on (default on). PanchangTicker always mounted for location toggle portal. */}
      <PanchangTicker visible={visible} locationToggleSlotRef={locationToggleRef} locationSlotReady={locationSlotReady} />
    </div>
  )
}
