'use client'

import { useCallback, useEffect, useState } from 'react'
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

  // Only show when user is logged in (auth done and user exists)
  if (loading || !user) return null

  return (
    <div className="sticky top-0 z-50">
      {/* Toggle bar — minimal */}
      <div className="flex items-center justify-center gap-3 py-1.5 px-4 bg-sacred-800/95 border-b border-gold-600/30 backdrop-blur-sm">
        <span className="text-sm font-medium text-cream-200">Your Panchangam Today</span>
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

      {/* Ticker — shown when toggled on (default on) */}
      {visible && <PanchangTicker />}
    </div>
  )
}
