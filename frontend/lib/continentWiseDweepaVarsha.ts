/**
 * Continent-wise Dweepa and Varsha — canonical sankalpa geography (Puranic dvīpa / varṣa names).
 *
 * Source strings are **Harvard-Kyoto (HK)** Sanskrit in **locative** case (…dvīpe, …varṣe), then
 * **Sanscript.js** (`transliterate`) fills Devanagari, Telugu, Tamil, Kannada, Malayalam,
 * Bengali, Gujarati, and Gurmukhi (Punjabi). Sanskrit, Hindi, and Marathi share Devanagari.
 *
 * Mapping (continent region → dvīpa + varṣa):
 * - Asia / Indian subcontinent → Jambūdvīpa, Bhāratavarṣa (+ Bhāratakhaṇḍa)
 * - North America → Puṣkaradvīpa, Ramyakavarṣa
 * - South America → Plakṣadvīpa, Kuśavarṣa
 * - Africa → Krauñcadvīpa, Rāmaṇakavarṣa
 * - Europe → Śakadvīpa, Śāvakavarṣa
 * - Australia / Oceania → Śālmalidvīpa, Arjunavarṣa
 *
 * Note: Sanscript’s Tamil output may include superscript combining marks for sandhi; verify
 * with a Tamil editor if you need print-quality copy.
 */

import { transliterate, type SanscriptScheme } from './sanscript'

/** ISO 639-1 codes aligned with `Language` in backend `app/models.py`. */
export const INDIAN_LANGUAGE_CODES = [
  'sa',
  'hi',
  'te',
  'ta',
  'kn',
  'ml',
  'mr',
  'gu',
  'bn',
  'pa',
] as const

export type IndianLanguageCode = (typeof INDIAN_LANGUAGE_CODES)[number]

export type ContinentDweepaKey =
  | 'ASIA_INDIA'
  | 'NORTH_AMERICA'
  | 'SOUTH_AMERICA'
  | 'AFRICA'
  | 'EUROPE'
  | 'AUSTRALIA'

export type ContinentDweepaVarshaPhrases = {
  dweepa: string
  varsha: string
  /** dweepa + varsha with a single space (for templates). */
  combined: string
}

export type ContinentDweepaVarshaRow = {
  continentKey: ContinentDweepaKey
  /** Human-readable region label (English). */
  continentLabelEn: string
  /** Canonical HK — use for audits or re-running Sanscript. */
  source: {
    dweepaLocativeHk: string
    varshaLocativeHk: string
  }
  /** IAST reference (from HK via Sanscript). */
  referenceIast: ContinentDweepaVarshaPhrases
  /** Pre-computed strings per app language code. */
  byLanguage: Record<IndianLanguageCode, ContinentDweepaVarshaPhrases>
}

const ISO_TO_SCHEME: Record<IndianLanguageCode, SanscriptScheme> = {
  sa: 'devanagari',
  hi: 'devanagari',
  mr: 'devanagari',
  te: 'telugu',
  ta: 'tamil',
  kn: 'kannada',
  ml: 'malayalam',
  bn: 'bengali',
  gu: 'gujarati',
  pa: 'gurmukhi',
}

/** Raw continent table: HK locative phrases (split dvīpa / varṣa). */
const CONTINENT_WISE_DWEEPA_VARSHA_SOURCE: ReadonlyArray<{
  continentKey: ContinentDweepaKey
  continentLabelEn: string
  dweepaLocativeHk: string
  varshaLocativeHk: string
}> = [
  {
    continentKey: 'ASIA_INDIA',
    continentLabelEn: 'Asia / Indian subcontinent',
    dweepaLocativeHk: 'jambudvIpe',
    varshaLocativeHk: 'bhAratavarSe bhAratakhaNDe',
  },
  {
    continentKey: 'NORTH_AMERICA',
    continentLabelEn: 'North America',
    dweepaLocativeHk: 'puSkaradvIpe',
    varshaLocativeHk: 'ramyakavarSe',
  },
  {
    continentKey: 'SOUTH_AMERICA',
    continentLabelEn: 'South America',
    dweepaLocativeHk: 'plakSadvIpe',
    varshaLocativeHk: 'kuSavarSe',
  },
  {
    continentKey: 'AFRICA',
    continentLabelEn: 'Africa',
    // HK: J = ञ (for Krauñca). Plain "nc" would not produce ञ्च.
    dweepaLocativeHk: 'krauJcadvIpe',
    varshaLocativeHk: 'rAmaNakavarSe',
  },
  {
    continentKey: 'EUROPE',
    continentLabelEn: 'Europe',
    dweepaLocativeHk: 'zakadvIpe',
    varshaLocativeHk: 'zAvakavarSe',
  },
  {
    continentKey: 'AUSTRALIA',
    continentLabelEn: 'Australia / Oceania',
    dweepaLocativeHk: 'zAlmalidvIpe',
    varshaLocativeHk: 'arjunavarSe',
  },
]

function phrasesFromHk(
  dweepaHk: string,
  varshaHk: string,
  toScheme: SanscriptScheme
): ContinentDweepaVarshaPhrases {
  const dweepa = transliterate(dweepaHk, 'hk', toScheme).trim()
  const varsha = transliterate(varshaHk, 'hk', toScheme).trim()
  const combined = [dweepa, varsha].filter(Boolean).join(' ')
  return { dweepa, varsha, combined }
}

function phrasesFromHkIast(dweepaHk: string, varshaHk: string): ContinentDweepaVarshaPhrases {
  return phrasesFromHk(dweepaHk, varshaHk, 'iast')
}

function buildRow(entry: (typeof CONTINENT_WISE_DWEEPA_VARSHA_SOURCE)[number]): ContinentDweepaVarshaRow {
  const { continentKey, continentLabelEn, dweepaLocativeHk, varshaLocativeHk } = entry
  const byLanguage = {} as Record<IndianLanguageCode, ContinentDweepaVarshaPhrases>
  for (const code of INDIAN_LANGUAGE_CODES) {
    byLanguage[code] = phrasesFromHk(dweepaLocativeHk, varshaLocativeHk, ISO_TO_SCHEME[code])
  }
  return {
    continentKey,
    continentLabelEn,
    source: { dweepaLocativeHk, varshaLocativeHk: varshaLocativeHk },
    referenceIast: phrasesFromHkIast(dweepaLocativeHk, varshaLocativeHk),
    byLanguage,
  }
}

/**
 * Full **Continent-wise Dweepa and Varsha** table: each row has HK source, IAST reference,
 * and per-language phrases generated with Sanscript.
 */
export const CONTINENT_WISE_DWEEPA_VARSHA: ReadonlyArray<ContinentDweepaVarshaRow> =
  CONTINENT_WISE_DWEEPA_VARSHA_SOURCE.map(buildRow)

const ROW_BY_KEY: Record<ContinentDweepaKey, ContinentDweepaVarshaRow> = Object.fromEntries(
  CONTINENT_WISE_DWEEPA_VARSHA.map((r) => [r.continentKey, r])
) as Record<ContinentDweepaKey, ContinentDweepaVarshaRow>

export function getContinentDweepaVarshaRow(key: ContinentDweepaKey): ContinentDweepaVarshaRow | undefined {
  return ROW_BY_KEY[key]
}

/** Dvīpa + varṣa strings for one continent and UI / API language code. */
export function getDweepaVarshaForLanguage(
  key: ContinentDweepaKey,
  lang: IndianLanguageCode
): ContinentDweepaVarshaPhrases | undefined {
  return ROW_BY_KEY[key]?.byLanguage[lang]
}

/**
 * Recompute phrases from HK with Sanscript (e.g. after fixing a source string).
 * Prefer using `CONTINENT_WISE_DWEEPA_VARSHA` for static bundles.
 */
export function computeDweepaVarshaFromHk(
  dweepaLocativeHk: string,
  varshaLocativeHk: string,
  lang: IndianLanguageCode
): ContinentDweepaVarshaPhrases {
  return phrasesFromHk(dweepaLocativeHk, varshaLocativeHk, ISO_TO_SCHEME[lang])
}

/** Plain matrix: continent × language → combined phrase (good for CSV / QA exports). */
export function continentWiseDweepaVarshaCombinedTable(): Record<
  ContinentDweepaKey,
  Record<IndianLanguageCode, string>
> {
  const out = {} as Record<ContinentDweepaKey, Record<IndianLanguageCode, string>>
  for (const row of CONTINENT_WISE_DWEEPA_VARSHA) {
    const langMap = {} as Record<IndianLanguageCode, string>
    for (const code of INDIAN_LANGUAGE_CODES) {
      langMap[code] = row.byLanguage[code].combined
    }
    out[row.continentKey] = langMap
  }
  return out
}
