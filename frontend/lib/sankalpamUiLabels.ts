/**
 * Shared copy + helpers for Generic Sankalpam (/sankalpam) and Pooja Sankalpam flows.
 * Labels use ISO-like language codes (en, te, …) for t().
 */

export const SANKALPAM_LANGUAGES: { code: string; label: string }[] = [
  { code: 'sa', label: 'Sanskrit' },
  { code: 'hi', label: 'Hindi' },
  { code: 'te', label: 'Telugu' },
  { code: 'ta', label: 'Tamil' },
  { code: 'kn', label: 'Kannada' },
  { code: 'ml', label: 'Malayalam' },
  { code: 'en', label: 'English' },
  { code: 'mr', label: 'Marathi' },
  { code: 'gu', label: 'Gujarati' },
  { code: 'bn', label: 'Bengali' },
  { code: 'or', label: 'Oriya' },
  { code: 'pa', label: 'Punjabi' },
]

export function preferredLanguageToCode(preferred: string | undefined): string {
  if (!preferred || !preferred.trim()) return ''
  const s = preferred.trim().toLowerCase()
  if (s.length === 2) return s
  const found = SANKALPAM_LANGUAGES.find(({ label }) => label.toLowerCase() === s)
  return found ? found.code : ''
}

/** Map Sankalpam language dropdown (ISO) → backend template.language enum string */
export const ISO_TO_BACKEND_LANGUAGE: Record<string, string> = {
  sa: 'sanskrit',
  hi: 'hindi',
  te: 'telugu',
  ta: 'tamil',
  kn: 'kannada',
  ml: 'malayalam',
  en: 'english',
  mr: 'marathi',
  gu: 'gujarati',
  bn: 'bengali',
  or: 'oriya',
  pa: 'punjabi',
}

export function backendLanguageFromIso(code: string): string {
  const c = (code || 'en').toLowerCase()
  return ISO_TO_BACKEND_LANGUAGE[c] || 'english'
}

/** Normalize API template.language (enum value, or stray "Language.TELUGU" strings) for comparison */
export function normalizeTemplateLanguage(raw: string | undefined): string {
  if (raw == null || raw === '') return ''
  let s = String(raw).trim().toLowerCase()
  if (s.startsWith('language.')) s = s.slice('language.'.length)
  const tail = s.includes('.') ? (s.split('.').pop() || s) : s
  return tail.toLowerCase()
}

const GENERIC_SANKALPAM_LABELS = {
  appName: { en: 'Sankalpam', te: 'సంకల్పం' },
  backToDashboard: { en: 'Back to Dashboard', te: 'డాష్‌బోర్డ్‌కు తిరిగి' },
  logout: { en: 'Logout', te: 'లాగౌట్' },
  pageTitle: { en: 'Generic Sankalpam', te: 'సాధారణ సంకల్పం' },
  pageIntro: {
    en: 'Generate a personalized Sankalpam from the default template for your chosen language. No separate template pick is needed.',
    te: 'మీరు ఎంచుకున్న భాషకు డిఫాల్ట్ టెంప్లేట్ నుండి వ్యక్తిగత సంకల్పాన్ని రూపొందించండి. ప్రత్యేక టెంప్లేట్ ఎంపిక అవసరం లేదు.',
  },
  location: { en: 'Location', te: 'స్థానం' },
  getCurrentLocation: { en: 'Get current location', te: 'ప్రస్తుత స్థానం పొందండి' },
  useApproxLocation: { en: 'Use approximate location', te: 'అంచనా స్థానం ఉపయోగించండి' },
  locationDesc: {
    en: 'Location where the pooja and Sankalpam are being performed. Use "Get current location" (browser GPS) or "Use approximate location" (from your internet connection). You can also enter city, state, and country manually.',
    te: 'పూజ మరియు సంకల్పం నిర్వహించే స్థానం. "ప్రస్తుత స్థానం పొందండి" (బ్రౌజర్ GPS) లేదా "అంచనా స్థానం ఉపయోగించండి" ఉపయోగించండి. నగరం, రాష్ట్రం మరియు దేశాన్ని మాన్యువల్‌గా నమోదు చేయవచ్చు.',
  },
  latitude: { en: 'Latitude', te: 'అక్షాంశం' },
  longitude: { en: 'Longitude', te: 'రేఖాంశం' },
  latitudeLongitudeDesc: { en: 'Shown after you select a place above.', te: 'పైన స్థానం ఎంచుకున్న తర్వాత చూపిస్తుంది.' },
  selectCountry: { en: 'Select country...', te: 'దేశం ఎంచుకోండి...' },
  selectState: { en: 'Select state...', te: 'రాష్ట్రం ఎంచుకోండి...' },
  selectProvince: { en: 'Select province...', te: 'ప్రావిన్స్ ఎంచుకోండి...' },
  selectRegion: { en: 'Select region...', te: 'ప్రాంతం ఎంచుకోండి...' },
  selectCity: { en: 'Select city...', te: 'నగరం ఎంచుకోండి...' },
  city: { en: 'City *', te: 'నగరం *' },
  state: { en: 'State *', te: 'రాష్ట్రం *' },
  province: { en: 'Province *', te: 'ప్రావిన్స్ *' },
  stateProvince: { en: 'State / Province *', te: 'రాష్ట్రం / ప్రావిన్స్ *' },
  country: { en: 'Country *', te: 'దేశం *' },
  sankalpamLanguage: { en: 'Sankalpam Language', te: 'సంకల్పం భాష' },
  languageDesc: {
    en: 'Choose the language in which the Sankalpam will be generated. This overrides your profile language for this generic Sankalpam.',
    te: 'సంకల్పం ఏ భాషలో రూపొందించబడుతుందో ఎంచుకోండి. ఈ సాధారణ సంకల్పం కోసం మీ ప్రొఫైల్ భాషను ఇది ఓవర్రైడ్ చేస్తుంది.',
  },
  language: { en: 'Language', te: 'భాష' },
  selectLanguage: { en: 'Select language...', te: 'భాష ఎంచుకోండి...' },
  noTemplateForLang: {
    en: 'No Sankalpam template exists for this language yet. Ask an admin to add one, or choose another language.',
    te: 'ఈ భాషకు ఇంకా సంకల్పం టెంప్లేట్ లేదు. అడ్మిన్‌ను జోడించమని కోరండి లేదా మరొక భాష ఎంచుకోండి.',
  },
  generateButton: { en: 'Generate Sankalpam', te: 'సంకల్పం రూపొందించండి' },
  generatingSankalpam: { en: 'Generating Sankalpam...', te: 'సంకల్పం రూపొందిస్తోంది...' },
  playSankalpam: { en: 'Play Sankalpam', te: 'సంకల్పం ప్లే చేయండి' },
  playing: { en: 'Playing...', te: 'ప్లే అవుతోంది...' },
  pause: { en: 'Pause', te: 'విరామం' },
  sankalpaSetupTitle: { en: 'Sankalpa setup', te: 'సంకల్ప తయారీ' },
  sankalpaSetupParticipants: {
    en: 'Who is participating in this Sankalpam with you?',
    te: 'ఈ సంకల్పంలో మీతో పాటు ఎవరెవరు పాల్గొంటున్నారు?',
  },
  profileReadyBadge: { en: 'Your details are ready for Sankalpam', te: 'మీ వివరాలు సంకల్పానికి సిద్ధంగా ఉన్నాయి' },
  profileIncompleteBadge: {
    en: 'Add gotra and nakshatra (or rashi) in your profile for the best experience',
    te: 'మంచి అనుభవానికి ప్రొఫైల్‌లో గోత్రం మరియు నక్షత్రం (లేదా రాశి) జోడించండి',
  },
  gotraNakshatraSection: { en: 'Gotra & birth star', te: 'గోత్ర & నక్షత్ర నిర్ధారణ' },
  gotraFieldLabel: { en: 'Gotra', te: 'గోత్రం' },
  janmaNakshatraFieldLabel: { en: 'Janma Nakshatra', te: 'జన్మ నక్షత్రం' },
  editRitualDetails: { en: 'Edit for today', te: 'ఈ రోజు కోసం మార్చు' },
  sankalpaIntentLabel: { en: 'Purpose (Telugu elaboration)', te: 'సంకల్ప ఉద్దేశం' },
  intentGeneral: { en: 'General wellbeing', te: 'సాధారణ శ్రేయస్సు' },
  intentHealth: { en: 'Health & longevity', te: 'ఆరోగ్యం' },
  intentWealth: { en: 'Wealth', te: 'ఐశ్వర్యం' },
  intentPapam: { en: 'Removal of sins', te: 'పాప నివృత్తి' },
  intentBusiness: { en: 'Business growth', te: 'వ్యాపారాభివృద్ధి' },
} as const

export type GenericSankalpamLabelKey = keyof typeof GENERIC_SANKALPAM_LABELS

export function t(key: GenericSankalpamLabelKey, langCode: string): string {
  const row = GENERIC_SANKALPAM_LABELS[key] as Record<string, string>
  const lc = (langCode || 'en').toLowerCase()
  if (row[lc]) return row[lc]
  return row.en
}

const STATE_LEVEL_LABEL_BY_COUNTRY: Record<string, keyof typeof GENERIC_SANKALPAM_LABELS> = {
  US: 'state',
  IN: 'state',
  AU: 'state',
  CA: 'province',
  GB: 'stateProvince',
}

export function getStateLevelLabelKey(countryCode: string): keyof typeof GENERIC_SANKALPAM_LABELS {
  return STATE_LEVEL_LABEL_BY_COUNTRY[countryCode] || 'stateProvince'
}

export function getStateLevelPlaceholderKey(countryCode: string): keyof typeof GENERIC_SANKALPAM_LABELS {
  if (countryCode === 'CA') return 'selectProvince'
  return 'selectState'
}
