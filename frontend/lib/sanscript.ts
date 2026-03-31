import Sanscript from 'sanscript'

export type SanscriptScheme =
  | 'iast'
  | 'itrans'
  | 'hk'
  | 'slp1'
  | 'devanagari'
  | 'telugu'
  | 'tamil'
  | 'kannada'
  | 'malayalam'
  | 'bengali'
  | 'gurmukhi'
  | 'gujarati'
  | 'oriya'

function safeString(v: unknown): string {
  return typeof v === 'string' ? v : v == null ? '' : String(v)
}

/**
 * Thin wrapper around Sanscript.js transliterate().
 *
 * Example:
 * - transliterate('gaNesha', 'hk', 'telugu') -> Telugu script
 * - transliterate('śrī gaṇeśāya namaḥ', 'iast', 'devanagari') -> Devanagari
 */
export function transliterate(input: unknown, from: SanscriptScheme, to: SanscriptScheme): string {
  const text = safeString(input)
  if (!text.trim()) return ''
  // sanscript package exports transliterate() as function property
  return (Sanscript as any).t(text, from, to)
}

