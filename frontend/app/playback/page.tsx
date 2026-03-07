'use client'

import React, { useEffect, useState, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'react-toastify'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'

interface SankalpamData {
  sankalpam_text: string
  nearby_river: string
  session_id: number
  sankalpam_audio_url?: string
}

export default function PlaybackPage() {
  const { user } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('session_id')
  
  const [sankalpam, setSankalpam] = useState<SankalpamData | null>(null)
  const [loading, setLoading] = useState(true)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentLine, setCurrentLine] = useState(0)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }

    if (!sessionId) {
      toast.error('No session ID provided')
      router.push('/pooja')
      return
    }

    generateSankalpam()
  }, [sessionId, user, router])

  const generateSankalpam = async () => {
    try {
      // Get session details first
      const sessionResponse = await api.get(`/api/pooja/session/${sessionId}`)
      const session = sessionResponse.data

      // Generate sankalpam
      const response = await api.post('/api/sankalpam/generate', {
        session_id: parseInt(sessionId || '0'),
        location_city: session.location_city || user?.birth_city,
        location_state: session.location_state || user?.birth_state,
        location_country: session.location_country || user?.birth_country,
      })

      const sankalpamData = response.data
      setSankalpam(sankalpamData)
      
      // If audio URL exists, set it up
      if (sankalpamData.sankalpam_audio_url) {
        setAudioUrl(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${sankalpamData.sankalpam_audio_url}`)
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to generate sankalpam')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handlePlay = () => {
    if (audioUrl && audioRef.current) {
      // Play audio if available
      audioRef.current.play()
      setIsPlaying(true)
      
      // Animation logic - highlight each line as audio plays
      const lines = sankalpam?.sankalpam_text.split('\n').filter(line => line.trim()) || []
      if (audioRef.current.duration) {
        const durationPerLine = audioRef.current.duration / lines.length
        let lineIndex = 0

        const interval = setInterval(() => {
          if (lineIndex < lines.length - 1 && audioRef.current && !audioRef.current.paused) {
            setCurrentLine(lineIndex)
            lineIndex++
          } else {
            clearInterval(interval)
          }
        }, durationPerLine * 1000)
        
        // When audio ends
        audioRef.current.onended = () => {
          clearInterval(interval)
          setIsPlaying(false)
          setCurrentLine(0)
        }
      }
    } else {
      // Fallback: visual animation if no audio
      setIsPlaying(true)
      const lines = sankalpam?.sankalpam_text.split('\n').filter(line => line.trim()) || []
      let lineIndex = 0

      const interval = setInterval(() => {
        if (lineIndex < lines.length - 1) {
          setCurrentLine(lineIndex)
          lineIndex++
        } else {
          clearInterval(interval)
          setIsPlaying(false)
          setCurrentLine(0)
        }
      }, 3000)
    }
  }

  const handlePause = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      setIsPlaying(false)
    }
  }

  if (loading) {
    return (
      <div className="page-bg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500 mx-auto"></div>
          <p className="font-cinzel mt-4 text-sacred-700">Generating Sankalpam...</p>
        </div>
      </div>
    )
  }

  if (!sankalpam) {
    return (
      <div className="page-bg flex items-center justify-center">
        <div className="text-center sacred-card p-8">
          <p className="text-red-600 mb-4">Failed to load sankalpam</p>
          <Link href="/pooja" className="gold-btn">Go Back</Link>
        </div>
      </div>
    )
  }

  const lines = sankalpam.sankalpam_text.split('\n').filter(line => line.trim())

  return (
    <div className="page-bg">
      <nav className="sacred-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="font-cinzel text-xl font-bold text-gold-400">Pooja Sankalpam</Link>
            <Link href="/dashboard" className="sacred-pill text-cream-200 border-gold-600/40 hover:text-gold-400">Dashboard</Link>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="sacred-card p-8">
          <div className="mb-6 text-center">
            <h2 className="font-cinzel text-3xl font-bold text-sacred-800 mb-2">Sankalpam</h2>
            <p className="text-stone-500">Nearby River: {sankalpam.nearby_river}</p>
          </div>

          <div className="mb-6 text-center">
            {audioUrl && <audio ref={audioRef} src={audioUrl} preload="auto" onEnded={() => setIsPlaying(false)} />}
            <div className="flex justify-center gap-4">
              <button onClick={handlePlay} disabled={isPlaying} className="gold-btn px-6 py-3 text-lg flex items-center gap-2">
                {isPlaying ? (
                  <><svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Playing...</>
                ) : (
                  <><svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20"><path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" /></svg>Play Sankalpam</>
                )}
              </button>
              {isPlaying && audioUrl && (
                <button onClick={handlePause} className="sacred-btn px-6 py-3 text-lg flex items-center gap-2">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                  Pause
                </button>
              )}
            </div>
            {!audioUrl && <p className="text-sm text-stone-500 mt-2">Audio generation in progress... Visual playback available</p>}
          </div>

          <div className="bg-cream-200 rounded-lg p-6 min-h-[400px]">
            <AnimatePresence mode="wait">
              {lines.map((line, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: currentLine === index ? 1 : 0.5, y: 0, scale: currentLine === index ? 1.05 : 1 }}
                  transition={{ duration: 0.5 }}
                  className={`mb-4 text-lg ${
                    currentLine === index
                      ? 'text-sacred-800 font-semibold bg-gold-500/20 border border-gold-500/30 p-2 rounded'
                      : 'text-stone-600'
                  }`}
                >
                  {line}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          <div className="mt-6 text-center">
            <button onClick={() => router.push('/pooja')} className="px-4 py-2 bg-cream-200 text-stone-700 rounded-md hover:bg-cream-300 border border-cream-300">
              Select Another Pooja
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
