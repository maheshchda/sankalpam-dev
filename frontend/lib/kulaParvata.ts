export type KulaParvataKey = 'HIMAVAT' | 'VINDHYA' | 'SAHYADRI' | 'MAHENDRA' | 'MALAYA' | 'MERU'

export type KulaParvataResult = {
  /** Stable key for analytics/conditional rendering */
  key: KulaParvataKey
  /** Human-friendly name (UI) */
  label: string
  /**
   * Sankalp-ready phrase (what you'd actually embed in the Sankalp line).
   * Keep it ASCII/IAST here; backend template layer can translate/transliterate per language if needed.
   */
  sankalpTerm: string
}

type Input = {
  /** Indian state/UT name; best-effort normalization (e.g. "UP", "Uttar Pradesh") */
  state?: string
  /** Latitude in decimal degrees */
  lat?: number | string | null
  /** Longitude in decimal degrees */
  lon?: number | string | null
}

const CATALOG: Record<KulaParvataKey, KulaParvataResult> = {
  HIMAVAT: { key: 'HIMAVAT', label: 'Himavat (Himalayas)', sankalpTerm: 'himavatparshve' },
  VINDHYA: { key: 'VINDHYA', label: 'Vindhya Range', sankalpTerm: 'vindhyachalaparshve' },
  SAHYADRI: { key: 'SAHYADRI', label: 'Sahyadri (Western Ghats)', sankalpTerm: 'sahyadriparshve' },
  MAHENDRA: { key: 'MAHENDRA', label: 'Mahendra Giri', sankalpTerm: 'mahendraparshve' },
  MALAYA: { key: 'MALAYA', label: 'Malaya Parvata', sankalpTerm: 'malayaparshve' },
  MERU: { key: 'MERU', label: 'Meru (General)', sankalpTerm: 'meruparshve' },
}

function toNum(v: unknown): number | null {
  if (v == null) return null
  if (typeof v === 'number' && Number.isFinite(v)) return v
  const s = String(v).trim()
  if (!s) return null
  const n = Number(s)
  return Number.isFinite(n) ? n : null
}

function normState(raw: string): string {
  return raw
    .trim()
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/\./g, '')
    .replace(/\s+/g, ' ')
}

/**
 * Return the Kula Parvata classification for Sankalpam.
 *
 * Heuristic mapping (varies by tradition). Designed to be predictable and safe:
 * - Use explicit state mapping when possible
 * - Else use lat/lon thresholds (similar to your sample logic)
 * - Else return MERU (general)
 */
export function getKulaParvata(input: Input = {}): KulaParvataResult {
  const lat = toNum(input.lat)
  const lon = toNum(input.lon)
  const st = input.state ? normState(input.state) : ''

  // --- State-first coarse mapping (India-centric) ---
  // Keep this conservative; lat/lon will refine when provided.
  const STATE_MAP: Record<string, KulaParvataKey> = {
    // North / Himalaya
    'jammu and kashmir': 'HIMAVAT',
    ladakh: 'HIMAVAT',
    'himachal pradesh': 'HIMAVAT',
    uttarakhand: 'HIMAVAT',

    // Central
    'madhya pradesh': 'VINDHYA',
    rajasthan: 'VINDHYA',
    'uttar pradesh': 'VINDHYA',
    chhattisgarh: 'VINDHYA',

    // West / Sahyadri
    maharashtra: 'SAHYADRI',
    goa: 'SAHYADRI',

    // East
    odisha: 'MAHENDRA',
    orissa: 'MAHENDRA',
    'andhra pradesh': 'MAHENDRA',

    // South
    'tamil nadu': 'MALAYA',
    kerala: 'MALAYA',
  }

  const ABBR_MAP: Record<string, string> = {
    jk: 'jammu and kashmir',
    hp: 'himachal pradesh',
    uk: 'uttarakhand',
    mp: 'madhya pradesh',
    up: 'uttar pradesh',
    rj: 'rajasthan',
    mh: 'maharashtra',
    ga: 'goa',
    or: 'odisha',
    ap: 'andhra pradesh',
    tn: 'tamil nadu',
    kl: 'kerala',
  }

  const stExpanded = st.length <= 3 && ABBR_MAP[st] ? ABBR_MAP[st] : st
  if (stExpanded && STATE_MAP[stExpanded]) {
    // Special case: Karnataka split is better with latitude.
    if (stExpanded === 'karnataka') {
      if (lat != null) return lat >= 14.0 ? CATALOG.SAHYADRI : CATALOG.MALAYA
      return CATALOG.SAHYADRI
    }
    return CATALOG[STATE_MAP[stExpanded]]
  }

  // --- Lat/Lon heuristic (matches the spirit of the user's sample logic) ---
  if (lat != null) {
    if (lat > 28) return CATALOG.HIMAVAT
    if (lat > 21 && lat <= 28) return CATALOG.VINDHYA
    if (lon != null) {
      if (lon < 78 && lat < 21) return CATALOG.SAHYADRI
      if (lon >= 78 && lat < 21) {
        // East-vs-south is ambiguous here; choose Mahendra for the east coast belt, else Malaya.
        // Without state/district, default to Malaya for "south" wording consistency.
        return lon >= 82 ? CATALOG.MAHENDRA : CATALOG.MALAYA
      }
    }
  }

  return CATALOG.MERU
}

