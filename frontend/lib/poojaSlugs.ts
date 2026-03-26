/** URL-safe slug from a pooja display name (matches calendar rows and backend list names). */
export function getPoojaSlug(name: string): string {
  return (name || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

/**
 * Canonical slug for matching calendar row ↔ API pooja name (strict equality).
 * Aligns common spelling variants so one calendar row maps to exactly one list entry.
 */
export function getCanonicalPoojaSlug(nameOrSlug: string): string {
  let s = getPoojaSlug(nameOrSlug)
  s = s.replace(/ganesha/g, 'ganesh')
  s = s.replace(/vinayaka/g, 'ganesh')
  s = s.replace(/laxmi/g, 'lakshmi')
  s = s.replace(/ekadashi/g, 'ekadasi')
  s = s.replace(/-+/g, '-').replace(/^-+|-+$/g, '')
  return s
}

/** True iff this API pooja is the one for the calendar URL slug (no substring matching). */
export function poojaSlugMatchesFilter(poojaDisplayName: string, urlSlug: string): boolean {
  const target = getCanonicalPoojaSlug(urlSlug)
  if (!target) return true
  return getCanonicalPoojaSlug(poojaDisplayName) === target
}

/**
 * Exact localized titles from backend `pooja_calendar` inject rows → English-key slug
 * (same as backend `_pooja_slug_from_english`). Used when API omits `pooja_slug` or
 * `pooja_name` is script-only so `getPoojaSlug` is empty.
 */
const CALENDAR_INJECT_FALLBACK_SLUG: Record<string, string> = {
  // Ganesha Pooja (ganesha_name_by_lang)
  'గణేశ పూజ': 'ganesha-pooja',
  'ગણેશ પૂજા': 'ganesha-pooja',
  'ಗಣೇಶ ಪೂಜೆ': 'ganesha-pooja',
  'கணேஷ பூஜை': 'ganesha-pooja',
  'ഗണേശ പൂജ': 'ganesha-pooja',
  'गणेश पूजा': 'ganesha-pooja',
  'গণেশ পূজা': 'ganesha-pooja',
  'ଗଣେଶ ପୂଜା': 'ganesha-pooja',
  'ਗਣੇਸ਼ ਪੂਜਾ': 'ganesha-pooja',
  'গণেশ পূজা': 'ganesha-pooja',
  // Common inject (name_map)
  'పౌర్ణిమ పూజ / సత్యనారాయణ పూజ': 'purnima-pooja-satyanarayan-pooja',
  'ప్రదోష శివ పూజ': 'pradosha-shiva-pooja',
  'ఏకాదశి శివ పూజ': 'ekadasi-shiva-pooja',
  'पूर्णिमा पूजा / सत्यनारायण पूजा': 'purnima-pooja-satyanarayan-pooja',
  'प्रदोष शिव पूजा': 'pradosha-shiva-pooja',
  'एकादशी शिव पूजा': 'ekadasi-shiva-pooja',
}

/** URL segment for /pooja/... and /pooja-readiness/... (calendar inject, backend slug). */
export const GANESHA_POOJA_URL_SLUG = 'ganesha-pooja'

/** Same slug as calendar "Readiness Info" for పౌర్ణిమ పూజ / సత్యనారాయణ పూజ */
export const PURNIMA_SATYANARAYANA_POOJA_SLUG =
  CALENDAR_INJECT_FALLBACK_SLUG['పౌర్ణిమ పూజ / సత్యనారాయణ పూజ']

export type CalendarRowLike = {
  pooja_slug?: string
  poojaSlug?: string
  pooja_name: string
  local_language: string
}

/** Stable slug for /pooja/<slug> from a calendar row (API field + fallbacks). */
export function resolveCalendarLinkSlug(row: CalendarRowLike): string {
  const fromApi = (row.pooja_slug || row.poojaSlug || '').trim()
  if (fromApi) return fromApi
  for (const field of [row.pooja_name, row.local_language]) {
    const s = (field || '').trim()
    const direct = getPoojaSlug(s)
    if (direct) return direct
    const fb = CALENDAR_INJECT_FALLBACK_SLUG[s]
    if (fb) return fb
  }
  const combined = `${row.local_language || ''} ${row.pooja_name || ''}`
  const m = combined.match(/\(([A-Za-z][A-Za-z0-9\s/\\-]+)\)/)
  if (m) {
    const fromParens = getPoojaSlug(m[1])
    if (fromParens) return fromParens
  }
  return ''
}

/** Stable slug for calendar rows: Open Pooja, Readiness, Items (handles script-only names + Ganesha). */
export function resolveCalendarRowSlug(row: CalendarRowLike): string {
  let slug = resolveCalendarLinkSlug(row)
  if (slug && getCanonicalPoojaSlug(slug) === 'ganesh-pooja') {
    slug = GANESHA_POOJA_URL_SLUG
  }
  return slug
}
