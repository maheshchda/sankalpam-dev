'use client'

import { useEffect } from 'react'

/**
 * Extension Compatibility Component
 * Provides compatibility functions for browser extensions
 * that may try to interact with the page
 */
export default function ExtensionCompatibility() {
  useEffect(() => {
    // Provide setLocation function for location-spoofing Chrome extension
    if (typeof window !== 'undefined') {
      (window as any).setLocation = (location: any) => {
        // Silently handle location setting from extensions
        // This prevents errors when extensions try to set location
        console.debug('Location set by extension:', location)
      }
    }

    return () => {
      // Cleanup on unmount
      if (typeof window !== 'undefined' && (window as any).setLocation) {
        delete (window as any).setLocation
      }
    }
  }, [])

  return null // This component doesn't render anything
}

