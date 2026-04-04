/**
 * KP (Krishnamurti Paddhati) sub-lord from a sidereal longitude (degrees).
 * Mirrors `backend/app/services/kp_core.py` for browser-side use or WASM pipelines.
 *
 * Longitude must already be sidereal (e.g. after Swiss Ephemeris + Krishnamurti ayanamsa).
 * For ephemeris + Placidus cusps, call the backend (`pyswisseph`) or wire `swisseph-wasm` here.
 */

export const VIMSHOTTARI_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17] as const

export const VIMSHOTTARI_PLANETS = [
  'Ketu',
  'Venus',
  'Sun',
  'Moon',
  'Mars',
  'Rahu',
  'Jupiter',
  'Saturn',
  'Mercury',
] as const

export type VimshottariPlanet = (typeof VIMSHOTTARI_PLANETS)[number]

const NAKSHATRA_SPAN = 360 / 27

export const NAKSHATRA_NAMES = [
  'Ashwini',
  'Bharani',
  'Krittika',
  'Rohini',
  'Mrigashira',
  'Ardra',
  'Punarvasu',
  'Pushya',
  'Ashlesha',
  'Magha',
  'Purva Phalguni',
  'Uttara Phalguni',
  'Hasta',
  'Chitra',
  'Swati',
  'Vishakha',
  'Anuradha',
  'Jyeshtha',
  'Mula',
  'Purva Ashadha',
  'Uttara Ashadha',
  'Shravana',
  'Dhanishta',
  'Shatabhisha',
  'Purva Bhadrapada',
  'Uttara Bhadrapada',
  'Revati',
] as const

function norm360(x: number): number {
  let y = x % 360
  if (y < 0) y += 360
  return y
}

export type KpSubLordResult = {
  siderealLongitude: number
  nakshatraIndex: number
  nakshatraName: string
  starLord: VimshottariPlanet
  subLord: VimshottariPlanet
  degreeWithinNakshatra: number
}

export function kpSubLordFromSiderealLongitude(siderealLongitude: number): KpSubLordResult {
  const lon = norm360(siderealLongitude)
  const idx = Math.floor(lon / NAKSHATRA_SPAN) % 27
  const within = lon - idx * NAKSHATRA_SPAN
  const nakName = NAKSHATRA_NAMES[idx]
  const startOrder = idx % 9
  const starLord = VIMSHOTTARI_PLANETS[startOrder]

  let cumulative = 0
  let subLord: VimshottariPlanet = VIMSHOTTARI_PLANETS[(startOrder + 8) % 9]
  for (let k = 0; k < 9; k++) {
    const pOrder = (startOrder + k) % 9
    const planet = VIMSHOTTARI_PLANETS[pOrder]
    const years = VIMSHOTTARI_YEARS[pOrder]
    const width = (years / 120) * NAKSHATRA_SPAN
    if (within < cumulative + width) {
      subLord = planet
      break
    }
    cumulative += width
  }

  return {
    siderealLongitude: lon,
    nakshatraIndex: idx,
    nakshatraName: nakName,
    starLord,
    subLord,
    degreeWithinNakshatra: within,
  }
}

/** Twelve house cusp sidereal longitudes (houses 1–12) → cuspal sub-lord each. */
export function cuspalSubLordsFromCusps(cuspLongitudes: readonly number[]): KpSubLordResult[] {
  return cuspLongitudes.map((c) => kpSubLordFromSiderealLongitude(c))
}
