'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'react-toastify'
import Link from 'next/link'

interface Template {
  id: number
  name: string
  description: string
  language: string
  variables: string
}

export default function SankalpamPage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [location, setLocation] = useState({
    city: '',
    state: '',
    country: '',
    latitude: '',
    longitude: '',
  })
  const [generatedSankalpam, setGeneratedSankalpam] = useState<{
    text: string
    audioUrl: string
  } | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentLine, setCurrentLine] = useState(0)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const fetchTemplates = async () => {
    setLoading(true)
    try {
      const response = await api.get('/api/templates/templates')
      
      // Ensure response.data is an array
      const templatesData = Array.isArray(response.data) ? response.data : []
      
      // Remove duplicates based on template ID
      const uniqueTemplates = templatesData.filter((template: Template, index: number, self: Template[]) => 
        index === self.findIndex((t: Template) => t.id === template.id)
      )
      
      setTemplates(uniqueTemplates)
      
      if (uniqueTemplates.length === 0) {
        toast.warning('No templates available. Please contact admin to upload templates.')
      }
    } catch (error: any) {
      console.error('Error fetching templates:', error)
      toast.error(`Failed to load templates: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }
    
    // Fetch templates only once when user is available
    fetchTemplates()
    
    // Don't pre-fill location - let user enter or detect it
    setLocation({
      city: '',
      state: '',
      country: '',
      latitude: '',
      longitude: '',
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  const reverseGeocode = async (lat: string, lon: string) => {
    try {
      const response = await api.get('/api/templates/reverse-geocode', {
        params: { latitude: lat, longitude: lon }
      })
      
      if (response.data.city || response.data.state || response.data.country) {
        setLocation(prev => ({
          ...prev,
          city: response.data.city || prev.city,
          state: response.data.state || prev.state,
          country: response.data.country || prev.country,
          latitude: lat,
          longitude: lon,
        }))
        toast.success('Location detected from coordinates!')
      }
    } catch (error) {
      console.error('Error reverse geocoding:', error)
      toast.error('Could not detect location from coordinates. Please enter manually.')
    }
  }

  const getCurrentLocation = async () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported by your browser.')
      return
    }

    try {
      setGenerating(true)
      
      // Request location with timeout
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const lat = position.coords.latitude.toString()
            const lon = position.coords.longitude.toString()
            
            // First clear location and set coordinates
            setLocation({
              city: '',
              state: '',
              country: '',
              latitude: lat,
              longitude: lon,
            })
            
            // Then reverse geocode to get city/state/country
            try {
              const response = await api.get('/api/templates/reverse-geocode', {
                params: { latitude: lat, longitude: lon }
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
                toast.warning('Coordinates obtained, but location details not available. Please enter manually.')
              }
            } catch (error) {
              console.error('Error reverse geocoding:', error)
              toast.error('Could not detect location from coordinates. Please enter manually.')
            }
          } catch (error) {
            console.error('Error processing location:', error)
            toast.error('Error processing location data. Please enter manually.')
          } finally {
            setGenerating(false)
          }
        },
        (error) => {
          console.error('Error getting location:', error)
          let errorMessage = 'Could not get your location. '
          
          switch (error.code) {
            case error.PERMISSION_DENIED:
              errorMessage += 'Please allow location access in your browser settings.'
              break
            case error.POSITION_UNAVAILABLE:
              errorMessage += 'Location information is unavailable.'
              break
            case error.TIMEOUT:
              errorMessage += 'Location request timed out.'
              break
            default:
              errorMessage += 'Please enter location manually.'
          }
          
          toast.error(errorMessage)
          setGenerating(false)
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      )
    } catch (error) {
      console.error('Error in getCurrentLocation:', error)
      toast.error('An error occurred while getting your location. Please enter manually.')
      setGenerating(false)
    }
  }

  // Auto-reverse geocode when coordinates are manually entered (but not when they're cleared)
  useEffect(() => {
    // Only reverse geocode if:
    // 1. Both lat and lon are provided
    // 2. City/state are empty (to avoid overwriting user input)
    // 3. We're not in the middle of getting current location
    if (
      location.latitude && 
      location.longitude && 
      !location.city && 
      !location.state &&
      !generating
    ) {
      // Debounce to avoid too many API calls
      const timer = setTimeout(() => {
        reverseGeocode(location.latitude, location.longitude)
      }, 1000)
      return () => clearTimeout(timer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.latitude, location.longitude])

  // Auto-play when Sankalpam is generated
  useEffect(() => {
    if (generatedSankalpam) {
      // Scroll to playback section
      setTimeout(() => {
        const playbackSection = document.getElementById('sankalpam-playback')
        if (playbackSection) {
          playbackSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 100)
      
      // Auto-play audio once it's loaded
      if (audioRef.current) {
        const audio = audioRef.current
        
        // Wait for audio to be loaded
        const handleCanPlay = () => {
          audio.play().then(() => {
            setIsPlaying(true)
            startTextAnimation()
          }).catch((error) => {
            console.error('Error auto-playing audio:', error)
            toast.info('Click play button to start Sankalpam playback')
          })
          audio.removeEventListener('canplay', handleCanPlay)
        }
        
        audio.addEventListener('canplay', handleCanPlay)
        
        // If already loaded, play immediately
        if (audio.readyState >= 2) {
          handleCanPlay()
        }
        
        return () => {
          audio.removeEventListener('canplay', handleCanPlay)
        }
      }
    }
  }, [generatedSankalpam])

  const handleGenerate = async () => {
    console.log('=== GENERATE BUTTON CLICKED ===')
    console.log('Selected template:', selectedTemplate)
    console.log('Location:', location)
    
    if (!selectedTemplate) {
      console.error('No template selected')
      toast.error('Please select a template')
      return
    }

    // Trim whitespace and validate
    const city = location.city?.trim()
    const state = location.state?.trim()
    const country = location.country?.trim()
    
    console.log('Trimmed values:', { city, state, country })
    
    if (!city || !state || !country) {
      console.error('Missing location fields:', { city: !!city, state: !!state, country: !!country })
      toast.error('Please provide complete location information (City, State, and Country)')
      return
    }

    console.log('All validations passed. Calling API...')
    setGenerating(true)
    try {
      const requestData = {
        template_id: selectedTemplate.id,
        location_city: city,
        location_state: state,
        location_country: country,
        latitude: location.latitude || null,
        longitude: location.longitude || null,
        date: new Date().toISOString(),
      }
      console.log('API request data:', requestData)
      
      const response = await api.post('/api/templates/generate', requestData)
      console.log('API response:', response.data)

      // Set generated Sankalpam data and automatically start playing
      if (response.data.audio_url) {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const audioUrl = `${baseUrl}${response.data.audio_url}`
        setGeneratedSankalpam({
          text: response.data.text,
          audioUrl: audioUrl
        })
        toast.success('Sankalpam generated successfully! Starting playback...')
        
        // Auto-scroll to playback section
        setTimeout(() => {
          const playbackSection = document.getElementById('sankalpam-playback')
          if (playbackSection) {
            playbackSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        }, 100)
      }
    } catch (error: any) {
      console.error('=== ERROR GENERATING SANKKALPAM ===')
      console.error('Error object:', error)
      console.error('Error response:', error.response)
      console.error('Error message:', error.message)
      console.error('Error data:', error.response?.data)
      
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to generate Sankalpam'
      toast.error(errorMessage)
      
      // Show more details in console
      if (error.response) {
        console.error('Response status:', error.response.status)
        console.error('Response data:', error.response.data)
      }
    } finally {
      setGenerating(false)
    }
  }

  const startTextAnimation = () => {
    if (!generatedSankalpam || !audioRef.current) return
    
    const lines = generatedSankalpam.text.split('\n').filter(line => line.trim())
    if (lines.length === 0) return

    const audio = audioRef.current
    
    // Wait for duration to be available
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

        // When audio ends
        audio.onended = () => {
          clearInterval(interval)
          setIsPlaying(false)
          setCurrentLine(0)
        }
      }
    }, 100)
    
    // Cleanup if component unmounts
    return () => {
      clearInterval(checkDuration)
    }
  }

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

  if (loading) {
    return <div className="page-bg flex items-center justify-center">
      <p className="font-cinzel text-sacred-700 text-xl">Loading...</p>
    </div>
  }

  return (
    <div className="page-bg">
      <nav className="sacred-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="font-cinzel text-xl font-bold text-gold-400">Pooja Sankalpam</Link>
            <div className="flex items-center gap-3">
              <Link href="/dashboard" className="sacred-pill text-cream-200 border-gold-600/40 hover:text-gold-400">Back to Dashboard</Link>
              <button onClick={() => { logout(); router.push('/login') }} className="rounded-md border border-gold-600/40 px-3 py-1.5 text-sm text-cream-300 hover:bg-sacred-700 transition-colors">Logout</button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="sacred-card p-6 mb-6">
          <h2 className="font-cinzel text-2xl font-bold text-sacred-800 mb-4">Generate Sankalpam</h2>
          <p className="text-stone-600 mb-6">
            Generate a personalized Sankalpam using your profile information and selected template.
          </p>

          {/* Template Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Template *
            </label>
            {loading ? (
              <p className="text-gray-500 text-sm py-4">Loading templates...</p>
            ) : templates.length === 0 ? (
              <div className="text-gray-500 text-sm py-4 space-y-2">
                <p>No templates available. Please contact admin to upload templates.</p>
                <div className="text-xs bg-gray-100 p-2 rounded">
                  <p><strong>Debug Info:</strong></p>
                  <p>Templates array length: {templates.length}</p>
                  <p>Loading state: {loading ? 'true' : 'false'}</p>
                  <p>User logged in: {user ? 'yes' : 'no'}</p>
                  <p className="text-red-600 mt-2">
                    Check browser console (F12) for API response details
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-xs text-green-600 mb-2">✓ Found {templates.length} template(s)</p>
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                      selectedTemplate?.id === template.id
                        ? 'border-gold-500 bg-gold-500/10 ring-1 ring-gold-500/30'
                        : 'border-cream-300 hover:border-gold-500/50'
                    }`}
                    onClick={() => setSelectedTemplate(template)}
                  >
                    <h3 className="font-bold text-lg">{template.name}</h3>
                    {template.description && (
                      <p className="text-gray-600 text-sm mt-1">{template.description}</p>
                    )}
                    <p className="text-xs text-gray-500 mt-1">Language: {template.language}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Location Information */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Location (where Sankalpam is being performed) *
              </label>
              <button
                type="button"
                onClick={getCurrentLocation}
                disabled={generating}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 disabled:opacity-50"
              >
                📍 Get Current Location
              </button>
            </div>
            <p className="text-xs text-gray-500 mb-3">
              Enter coordinates to automatically detect city/state/country, or enter manually
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Latitude (optional, auto-detects location)</label>
                <input
                  type="text"
                  value={location.latitude}
                  onChange={(e) => setLocation({ ...location, latitude: e.target.value })}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                  placeholder="e.g., 17.0583"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Longitude (optional, auto-detects location)</label>
                <input
                  type="text"
                  value={location.longitude}
                  onChange={(e) => setLocation({ ...location, longitude: e.target.value })}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                  placeholder="e.g., 79.2678"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-600 mb-1">City *</label>
                <input
                  type="text"
                  value={location.city}
                  onChange={(e) => setLocation({ ...location, city: e.target.value })}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                  placeholder="City (auto-filled if coordinates provided)"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">State *</label>
                <input
                  type="text"
                  value={location.state}
                  onChange={(e) => setLocation({ ...location, state: e.target.value })}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                  placeholder="State (auto-filled if coordinates provided)"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Country *</label>
                <input
                  type="text"
                  value={location.country}
                  onChange={(e) => setLocation({ ...location, country: e.target.value })}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                  placeholder="Country (auto-filled if coordinates provided)"
                  required
                />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              💡 Tip: Click "Get Current Location" or enter coordinates to automatically fill city/state/country
            </p>
          </div>

                  {/* User Info Preview */}
                  <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                    <h3 className="font-semibold mb-2">Your Information (from profile)</h3>
                    <div className="text-sm text-gray-600 space-y-1">
                      <p><strong>Name:</strong> {user?.first_name} {user?.last_name}</p>
                      <p><strong>Gotram:</strong> {user?.gotram}</p>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      This information will be automatically used in the Sankalpam.
                    </p>
                  </div>

          {/* Debug Info (only show if button is disabled) */}
          {(!selectedTemplate || !location.city?.trim() || !location.state?.trim() || !location.country?.trim()) && (
            <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="text-sm text-yellow-800 font-semibold mb-2">⚠️ Please complete the following:</p>
              <ul className="text-xs text-yellow-700 space-y-1">
                {!selectedTemplate && <li>• Select a template (Current: {selectedTemplate ? selectedTemplate.name : 'None'})</li>}
                {!location.city?.trim() && <li>• Enter City (Current: "{location.city}" - length: {location.city?.length || 0})</li>}
                {!location.state?.trim() && <li>• Enter State (Current: "{location.state}" - length: {location.state?.length || 0})</li>}
                {!location.country?.trim() && <li>• Enter Country (Current: "{location.country}" - length: {location.country?.length || 0})</li>}
              </ul>
              <div className="mt-2 text-xs bg-white p-2 rounded border">
                <p><strong>Debug:</strong></p>
                <p>Template selected: {selectedTemplate ? 'Yes (' + selectedTemplate.name + ')' : 'No'}</p>
                <p>City: "{location.city}" (trimmed: "{location.city?.trim()}")</p>
                <p>State: "{location.state}" (trimmed: "{location.state?.trim()}")</p>
                <p>Country: "{location.country}" (trimmed: "{location.country?.trim()}")</p>
                <p>Button disabled: {(!selectedTemplate || !location.city?.trim() || !location.state?.trim() || !location.country?.trim()) ? 'Yes' : 'No'}</p>
              </div>
            </div>
          )}

          {/* Generate Button */}
          <button
            onClick={() => handleGenerate()}
            disabled={!selectedTemplate || generating || !location.city?.trim() || !location.state?.trim() || !location.country?.trim()}
            className="gold-btn w-full py-3"
          >
            {generating ? 'Generating Sankalpam...' : 'Generate Sankalpam'}
          </button>
          
          {/* Button State Debug */}
          <div className="mt-2 text-xs text-gray-500">
            <p>Button state: {generating ? 'Generating...' : (!selectedTemplate || !location.city?.trim() || !location.state?.trim() || !location.country?.trim() ? 'Disabled' : 'Enabled - Click to generate')}</p>
          </div>
        </div>

        {/* Sankalpam Playback Section */}
        {generatedSankalpam && (
          <div id="sankalpam-playback" className="sacred-card p-6 mt-6">
            <div className="mb-6 text-center">
              <h2 className="font-cinzel text-3xl font-bold text-sacred-800 mb-2">Sankalpam</h2>
              <p className="text-stone-500">Your personalized Sankalpam with professional priest chanting</p>
            </div>

            <div className="mb-6 text-center">
              <audio ref={audioRef} src={generatedSankalpam.audioUrl} preload="auto" id="sankalpam-audio" onEnded={() => { setIsPlaying(false); setCurrentLine(0) }} />
              <div className="flex justify-center gap-4">
                <button onClick={handlePlay} disabled={isPlaying} className="gold-btn px-6 py-3 text-lg flex items-center gap-2">
                  ▶️ {isPlaying ? 'Playing...' : 'Play Sankalpam'}
                </button>
                {isPlaying && (
                  <button onClick={handlePause} className="sacred-btn px-6 py-3 text-lg flex items-center gap-2">
                    ⏸️ Pause
                  </button>
                )}
              </div>
            </div>

            <div className="bg-cream-200 rounded-lg p-6 min-h-[400px] max-h-[600px] overflow-y-auto">
              <AnimatePresence mode="wait">
                {generatedSankalpam.text.split('\n').filter(line => line.trim()).map((line, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: currentLine === index ? 1 : 0.5, y: 0, scale: currentLine === index ? 1.02 : 1 }}
                    transition={{ duration: 0.3 }}
                    className={`mb-3 text-lg ${
                      currentLine === index
                        ? 'text-sacred-800 font-semibold bg-gold-500/20 border border-gold-500/30 p-3 rounded-lg'
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
                onClick={() => { setGeneratedSankalpam(null); setIsPlaying(false); setCurrentLine(0); if (audioRef.current) { audioRef.current.pause(); audioRef.current.currentTime = 0 } }}
                className="px-4 py-2 bg-cream-200 text-stone-700 rounded-md hover:bg-cream-300 border border-cream-300"
              >
                Generate New Sankalpam
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

