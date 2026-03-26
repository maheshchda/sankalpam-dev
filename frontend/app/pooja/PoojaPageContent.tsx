'use client'

import { useEffect, useState, useRef, useMemo, type ReactNode } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'react-toastify'
import Link from 'next/link'
import HomeButton from '@/components/HomeButton'
import { getPoojaSlug, poojaSlugMatchesFilter } from '@/lib/poojaSlugs'
import { motion, AnimatePresence } from 'framer-motion'
import Select from 'react-select'
import { Country, State, City } from 'country-state-city'

interface Pooja {
  id: number
  name: string
  description: string
  duration_minutes: number
}

interface SankalpamData {
  sankalpam_text: string
  nearby_river: string
  session_id: number
  sankalpam_audio_url?: string
  profile_ready?: boolean
  highlight_names?: string[]
}

interface FamilyMemberRow {
  id: number
  name: string
  relation: string
  is_deceased?: boolean
}

function isSankalpaProfileReady(u: { gotram?: string; birth_nakshatra?: string; birth_rashi?: string } | null): boolean {
  if (!u) return false
  const g = (u.gotram || '').trim()
  const nak = (u.birth_nakshatra || '').trim()
  const rashi = (u.birth_rashi || '').trim()
  return Boolean(g && (nak || rashi))
}

function renderLineWithNameHighlights(line: string, names: string[]): ReactNode {
  const uniq = Array.from(new Set(names)).filter(Boolean).sort((a, b) => b.length - a.length)
  if (!uniq.length) return line
  const parts: ReactNode[] = []
  let remaining = line
  let key = 0
  while (remaining.length) {
    let earliest = -1
    let matched = ''
    for (const n of uniq) {
      const idx = remaining.indexOf(n)
      if (idx >= 0 && (earliest < 0 || idx < earliest)) {
        earliest = idx
        matched = n
      }
    }
    if (earliest < 0) {
      parts.push(remaining)
      break
    }
    if (earliest > 0) parts.push(remaining.slice(0, earliest))
    parts.push(
      <strong key={`h-${key++}`} className="text-xl font-bold text-amber-950">
        {matched}
      </strong>
    )
    remaining = remaining.slice(earliest + matched.length)
  }
  return <>{parts}</>
}

// Available languages for Sankalpam (must match backend Language enum codes)
const SANKALPAM_LANGUAGES: { code: string; label: string }[] = [
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

// Map profile preferred_language (API returns enum value e.g. "telugu" or code "te") to dropdown code
function preferredLanguageToCode(preferred: string | undefined): string {
  if (!preferred || !preferred.trim()) return ''
  const s = preferred.trim().toLowerCase()
  if (s.length === 2) return s // already a code
  const found = SANKALPAM_LANGUAGES.find(({ label }) => label.toLowerCase() === s)
  return found ? found.code : ''
}

// Page labels: `en` required; add other language codes (same as Sankalpam language) as needed.
const POOJA_PAGE_LABELS: Record<string, Record<string, string>> = {
  appName: { en: 'Sankalpam', te: 'సంకల్పం' },
  backToDashboard: { en: 'Back to Dashboard', te: 'డాష్‌బోర్డ్‌కు తిరిగి' },
  logout: { en: 'Logout', te: 'లాగౌట్' },
  location: { en: 'Location', te: 'స్థానం' },
  getCurrentLocation: { en: 'Get current location', te: 'ప్రస్తుత స్థానం పొందండి' },
  useApproxLocation: { en: 'Use approximate location', te: 'అంచనా స్థానం ఉపయోగించండి' },
  locationDesc: { en: 'Location where the pooja and Sankalpam are being performed. Use "Get current location" (browser GPS) or "Use approximate location" (from your internet connection). You can also enter city, state, and country manually.', te: 'పూజ మరియు సంకల్పం నిర్వహించే స్థానం. "ప్రస్తుత స్థానం పొందండి" (బ్రౌజర్ GPS) లేదా "అంచనా స్థానం ఉపయోగించండి" ఉపయోగించండి. నగరం, రాష్ట్రం మరియు దేశాన్ని మాన్యువల్‌గా నమోదు చేయవచ్చు.' },
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
  languageDesc: { en: 'Choose the language in which the Sankalpam will be generated. This overrides your profile language for this pooja.', te: 'సంకల్పం ఏ భాషలో రూపొందించబడుతుందో ఎంచుకోండి. ఈ పూజకు మీ ప్రొఫైల్ భాషను ఇది ఓవర్రైడ్ చేస్తుంది.' },
  language: { en: 'Language', te: 'భాష' },
  selectLanguage: { en: 'Select language...', te: 'భాష ఎంచుకోండి...' },
  selectAPooja: { en: 'Select a Pooja', te: 'పూజ ఎంచుకోండి' },
  poojaListDesc: { en: 'Poojas listed below have a Sankalpam template in the selected language. Choose one to generate and play a personalized Sankalpam.', te: 'ఎంచుకున్న భాషలో సంకల్పం టెంప్లేట్ ఉన్న పూజలు క్రింద ఇవ్వబడ్డాయి. వ్యక్తిగత సంకల్పాన్ని రూపొందించడానికి మరియు ప్లే చేయడానికి ఒకటి ఎంచుకోండి.' },
  selectLangFirst: { en: 'Select a language above to see available poojas.', te: 'అందుబాటులో ఉన్న పూజలను చూడడానికి పైన భాషను ఎంచుకోండి.' },
  noPoojasForLang: { en: 'No poojas available for this language. Add template files under backend/templates/ for the selected language, or choose Sanskrit/Hindi.', te: 'ఈ భాషకు పూజలు అందుబాటులో లేవు. ఎంచుకున్న భాషకు backend/templates/ కింద టెంప్లేట్ ఫైల్‌లను జోడించండి, లేదా సంస్కృతం/హిందీ ఎంచుకోండి.' },
  duration: { en: 'Duration', te: 'వ్యవధి' },
  minutes: { en: 'minutes', te: 'నిమిషాలు' },
  selected: { en: 'Selected', te: 'ఎంచుకున్నారు' },
  selectAndStart: { en: 'Select & Start', te: 'ఎంచుకొని ప్రారంభించండి' },
  sankalpam: { en: 'Sankalpam', te: 'సంకల్పం' },
  nearbyRiver: { en: 'Nearby River', te: 'దగ్గరి నది' },
  generatingSankalpam: { en: 'Generating Sankalpam...', te: 'సంకల్పం రూపొందిస్తోంది...' },
  playSankalpam: { en: 'Play Sankalpam', te: 'సంకల్పం ప్లే చేయండి' },
  playing: { en: 'Playing...', te: 'ప్లే అవుతోంది...' },
  pause: { en: 'Pause', te: 'విరామం' },
  rewind: { en: 'Rewind', te: 'వెనుకకు' },
  forward: { en: 'Forward', te: 'ముందుకు' },
  audioUnavailable: { en: 'Audio generation in progress or unavailable. Visual playback only.', te: 'ఆడియో రూపొందణ ప్రగతిలో లేదా అందుబాటులో లేదు. విజువల్ ప్లేబ్యాక్ మాత్రమే.' },
  sankalpaSetupTitle: { en: 'Sankalpa setup', te: 'సంకల్ప తయారీ' },
  sankalpaSetupParticipants: { en: 'Who is participating in this pooja with you?', te: 'ఈ పూజలో మీతో పాటు ఎవరెవరు పాల్గొంటున్నారు?' },
  profileReadyBadge: { en: 'Your details are ready for Sankalpam', te: 'మీ వివరాలు సంకల్పానికి సిద్ధంగా ఉన్నాయి' },
  profileIncompleteBadge: { en: 'Add gotra and nakshatra (or rashi) in your profile for the best experience', te: 'మంచి అనుభవానికి ప్రొఫైల్‌లో గోత్రం మరియు నక్షత్రం (లేదా రాశి) జోడించండి' },
  gotraNakshatraSection: { en: 'Gotra & birth star', te: 'గోత్ర & నక్షత్ర నిర్ధారణ' },
  editRitualDetails: { en: 'Edit for today', te: 'ఈ రోజు కోసం మార్చు' },
  sankalpaIntentLabel: { en: 'Purpose (Telugu elaboration)', te: 'సంకల్ప ఉద్దేశం' },
  intentGeneral: { en: 'General wellbeing', te: 'సాధారణ శ్రేయస్సు' },
  intentHealth: { en: 'Health & longevity', te: 'ఆరోగ్యం' },
  intentWealth: { en: 'Wealth', te: 'ఐశ్వర్యం' },
  intentPapam: { en: 'Removal of sins', te: 'పాప నివృత్తి' },
  intentBusiness: { en: 'Business growth', te: 'వ్యాపారాభివృద్ధి' },
  startThePooja: {
    en: 'Start the Pooja',
    te: 'పూజను ప్రారంభించండి',
    hi: 'पूजा आरंभ करें',
    sa: 'पूजां आरभत',
    ta: 'பூஜையைத் தொடங்குங்கள்',
    kn: 'ಪೂಜೆಯನ್ನು ಪ್ರಾರಂಭಿಸಿ',
    ml: 'പൂജ ആരംഭിക്കുക',
    mr: 'पूजा सुरू करा',
    gu: 'પૂજા શરૂ કરો',
    bn: 'পূজা শুরু করুন',
    or: 'ପୂଜା ଆରମ୍ଭ କରନ୍ତୁ',
    pa: 'ਪੂਜਾ ਸ਼ੁਰੂ ਕਰੋ',
  },
  poojaPreparationTitle: {
    en: 'Pooja preparation',
    te: 'పూజ సిద్ధత',
    hi: 'पूजा की तैयारी',
    sa: 'पूजा-पूर्वतैयारी',
    ta: 'பூஜை தயாரிப்பு',
    kn: 'ಪೂಜೆ ತಯಾರಿ',
    ml: 'പൂജയുടെ തയ്യാറെടുപ്പ്',
    mr: 'पूजा तयारी',
    gu: 'પૂજાની તૈયારી',
    bn: 'পূজার প্রস্তুতি',
    or: 'ପୂଜା ପ୍ରସ୍ତୁତି',
    pa: 'ਪੂਜਾ ਦੀ ਤਿਆਰੀ',
  },
  poojaPreparationBody: {
    en: 'Prepare a clean, sacred space; bathe and dress suitably; set up the altar and offerings before you begin the Sankalpam.',
    te: 'శుభ్రమైన పవిత్ర స్థలం సిద్ధం చేయండి; స్నానం చేసి తగిన వస్త్రాలు ధరించండి; సంకల్పానికి ముందు వేదిక లేదా అర్చన సామగ్రిని అమర్చండి.',
    hi: 'स्वच्छ एवं पवित्र स्थान तैयार करें; स्नान कर उपयुक्त वस्त्र धारण करें; संकल्प से पूर्व वेदी-सामग्री व्यवस्थित करें।',
    sa: 'शुद्धं पवित्रं च स्थानं सज्जयतु; स्नानं कृत्वा युक्तवस्त्रं धारयतु; संकल्पात् पूर्वं वेदिकां उपकरणानि च व्यवस्थापयतु।',
    ta: 'சுத்தமான புனித இடத்தைத் தயாருங்கள்; குளித்து ஏற்றவுடை அணியுங்கள்; சங்கல்பத்திற்கு முன் வேதிகையை அமைக்கவும்.',
    kn: 'ಶುದ್ಧವಾದ ಪವಿತ್ರ ಸ್ಥಳವನ್ನು ಸಿದ್ಧಿಸಿ; ಸ್ನಾನ ಮಾಡಿ ಮರ್ಯಾದೆಯ ವಸ್ತ್ರ ಧರಿಸಿ; ಸಂಕಲ್ಪಕ್ಕು ಮುನ್ನ ವೇದಿಕೆಯನ್ನು ಸಜ್ಜುಗೊಳಿಸಿ.',
    ml: 'വിശുദ്ധമായ സ്ഥലം തയ്യാറാക്കുക; സ്നാനം ചെയ്ത് ഉചിതമായ വസ്ത്രം ധരിക്കുക; സംകല്പത്തിന് മുമ്പ് വേദികയം സജ്ജമാക്കുക.',
    mr: 'स्वच्छ पवित्र जागा तयार करा; अंघोळ घेऊन योग्य वस्त्रे घाला; संकल्पापूर्वी वेदी व सामग्री व्यवस्थित करा.',
    gu: 'સ્વચ્છ પવિત્ર સ્થાન તૈયાર કરો; સ્નાન કરી યોગ્ય વસ્ત્રો પહેરો; સંકલ્પ પહેલાં વેદી ગોઠવો.',
    bn: 'পরিষ্কার পবিত্র স্থান প্রস্তুত করুন; স্নান করে উপযুক্ত বস্ত্র পরিধান করুন; সংকল্পের আগে বেদি সাজান।',
    or: 'ସ୍ୱଚ୍ଛ ପବିତ୍ର ସ୍ଥାନ ପ୍ରସ୍ତୁତ କରନ୍ତୁ; ସ୍ନାନ କରି ଉପଯୁକ୍ତ ବସ୍ତ୍ର ପିନ୍ଧନ୍ତୁ; ସଂକଳ୍ପ ପୂର୍ବେ ବେଦୀ ବ୍ୟବସ୍ଥା କରନ୍ତୁ।',
    pa: 'ਸਾਫ਼ ਪਵਿੱਤਰ ਸਥਾਨ ਤਿਆਰ ਕਰੋ; ਇਸ਼ਨਾਨ ਕਰਕੇ ਢੁਕਵੇਂ ਕਪੜੇ ਪਾਓ; ਸੰਕਲਪ ਤੋਂ ਪਹਿਲਾਂ ਵੇਦੀ ਤਿਆਰ ਕਰੋ।',
  },
  poojaMaterialTitle: {
    en: 'Materials required',
    te: 'అవసరమైన సామగ్రి',
    hi: 'आवश्यक सामग्री',
    sa: 'आवश्यकाः द्रव्याः',
    ta: 'தேவையான பொருட்கள்',
    kn: 'ಅಗತ್ಯವಿರುವ ಸಾಮಗ್ರಿಗಳು',
    ml: 'ആവശ്യമായ സാമഗ്രികൾ',
    mr: 'आवश्यक साहित्य',
    gu: 'જરૂરી સામગ્રી',
    bn: 'প্রয়োজনীয় সামগ্রী',
    or: 'ଆବଶ୍ୟକ ସାମଗ୍ରୀ',
    pa: 'ਲੋੜੀਂਦੀ ਸਮਗ੍ਰੀ',
  },
  poojaMaterialBody: {
    en: 'Flowers, lamps, incense, naivedyam, and other items depend on your tradition. Open the full list for this pooja.',
    te: 'పువ్వులు, దీపాలు, అగరువత్తులు, నైవేద్యం మొదలైనవి మీ సంప్రదాయాన్ని బట్టి మారుతాయి. ఈ పూజకు పూర్తి జాబితాను తెరవండి.',
    hi: 'फूल, दीप, धूप, नैवेद्य आदि आपकी परंपरा पर निर्भर करते हैं। इस पूजा की पूरी सूची देखें।',
    sa: 'पुष्पाणि, दीपाः, धूपः, नैवेद्यं च परम्परायाम् अधीनाः। अस्याः पूजायाः सम्पूर्णं सूच्यां पश्यतु।',
    ta: 'மலர், விளக்கு, தூபம், நைவேத்யம் முதலியன பாரம்பரியத்தைப் பொறுத்து மாறும். முழு பட்டியலைத் திறக்கவும்.',
    kn: 'ಹೂವು, ದೀಪ, ಧೂಪ, ನೈವೇದ್ಯ ಮುಂತಾದವು ಸಂಪ್ರದಾಯಕ್ಕೆ ಅನುಗುಣವಾಗುತ್ತವೆ. ಪೂರ್ಣ ಪಟ್ಟಿಗೆ ಹೋಗಿ.',
    ml: 'പുഷ്പങ്ങൾ, വിളക്ക്, ധൂപം, നൈവേദ്യം എന്നിവ പാരമ്പര്യമനുസരിച്ച് വ്യത്യാസപ്പെടും. പൂർണ്ണ പട്ടിക തുറക്കുക.',
    mr: 'फुले, दिवा, धूप, नैवेद्य इतर सामग्री परंपरेनुसार बदलते. पूर्ण यादी पाहा.',
    gu: 'ફૂલ, દીવો, ધૂપ, નૈવેદ્ય વગેરે પરંપરા અનુસાર બદલાય છે. સંપૂર્ણ યાદી દેખો.',
    bn: 'ফুল, প্রদীপ, ধূপ, নৈবেদ্য ইত্যাদি পরম্পরা অনুযায়ী ভিন্ন হতে পারে। সম্পূর্ণ তালিকা দেখুন।',
    or: 'ଫୁଲ, ଦୀପ, ଧୂପ, ନୈବେଦ୍ୟ ଇତ୍ୟାଦି ପରମ୍ପରା ଅନୁସାରେ ଭିନ୍ନ ହୋଇପାରେ। ସମ୍ପୂର୍ଣ ତାଲିକା ଦେଖନ୍ତୁ।',
    pa: 'ਫੁੱਲ, ਦੀਵੇ, ਧੂਪ, ਨੈਵੇਦ ਆਦਿ ਰੀਤ ਅਨੁਸਾਰ ਬਦਲਦੇ ਹਨ। ਪੂਰੀ ਸੂਚੀ ਖੋਲ੍ਹੋ।',
  },
  readinessLinkLabel: {
    en: 'Preparation guide',
    te: 'సిద్ధత మార్గదర్శకం',
    hi: 'तैयारी मार्गदर्शिका',
    sa: 'सन्नाह-निर्देशिका',
    ta: 'தயாரிப்பு வழிகாட்டி',
    kn: 'ತಯಾರಿ ಮಾರ್ಗದರ್ಶಿ',
    ml: 'തയ്യാറെടുപ്പ് മാർഗ്ഗനിർദ്ദേശം',
    mr: 'तयारी मार्गदर्शक',
    gu: 'તૈયારી માર્ગદર્શિકા',
    bn: 'প্রস্তুতি নির্দেশিকা',
    or: 'ପ୍ରସ୍ତୁତି ମାର୍ଗଦର୍ଶିକା',
    pa: 'ਤਿਆਰੀ ਗਾਈਡ',
  },
  itemsLinkLabel: {
    en: 'Full materials list',
    te: 'పూర్తి సామగ్రి జాబితా',
    hi: 'पूरी सामग्री सूची',
    sa: 'सम्पूर्ण-द्रव्य-सूची',
    ta: 'முழு பொருட்கள் பட்டியல்',
    kn: 'ಪೂರ್ಣ ಸಾಮಗ್ರಿ ಪಟ್ಟಿ',
    ml: 'പൂർണ്ണ സാമഗ്രി പട്ടിക',
    mr: 'संपूर्ण साहित्य यादी',
    gu: 'સંપૂર્ણ સામગ્રી યાદી',
    bn: 'সম্পূর্ণ সামগ্রীর তালিকা',
    or: 'ସମ୍ପୂର୍ଣ ସାମଗ୍ରୀ ତାଲିକା',
    pa: 'ਪੂਰੀ ਸਮਗ੍ਰੀ ਸੂਚੀ',
  },
}

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function t (key: keyof typeof POOJA_PAGE_LABELS, langCode: string): string {
  const labels = POOJA_PAGE_LABELS[key]
  const lc = (langCode || 'en').toLowerCase()
  if (labels[lc]) return labels[lc]
  return labels.en
}

// Label for the middle field (State/Province/Region) depending on country
const STATE_LEVEL_LABEL_BY_COUNTRY: Record<string, keyof typeof POOJA_PAGE_LABELS> = {
  US: 'state',           // United States
  IN: 'state',           // India
  AU: 'state',           // Australia
  CA: 'province',        // Canada
  GB: 'stateProvince',   // United Kingdom (could use "County" - dataset uses states)
}
function getStateLevelLabelKey(countryCode: string): keyof typeof POOJA_PAGE_LABELS {
  return STATE_LEVEL_LABEL_BY_COUNTRY[countryCode] || 'stateProvince'
}
function getStateLevelPlaceholderKey(countryCode: string): keyof typeof POOJA_PAGE_LABELS {
  if (countryCode === 'CA') return 'selectProvince'
  return 'selectState'
}

type PoojaPageProps = {
  /** When set, show only poojas matching this type (e.g. /pooja/ganesha shows only Ganesh Pooja) */
  includedPooja?: 'ganesha' | 'lakshmi' | null
  /** From /pooja/[poojaSlug] or calendar — show only the pooja whose name slug matches */
  filterPoojaSlug?: string | null
}

function isGaneshaPooja(name: string): boolean {
  const value = (name || '').toLowerCase()
  return value.includes('ganesh') || value.includes('ganesha') || value.includes('vinayaka')
}

function isLakshmiPooja(name: string): boolean {
  const value = (name || '').toLowerCase()
  return value.includes('lakshmi') || value.includes('laxmi')
}

function matchesIncludedPooja(name: string, includedPooja: 'ganesha' | 'lakshmi' | null): boolean {
  if (!includedPooja) return true
  if (includedPooja === 'ganesha') return isGaneshaPooja(name)
  if (includedPooja === 'lakshmi') return isLakshmiPooja(name)
  return true
}

export function PoojaPageContent({ includedPooja = null, filterPoojaSlug = null }: PoojaPageProps) {
  const searchParams = useSearchParams()
  const poojaSlugFromUrl = searchParams.get('pooja')
  const effectivePoojaSlug = filterPoojaSlug ?? poojaSlugFromUrl
  const { user, loading: authLoading, logout } = useAuth()
  const router = useRouter()

  const [poojas, setPoojas] = useState<Pooja[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedPooja, setSelectedPooja] = useState<Pooja | null>(null)
  const [sankalpamLanguageCode, setSankalpamLanguageCode] = useState<string>('en')

  const [location, setLocation] = useState({
    city: '',
    state: '',
    country: '',
    latitude: '',
    longitude: '',
  })

  // Country/state/city use country-state-city (states by country, cities by country+state or country-only)
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>('')
  const [selectedStateCode, setSelectedStateCode] = useState<string>('')
  const [geocodeLoading, setGeocodeLoading] = useState(false)

  // Some countries have no states/provinces; options depend on selected country
  const statesForCountry = useMemo(
    () => (selectedCountryCode ? State.getStatesOfCountry(selectedCountryCode) : []),
    [selectedCountryCode]
  )
  const hasStates = statesForCountry.length > 0

  const [sankalpam, setSankalpam] = useState<SankalpamData | null>(null)
  const [sankalpamLoading, setSankalpamLoading] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentLine, setCurrentLine] = useState(0)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [playbackCurrentTime, setPlaybackCurrentTime] = useState(0)
  const [playbackDuration, setPlaybackDuration] = useState(0)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const visualIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const profileInitDoneRef = useRef(false)
  // Latest profile from server (so Pooja page always gets current address)
  const [userProfileForLocation, setUserProfileForLocation] = useState<{
    current_city?: string
    current_state?: string
    current_country?: string
    birth_city?: string
    birth_state?: string
    birth_country?: string
    preferred_language?: string
  } | null>(null)

  const [familyMembers, setFamilyMembers] = useState<FamilyMemberRow[] | null>(null)
  const [participantIds, setParticipantIds] = useState<number[] | null>(null)
  const [sankalpaIntent, setSankalpaIntent] = useState('general')
  const [showGotraNakEdit, setShowGotraNakEdit] = useState(false)
  const [gotraOverride, setGotraOverride] = useState('')
  const [nakshatraOverride, setNakshatraOverride] = useState('')
  const familyHydratedRef = useRef(false)

  // Fetch latest user profile when Pooja page loads so we have current Country, State, City
  useEffect(() => {
    if (authLoading || !user) return
    api.get('/api/auth/me')
      .then((res) => setUserProfileForLocation(res.data))
      .catch(() => {})
  }, [authLoading, user])

  useEffect(() => {
    if (authLoading || !user) return
    api
      .get('/api/family/members')
      .then((res) => {
        const list = Array.isArray(res.data) ? res.data : []
        setFamilyMembers(
          list.map((m: { id: number; name: string; relation: string; is_deceased?: boolean }) => ({
            id: m.id,
            name: m.name,
            relation: m.relation,
            is_deceased: m.is_deceased,
          }))
        )
      })
      .catch(() => setFamilyMembers([]))
  }, [authLoading, user])

  useEffect(() => {
    if (familyMembers === null || familyHydratedRef.current) return
    familyHydratedRef.current = true
    if (familyMembers.length === 0) {
      setParticipantIds([])
      return
    }
    setParticipantIds(familyMembers.filter((m) => !m.is_deceased).map((m) => m.id))
  }, [familyMembers])

  // Initialize location and language from user profile once.
  // Preference order:
  // - Language: preferred_language, fallback English
  // - Location: current address (where user lives now) first, fallback to birth place
  useEffect(() => {
    if (!userProfileForLocation || profileInitDoneRef.current) return
    profileInitDoneRef.current = true

    const birthCity = userProfileForLocation.birth_city?.trim()
    const birthState = userProfileForLocation.birth_state?.trim()
    const birthCountry = userProfileForLocation.birth_country?.trim()
    const currentCity = userProfileForLocation.current_city?.trim()
    const currentState = userProfileForLocation.current_state?.trim()
    const currentCountry = userProfileForLocation.current_country?.trim()
    const city = currentCity || birthCity
    const state = currentState || birthState
    const country = currentCountry || birthCountry
    const prefLang = userProfileForLocation.preferred_language

    if (country || state || city) {
      let countryCode = ''
      let stateCode = ''
      if (country) {
        const match = Country.getAllCountries().find(
          (c) => c.name.toLowerCase() === country.toLowerCase()
        )
        if (match) {
          countryCode = match.isoCode
          const states = State.getStatesOfCountry(match.isoCode)
          if (state && states.length > 0) {
            const stateMatch = states.find(
              (s) => s.name.toLowerCase() === state.toLowerCase()
            )
            if (stateMatch) stateCode = stateMatch.isoCode
          }
        }
      }
      setLocation((prev) => ({
        ...prev,
        city: city || prev.city,
        state: state || prev.state,
        country: country || prev.country,
        latitude: '',
        longitude: '',
      }))
      if (countryCode) setSelectedCountryCode(countryCode)
      if (stateCode) setSelectedStateCode(stateCode)
    }

    const langCode = preferredLanguageToCode(prefLang)
    setSankalpamLanguageCode(langCode || 'en')
  }, [userProfileForLocation])

  // When location is set from Get current location / IP, sync country and state codes so dropdowns show correctly
  useEffect(() => {
    if (location.country && !selectedCountryCode) {
      const match = Country.getAllCountries().find(
        (c) => c.name.toLowerCase() === location.country.trim().toLowerCase()
      )
      if (match) setSelectedCountryCode(match.isoCode)
    }
  }, [location.country, selectedCountryCode])
  useEffect(() => {
    if (location.state && selectedCountryCode && !selectedStateCode) {
      const match = State.getStatesOfCountry(selectedCountryCode).find(
        (s) => s.name.toLowerCase() === location.state.trim().toLowerCase()
      )
      if (match) setSelectedStateCode(match.isoCode)
    }
  }, [location.state, selectedCountryCode, selectedStateCode])

  // Redirect to login only after auth state is known
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [authLoading, user, router])

  // When language is selected, load poojas for that language; when language is cleared or changed, clear selection
  useEffect(() => {
    if (!authLoading && user) {
      if (sankalpamLanguageCode) {
        fetchPoojas(sankalpamLanguageCode)
        setSelectedPooja(null)
        setSankalpam(null)
        setAudioUrl(null)
        setIsPlaying(false)
        setCurrentLine(0)
      } else {
        setPoojas([])
        setSelectedPooja(null)
        setSankalpam(null)
        setAudioUrl(null)
        setLoading(false)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, user, sankalpamLanguageCode, includedPooja, filterPoojaSlug, effectivePoojaSlug])

  const fetchPoojas = async (languageCode: string) => {
    try {
      setLoading(true)
      const response = await api.get('/api/pooja/list', {
        params: languageCode ? { language_code: languageCode } : undefined,
      })
      let poojaList: Pooja[] = Array.isArray(response.data) ? response.data : []

      // If there are no templates for selected language, fall back to general pooja list.
      if (languageCode && poojaList.length === 0) {
        const fallbackResponse = await api.get('/api/pooja/list')
        poojaList = Array.isArray(fallbackResponse.data) ? fallbackResponse.data : []
      }

      // When coming from /pooja/[slug] or ?pooja=slug, show only that calendar pooja
      if (effectivePoojaSlug) {
        poojaList = poojaList.filter((pooja) =>
          poojaSlugMatchesFilter(pooja.name, effectivePoojaSlug)
        )
      }
      // When on /pooja/ganesha or /pooja/lakshmi, show only poojas of that type
      else if (includedPooja) {
        poojaList = poojaList.filter((pooja) => matchesIncludedPooja(pooja.name, includedPooja))
      }

      // Sort so Ganesh Pooja appears first if present
      poojaList.sort((a, b) => {
        const aIsGanesh = a.name.toLowerCase().includes('ganesh')
        const bIsGanesh = b.name.toLowerCase().includes('ganesh')
        if (aIsGanesh && !bIsGanesh) return -1
        if (!aIsGanesh && bIsGanesh) return 1
        return a.name.localeCompare(b.name)
      })

      setPoojas(poojaList)
    } catch (error) {
      console.error('Error fetching poojas:', error)
      toast.error('Failed to load poojas')
    } finally {
      setLoading(false)
    }
  }

  const reverseGeocode = async (lat: string, lon: string) => {
    try {
      const response = await api.get('/api/templates/reverse-geocode', {
        params: { latitude: lat, longitude: lon },
      })

      if (response.data.city || response.data.state || response.data.country) {
        setLocation((prev) => ({
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

  // Fallback: get approximate location from IP (works when browser geolocation is blocked or fails)
  const getApproximateLocationFromIP = async () => {
    toast.info('Getting approximate location from your internet connection…')
    setSankalpamLoading(true)
    try {
      const res = await fetch('https://ipapi.co/json/')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const city = data.city || ''
      const state = data.region || data.region_code || ''
      const country = data.country_name || data.country_code || ''
      const lat = data.latitude != null ? String(data.latitude) : ''
      const lon = data.longitude != null ? String(data.longitude) : ''
      setLocation({
        city,
        state,
        country,
        latitude: lat,
        longitude: lon,
      })
      toast.success('Approximate location set from your IP. You can edit the fields if needed.')
    } catch (err) {
      console.error('[Pooja Location] IP lookup failed:', err)
      toast.error('Could not get location from IP. Please enter city, state, and country manually.')
    } finally {
      setSankalpamLoading(false)
    }
  }

  const getCurrentLocation = async () => {
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported by your browser. Use "Use approximate location" below.')
      return
    }

    // Check permission state when supported (Chrome, etc.)
    let permissionState: string | null = null
    if ('permissions' in navigator && 'query' in navigator.permissions) {
      try {
        const result = await navigator.permissions.query({ name: 'geolocation' as PermissionName })
        permissionState = result.state
        if (result.state === 'denied') {
          toast.error('Location is blocked for this site. Use "Use approximate location" or allow location in site settings.')
          return
        }
      } catch {
        // Permissions API not fully supported, continue with getCurrentPosition
      }
    }

    toast.info('Getting your location… Allow when your browser asks.')
    try {
      setSankalpamLoading(true)

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const lat = position.coords.latitude.toString()
            const lon = position.coords.longitude.toString()

            setLocation({
              city: '',
              state: '',
              country: '',
              latitude: lat,
              longitude: lon,
            })

            try {
              const response = await api.get('/api/templates/reverse-geocode', {
                params: { latitude: lat, longitude: lon },
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
                toast.warning('Coordinates obtained. Enter city, state, and country manually if needed.')
              }
            } catch (err: any) {
              console.error('[Pooja Location] Reverse geocode failed:', err)
              const status = err.response?.status
              const detail = err.response?.data?.detail
              if (status === 401) {
                toast.error('Please log in again, then try Get Location.')
              } else if (detail && typeof detail === 'string') {
                toast.error(`Address lookup failed: ${detail}`)
              } else {
                toast.error('Could not get address from coordinates. Enter city, state, and country manually.')
              }
            }
          } catch (error) {
            console.error('[Pooja Location] Process error:', error)
            toast.error('Error processing location data. Please enter manually.')
          } finally {
            setSankalpamLoading(false)
          }
        },
        (error) => {
          console.error('[Pooja Location] Geolocation error:', error.code, error.message)
          let errorMessage = 'Could not get your location. '

          switch (error.code) {
            case 1: // PERMISSION_DENIED
              errorMessage += 'Use "Use approximate location" below or allow location in site settings.'
              break
            case 2: // POSITION_UNAVAILABLE
              errorMessage += 'Use "Use approximate location" below or enter address manually.'
              break
            case 3: // TIMEOUT
              errorMessage += 'Use "Use approximate location" below or try again.'
              break
            default:
              errorMessage += 'Use "Use approximate location" below or enter manually.'
          }

          toast.error(errorMessage)
          setSankalpamLoading(false)
        },
        {
          enableHighAccuracy: false, // false often works better on desktop (faster, fewer timeouts)
          timeout: 20000,
          maximumAge: 120000, // Use cached position up to 2 min
        }
      )
    } catch (error) {
      console.error('[Pooja Location] getCurrentLocation error:', error)
      toast.error('An error occurred. Try "Use approximate location" or enter manually.')
      setSankalpamLoading(false)
    }
  }

  // Forward geocode: when country, state, city are selected, fetch lat/lon and set display-only fields
  const fetchLatLonFromPlace = async (city: string, state: string, country: string) => {
    const c = city?.trim()
    const s = state?.trim()
    const co = country?.trim()
    if (!c || !co) return
    setGeocodeLoading(true)
    try {
      const response = await api.get('/api/templates/forward-geocode', {
        params: { city: c, state: s, country: co },
      })
      const lat = response.data?.latitude ?? ''
      const lon = response.data?.longitude ?? ''
      setLocation((prev) => ({ ...prev, latitude: lat, longitude: lon }))
      if (lat && lon) {
        toast.success('Coordinates updated for selected place.')
      } else {
        toast.warning('Could not resolve coordinates for this place. Sankalpam may use default location.')
      }
    } catch (err) {
      console.error('Forward geocode failed:', err)
      toast.error('Could not get coordinates for this place.')
      setLocation((prev) => ({ ...prev, latitude: '', longitude: '' }))
    } finally {
      setGeocodeLoading(false)
    }
  }

  // When user has selected place (country + city, and state if country has states), get lat/lon automatically
  const placeKeyRef = useRef<string>('')
  useEffect(() => {
    const city = location.city?.trim()
    const state = location.state?.trim()
    const country = location.country?.trim()
    const key = `${country}|${state}|${city}`
    const placeComplete = city && country && (hasStates ? state : true)
    if (placeComplete && key !== placeKeyRef.current) {
      placeKeyRef.current = key
      // Only call backend if we don't already have coordinates (e.g. from package or previous fetch)
      if (!location.latitude || !location.longitude) {
        fetchLatLonFromPlace(city, state || '', country)
      }
    }
    if (!city || !country) placeKeyRef.current = ''
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.country, location.state, location.city, location.latitude, location.longitude, hasStates])

  const toggleParticipant = (memberId: number) => {
    setParticipantIds((prev) => {
      if (prev === null) return prev
      if (prev.includes(memberId)) return prev.filter((x) => x !== memberId)
      return [...prev, memberId]
    })
  }

  const generateSankalpam = async (sessionId: number) => {
    try {
      setSankalpamLoading(true)

      const city = location.city?.trim()
      const state = location.state?.trim()
      const country = location.country?.trim()

      const needState = State.getStatesOfCountry(selectedCountryCode || '').length > 0
      if (!city || !country || (needState && !state)) {
        toast.error(needState ? 'Please select Country, State, and City.' : 'Please select Country and City.')
        setSankalpamLoading(false)
        return
      }

      // Ensure session exists (will raise if not found)
      await api.get(`/api/pooja/session/${sessionId}`)

      // Generate sankalpam for this session, location, and selected language
      // Send browser timezone so Panchang (tithi, nakshatra, yoga, karana) is correct for user's location
      const tzOffsetHours = -new Date().getTimezoneOffset() / 60
      const response = await api.post('/api/sankalpam/generate', {
        session_id: sessionId,
        location_city: city,
        location_state: state,
        location_country: country,
        latitude: location.latitude || null,
        longitude: location.longitude || null,
        timezone_offset_hours: tzOffsetHours,
        language_code: sankalpamLanguageCode || undefined,
        participant_member_ids: participantIds === null ? undefined : participantIds,
        sankalpa_intent: sankalpaIntent || undefined,
        override_gotram:
          showGotraNakEdit && gotraOverride.trim() ? gotraOverride.trim() : undefined,
        override_birth_nakshatra:
          showGotraNakEdit && nakshatraOverride.trim() ? nakshatraOverride.trim() : undefined,
      })

      const sankalpamData: SankalpamData = response.data
      setSankalpam(sankalpamData)

      if (sankalpamData.sankalpam_audio_url) {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        setAudioUrl(`${baseUrl}${sankalpamData.sankalpam_audio_url}`)
      } else {
        setAudioUrl(null)
      }
    } catch (error: any) {
      console.error('Error generating sankalpam:', error)
      toast.error(error.response?.data?.detail || 'Failed to generate sankalpam')
      setSankalpam(null)
      setAudioUrl(null)
    } finally {
      setSankalpamLoading(false)
      setIsPlaying(false)
      setCurrentLine(0)
      setPlaybackCurrentTime(0)
      setPlaybackDuration(0)
    }
  }

  const handleSelectPooja = async (pooja: Pooja) => {
    setSelectedPooja(pooja)
    setSankalpam(null)
    setAudioUrl(null)
    setIsPlaying(false)
    setCurrentLine(0)
    setPlaybackCurrentTime(0)
    setPlaybackDuration(0)

    try {
      const city = location.city?.trim()
      const state = location.state?.trim()
      const country = location.country?.trim()

      const needState = State.getStatesOfCountry(selectedCountryCode || '').length > 0
      if (!city || !country || (needState && !state)) {
        toast.error(needState ? 'Please select Country, State, and City before starting.' : 'Please select Country and City before starting.')
        return
      }

      const response = await api.post('/api/pooja/session', {
        pooja_id: pooja.id,
        location_city: city,
        location_state: state,
        location_country: country,
        latitude: location.latitude || null,
        longitude: location.longitude || null,
      })

      await generateSankalpam(response.data.id)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start pooja session')
    }
  }

  // Sync highlighted line with playback position (audio mode)
  const lines = useMemo(
    () => (sankalpam?.sankalpam_text ? sankalpam.sankalpam_text.split('\n').filter((line: string) => line.trim()) : []),
    [sankalpam]
  )
  useEffect(() => {
    if (!sankalpam || !audioUrl || playbackDuration <= 0 || lines.length === 0) return
    const lineIndex = Math.min(
      lines.length - 1,
      Math.floor((playbackCurrentTime / playbackDuration) * lines.length)
    )
    setCurrentLine(lineIndex)
  }, [sankalpam, audioUrl, playbackDuration, playbackCurrentTime, lines.length])

  const handlePlay = () => {
    if (audioUrl && audioRef.current && sankalpam) {
      audioRef.current.play()
      setIsPlaying(true)
    } else if (sankalpam) {
      // Visual-only: no audio
      if (visualIntervalRef.current) clearInterval(visualIntervalRef.current)
      setIsPlaying(true)
      let lineIndex = currentLine
      visualIntervalRef.current = setInterval(() => {
        if (lineIndex < lines.length - 1) {
          lineIndex++
          setCurrentLine(lineIndex)
        } else {
          if (visualIntervalRef.current) clearInterval(visualIntervalRef.current)
          visualIntervalRef.current = null
          setIsPlaying(false)
        }
      }, 3000)
    }
  }

  const handlePause = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      setIsPlaying(false)
    }
    if (visualIntervalRef.current) {
      clearInterval(visualIntervalRef.current)
      visualIntervalRef.current = null
      setIsPlaying(false)
    }
  }

  const SEEK_SECONDS = 10
  const handleRewind = () => {
    if (audioUrl && audioRef.current) {
      const newTime = Math.max(0, (audioRef.current.currentTime || 0) - SEEK_SECONDS)
      audioRef.current.currentTime = newTime
      setPlaybackCurrentTime(newTime)
    } else if (sankalpam && lines.length > 0) {
      setCurrentLine((prev) => Math.max(0, prev - 1))
    }
  }

  const handleForward = () => {
    if (audioUrl && audioRef.current) {
      const dur = audioRef.current.duration
      const newTime = dur ? Math.min(dur, (audioRef.current.currentTime || 0) + SEEK_SECONDS) : playbackCurrentTime + SEEK_SECONDS
      audioRef.current.currentTime = newTime
      setPlaybackCurrentTime(newTime)
    } else if (sankalpam && lines.length > 0) {
      setCurrentLine((prev) => Math.min(lines.length - 1, prev + 1))
    }
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value)
    if (audioUrl && audioRef.current) {
      audioRef.current.currentTime = value
      setPlaybackCurrentTime(value)
    }
  }

  const onlyOnePooja = poojas.length === 1

  if (authLoading || loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="text-2xl font-bold text-amber-600">
              {t('appName', sankalpamLanguageCode)}
            </Link>
            <div className="flex items-center gap-2 sm:gap-4">
              <HomeButton variant="light" />
              <Link href="/dashboard" className="px-4 py-2 text-gray-700 hover:text-amber-600">
                {t('backToDashboard', sankalpamLanguageCode)}
              </Link>
              <button
                onClick={() => {
                  logout()
                  router.push('/login')
                }}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                {t('logout', sankalpamLanguageCode)}
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Location section (similar to Generate Sankalpam page) */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-2xl font-bold">{t('location', sankalpamLanguageCode)}</h2>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={getCurrentLocation}
                disabled={sankalpamLoading}
                className="px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 disabled:opacity-50"
              >
                📍 {t('getCurrentLocation', sankalpamLanguageCode)}
              </button>
              <button
                type="button"
                onClick={getApproximateLocationFromIP}
                disabled={sankalpamLoading}
                className="px-3 py-1.5 text-sm bg-slate-100 text-slate-700 rounded-md hover:bg-slate-200 disabled:opacity-50"
              >
                🌐 {t('useApproxLocation', sankalpamLanguageCode)}
              </button>
            </div>
          </div>
          <p className="text-gray-600 mb-4 text-sm">
            {t('locationDesc', sankalpamLanguageCode)}
          </p>

          {/* Place selection: Country → (State/Province when country has them) → City */}
            <div className={`grid grid-cols-1 gap-4 mb-4 ${hasStates ? 'md:grid-cols-3' : 'md:grid-cols-2'}`}>
              <div>
                <label className="block text-xs text-gray-600 mb-1">{t('country', sankalpamLanguageCode)}</label>
                <Select<{ value: string; label: string }>
                  options={Country.getAllCountries().map((c) => ({ value: c.isoCode, label: c.name }))}
                  value={location.country ? { value: selectedCountryCode, label: location.country } : null}
                  onChange={(opt) => {
                    const code = opt?.value ?? ''
                    const name = opt?.label ?? ''
                    setSelectedCountryCode(code)
                    setSelectedStateCode('')
                    setLocation((prev) => ({
                      ...prev,
                      country: name,
                      state: '',
                      city: '',
                      latitude: '',
                      longitude: '',
                    }))
                  }}
                  placeholder={t('selectCountry', sankalpamLanguageCode)}
                  isClearable
                  isSearchable
                  className="react-select-container"
                  classNamePrefix="react-select"
                />
              </div>
              {hasStates && (
                <div>
                  <label className="block text-xs text-gray-600 mb-1">{t(getStateLevelLabelKey(selectedCountryCode), sankalpamLanguageCode)}</label>
                  <Select<{ value: string; label: string }>
                    options={statesForCountry.map((s) => ({ value: s.isoCode, label: s.name }))}
                    value={location.state ? { value: selectedStateCode, label: location.state } : null}
                    onChange={(opt) => {
                      const code = opt?.value ?? ''
                      const name = opt?.label ?? ''
                      setSelectedStateCode(code)
                      setLocation((prev) => ({
                        ...prev,
                        state: name,
                        city: '',
                        latitude: '',
                        longitude: '',
                      }))
                    }}
                    placeholder={t(getStateLevelPlaceholderKey(selectedCountryCode), sankalpamLanguageCode)}
                    isClearable
                    isSearchable
                    isDisabled={!selectedCountryCode}
                    className="react-select-container"
                    classNamePrefix="react-select"
                  />
                </div>
              )}
              <div>
                <label className="block text-xs text-gray-600 mb-1">{t('city', sankalpamLanguageCode)}</label>
                <Select<{ value: string; label: string; latitude?: string | null; longitude?: string | null }>
                  options={
                    hasStates
                      ? (City.getCitiesOfState(selectedCountryCode, selectedStateCode) || []).map((c) => ({
                          value: c.name,
                          label: c.name,
                          latitude: c.latitude ?? undefined,
                          longitude: c.longitude ?? undefined,
                        }))
                      : (City.getCitiesOfCountry(selectedCountryCode) || []).map((c) => ({
                          value: c.name,
                          label: c.name,
                          latitude: c.latitude ?? undefined,
                          longitude: c.longitude ?? undefined,
                        }))
                  }
                  value={location.city ? { value: location.city, label: location.city } : null}
                  onChange={(opt) => {
                    const city = opt?.value ?? ''
                    const lat = (opt?.latitude != null && opt?.latitude !== '') ? String(opt.latitude) : ''
                    const lon = (opt?.longitude != null && opt?.longitude !== '') ? String(opt.longitude) : ''
                    setLocation((prev) => ({
                      ...prev,
                      city,
                      latitude: lat,
                      longitude: lon,
                    }))
                  }}
                  placeholder={t('selectCity', sankalpamLanguageCode)}
                  isClearable
                  isSearchable
                  isDisabled={!selectedCountryCode || (hasStates && !selectedStateCode)}
                  className="react-select-container"
                  classNamePrefix="react-select"
                />
              </div>
            </div>

          {/* Latitude and Longitude: display only, below place selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">{t('latitude', sankalpamLanguageCode)}</label>
              <input
                type="text"
                readOnly
                value={location.latitude || (geocodeLoading ? '…' : '')}
                className="w-full rounded-md border-gray-200 bg-gray-50 text-gray-700"
                placeholder="—"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">{t('longitude', sankalpamLanguageCode)}</label>
              <input
                type="text"
                readOnly
                value={location.longitude || (geocodeLoading ? '…' : '')}
                className="w-full rounded-md border-gray-200 bg-gray-50 text-gray-700"
                placeholder="—"
              />
            </div>
          </div>
          <p className="text-gray-500 text-xs mt-1">
            {t('latitudeLongitudeDesc', sankalpamLanguageCode)}
          </p>
        </div>

        {/* Language selection for Sankalpam */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-bold mb-2">{t('sankalpamLanguage', sankalpamLanguageCode)}</h2>
          <p className="text-gray-600 mb-4 text-sm">
            {t('languageDesc', sankalpamLanguageCode)}
          </p>
          <div className="max-w-xs">
            <label htmlFor="sankalpam-language" className="block text-xs text-gray-600 mb-1">{t('language', sankalpamLanguageCode)}</label>
            <select
              id="sankalpam-language"
              value={sankalpamLanguageCode}
              onChange={(e) => setSankalpamLanguageCode(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
            >
              <option value="">{t('selectLanguage', sankalpamLanguageCode)}</option>
              {SANKALPAM_LANGUAGES.map(({ code, label }) => (
                <option key={code} value={code}>{label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Sankalpa: participants, intent, gotra/nakshatra (when language chosen) */}
        {sankalpamLanguageCode ? (
          <div className="bg-white rounded-lg shadow p-6 mb-6 space-y-6">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-2xl font-bold">{t('sankalpaSetupTitle', sankalpamLanguageCode)}</h2>
              {isSankalpaProfileReady(user) ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-800">
                  <span aria-hidden>✓</span> {t('profileReadyBadge', sankalpamLanguageCode)}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-900">
                  {t('profileIncompleteBadge', sankalpamLanguageCode)}
                </span>
              )}
            </div>

            <div>
              <p className="text-gray-600 mb-3 text-sm">{t('sankalpaSetupParticipants', sankalpamLanguageCode)}</p>
              {familyMembers === null ? (
                <p className="text-gray-500 text-sm">…</p>
              ) : familyMembers.filter((m) => !m.is_deceased).length === 0 ? (
                <p className="text-gray-500 text-sm">
                  {sankalpamLanguageCode === 'te'
                    ? 'కుటుంబ సభ్యులను డాష్‌బోర్డ్‌లో జోడించండి.'
                    : 'Add family members from your dashboard to include them here.'}
                </p>
              ) : (
                <ul className="space-y-2">
                  {familyMembers
                    .filter((m) => !m.is_deceased)
                    .map((m) => (
                      <li key={m.id} className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          id={`participant-${m.id}`}
                          checked={participantIds?.includes(m.id) ?? false}
                          onChange={() => toggleParticipant(m.id)}
                          className="h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
                        />
                        <label htmlFor={`participant-${m.id}`} className="text-gray-800 cursor-pointer">
                          <span className="font-medium">{m.name}</span>
                          <span className="text-gray-500 text-sm"> ({m.relation})</span>
                        </label>
                      </li>
                    ))}
                </ul>
              )}
            </div>

            <div>
              <label htmlFor="sankalpa-intent" className="block text-xs text-gray-600 mb-1">
                {t('sankalpaIntentLabel', sankalpamLanguageCode)}
              </label>
              <select
                id="sankalpa-intent"
                value={sankalpaIntent}
                onChange={(e) => setSankalpaIntent(e.target.value)}
                className="max-w-md w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
              >
                <option value="general">{t('intentGeneral', sankalpamLanguageCode)}</option>
                <option value="health">{t('intentHealth', sankalpamLanguageCode)}</option>
                <option value="wealth">{t('intentWealth', sankalpamLanguageCode)}</option>
                <option value="papam">{t('intentPapam', sankalpamLanguageCode)}</option>
                <option value="business">{t('intentBusiness', sankalpamLanguageCode)}</option>
              </select>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-start gap-4 rounded-xl border border-amber-100 bg-amber-50/60 p-4">
              <div className="text-5xl leading-none select-none" aria-hidden>
                🪷
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <h3 className="font-semibold text-gray-900">{t('gotraNakshatraSection', sankalpamLanguageCode)}</h3>
                  <button
                    type="button"
                    onClick={() => {
                      setShowGotraNakEdit((open) => {
                        const next = !open
                        if (next && user) {
                          setGotraOverride(user.gotram || '')
                          setNakshatraOverride(user.birth_nakshatra || '')
                        }
                        return next
                      })
                    }}
                    className="text-sm text-amber-700 underline hover:text-amber-900"
                  >
                    {t('editRitualDetails', sankalpamLanguageCode)}
                  </button>
                </div>
                {!showGotraNakEdit ? (
                  <p className="text-gray-800 break-words">
                    <span className="font-medium">{user?.gotram || '—'}</span>
                    {user?.birth_nakshatra ? (
                      <span className="text-gray-600"> · {user.birth_nakshatra}</span>
                    ) : null}
                    {user?.birth_rashi ? (
                      <span className="text-gray-600"> · {user.birth_rashi}</span>
                    ) : null}
                  </p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Gotra</label>
                      <input
                        type="text"
                        value={gotraOverride}
                        onChange={(e) => setGotraOverride(e.target.value)}
                        className="w-full rounded-md border-gray-300 shadow-sm text-sm"
                        placeholder={user?.gotram || ''}
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Janma Nakshatra</label>
                      <input
                        type="text"
                        value={nakshatraOverride}
                        onChange={(e) => setNakshatraOverride(e.target.value)}
                        className="w-full rounded-md border-gray-300 shadow-sm text-sm"
                        placeholder={user?.birth_nakshatra || ''}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : null}

        {/* Pooja selection */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-bold mb-2">
            {onlyOnePooja && sankalpamLanguageCode
              ? t('startThePooja', sankalpamLanguageCode)
              : t('selectAPooja', sankalpamLanguageCode)}
          </h2>
          {!(onlyOnePooja && sankalpamLanguageCode) && (
            <p className="text-gray-600 mb-6">
              {t('poojaListDesc', sankalpamLanguageCode)}
            </p>
          )}

          {!sankalpamLanguageCode ? (
            <p className="text-gray-500 text-center py-8">
              {t('selectLangFirst', sankalpamLanguageCode)}
            </p>
          ) : poojas.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              {t('noPoojasForLang', sankalpamLanguageCode)}
            </p>
          ) : (
            <div className="space-y-4">
              {poojas.map((pooja) => (
                <div
                  key={pooja.id}
                  className={`border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer ${
                    selectedPooja?.id === pooja.id ? 'border-amber-600 bg-amber-50' : ''
                  }`}
                  onClick={() => handleSelectPooja(pooja)}
                >
                  <h3 className="font-bold text-lg mb-2">{pooja.name}</h3>
                  {pooja.description && (
                    <p className="text-gray-600 mb-2">{pooja.description}</p>
                  )}
                  {pooja.duration_minutes && (
                    <p className="text-sm text-gray-500">{t('duration', sankalpamLanguageCode)}: {pooja.duration_minutes} {t('minutes', sankalpamLanguageCode)}</p>
                  )}
                  <button type="button" className="mt-3 px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700">
                    {selectedPooja?.id === pooja.id ? t('selected', sankalpamLanguageCode) : t('selectAndStart', sankalpamLanguageCode)}
                  </button>
                </div>
              ))}
              {onlyOnePooja && poojas[0] && (
                <div className="space-y-4 pt-4 mt-4 border-t border-amber-100">
                  <section className="rounded-lg border border-amber-100 bg-amber-50/60 p-4">
                    <h3 className="text-lg font-semibold text-amber-900 mb-2">
                      {t('poojaPreparationTitle', sankalpamLanguageCode)}
                    </h3>
                    <p className="text-gray-700 text-sm leading-relaxed mb-3">
                      {t('poojaPreparationBody', sankalpamLanguageCode)}
                    </p>
                    <Link
                      href={`/pooja-readiness/${getPoojaSlug(poojas[0].name)}`}
                      className="text-sm font-medium text-amber-800 underline hover:text-amber-950"
                    >
                      {t('readinessLinkLabel', sankalpamLanguageCode)}
                    </Link>
                  </section>
                  <section className="rounded-lg border border-amber-100 bg-amber-50/60 p-4">
                    <h3 className="text-lg font-semibold text-amber-900 mb-2">
                      {t('poojaMaterialTitle', sankalpamLanguageCode)}
                    </h3>
                    <p className="text-gray-700 text-sm leading-relaxed mb-3">
                      {t('poojaMaterialBody', sankalpamLanguageCode)}
                    </p>
                    <Link
                      href={`/pooja-items/${getPoojaSlug(poojas[0].name)}`}
                      className="text-sm font-medium text-amber-800 underline hover:text-amber-950"
                    >
                      {t('itemsLinkLabel', sankalpamLanguageCode)}
                    </Link>
                  </section>
                </div>
              )}
            </div>
          )}
        </div>

        {selectedPooja && (
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="mb-4 text-center">
              <h2 className="text-3xl font-bold mb-2">
                {selectedPooja.name} - {t('sankalpam', sankalpamLanguageCode)}
              </h2>
              {sankalpam && (
                <p className="text-gray-600">
                  {t('nearbyRiver', sankalpamLanguageCode)}: {sankalpam.nearby_river}
                </p>
              )}
            </div>

            {sankalpamLoading && (
              <div className="text-center mb-4">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-amber-600 mx-auto"></div>
                <p className="mt-3 text-gray-600">{t('generatingSankalpam', sankalpamLanguageCode)}</p>
              </div>
            )}

            {sankalpam && (
              <>
                <div className="mb-6">
                  {audioUrl && (
                    <audio
                      ref={audioRef}
                      src={audioUrl}
                      preload="auto"
                      onTimeUpdate={() => {
                        if (audioRef.current) setPlaybackCurrentTime(audioRef.current.currentTime)
                      }}
                      onLoadedMetadata={() => {
                        if (audioRef.current && Number.isFinite(audioRef.current.duration)) {
                          setPlaybackDuration(audioRef.current.duration)
                        }
                      }}
                      onEnded={() => {
                        setIsPlaying(false)
                        setPlaybackCurrentTime(0)
                        setCurrentLine(0)
                      }}
                    />
                  )}

                  {/* Progress bar (seekable when audio; visual-only progress when no audio) */}
                  <div className="max-w-2xl mx-auto mb-4">
                    {audioUrl ? (
                      <>
                        <input
                          type="range"
                          min={0}
                          max={playbackDuration || 100}
                          step={0.1}
                          value={playbackCurrentTime}
                          onChange={handleSeek}
                          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-amber-600"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>{formatTime(playbackCurrentTime)}</span>
                          <span>{formatTime(playbackDuration)}</span>
                        </div>
                      </>
                    ) : (
                      lines.length > 0 && (
                        <>
                          <div className="w-full h-2 bg-gray-200 rounded-lg overflow-hidden">
                            <div
                              className="h-full bg-amber-600 transition-all duration-300"
                              style={{ width: `${(currentLine / (lines.length - 1 || 1)) * 100}%` }}
                            />
                          </div>
                          <div className="flex justify-between text-xs text-gray-500 mt-1">
                            <span>{currentLine + 1} / {lines.length}</span>
                          </div>
                        </>
                      )
                    )}
                  </div>

                  {/* Playback controls: Rewind | Play/Pause | Forward */}
                  <div className="flex justify-center items-center gap-3 flex-wrap">
                    <button
                      type="button"
                      onClick={handleRewind}
                      disabled={!sankalpam}
                      className="p-3 rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                      title={t('rewind', sankalpamLanguageCode)}
                    >
                      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M8.445 14.832A1 1 0 0010 14v-2.798l5.445 3.63A1 1 0 0017 15V5a1 1 0 00-1.555-.832L10 7.798V5a1 1 0 00-1.555-.832l-6 4a1 1 0 000 1.664l6 4z" />
                      </svg>
                    </button>

                    {isPlaying ? (
                      <button
                        type="button"
                        onClick={handlePause}
                        className="p-4 rounded-full bg-amber-600 text-white hover:bg-amber-700 text-lg font-medium flex items-center gap-2"
                      >
                        <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        {t('pause', sankalpamLanguageCode)}
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={handlePlay}
                        disabled={!sankalpam}
                        className="p-4 rounded-full bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 text-lg font-medium flex items-center gap-2"
                      >
                        <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                        </svg>
                        {t('playSankalpam', sankalpamLanguageCode)}
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={handleForward}
                      disabled={!sankalpam}
                      className="p-3 rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                      title={t('forward', sankalpamLanguageCode)}
                    >
                      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M4.555 5.168A1 1 0 003 6v8a1 1 0 001.555.832L10 11.202V14a1 1 0 001.555.832l6-4a1 1 0 000-1.664l-6-4A1 1 0 0010 6v2.798l-5.445-3.63z" />
                      </svg>
                    </button>
                  </div>

                  {!audioUrl && (
                    <p className="text-sm text-gray-500 mt-2 text-center">
                      {t('audioUnavailable', sankalpamLanguageCode)}
                    </p>
                  )}
                </div>

                <div className="bg-amber-50 rounded-lg p-6 min-h-[300px] max-h-[600px] overflow-y-auto">
                  <AnimatePresence mode="wait">
                    {sankalpam.sankalpam_text
                      .split('\n')
                      .filter(line => line.trim())
                      .map((line, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{
                            opacity: currentLine === index ? 1 : 0.5,
                            y: 0,
                            scale: currentLine === index ? 1.05 : 1,
                          }}
                          transition={{ duration: 0.5 }}
                          className={`mb-3 text-lg ${
                            currentLine === index
                              ? 'text-amber-900 font-semibold bg-amber-200 p-2 rounded'
                              : 'text-gray-700'
                          }`}
                        >
                          {renderLineWithNameHighlights(line, sankalpam.highlight_names || [])}
                        </motion.div>
                      ))}
                  </AnimatePresence>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

