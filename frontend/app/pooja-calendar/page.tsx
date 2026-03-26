'use client'

import { useEffect, useMemo, useState, type MouseEvent } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import Link from 'next/link'
import HomeButton from '@/components/HomeButton'
import { getCanonicalPoojaSlug, resolveCalendarRowSlug } from '@/lib/poojaSlugs'

interface CalendarRow {
  pooja_name: string
  freq: string
  cal: string
  local_language: string
  pooja_date?: string
  /** Stable ASCII slug from backend (English key); required when pooja_name is localized script */
  pooja_slug?: string
  /** Some proxies/clients may camelCase */
  poojaSlug?: string
}

const YEARS = [2026, 2027, 2028, 2029, 2030]
const POOJA_TYPES = ['Daily', 'Monthly', 'Yearly']

type LangCode = 'en' | 'hi' | 'te' | 'ta' | 'mr' | 'bn' | 'gu' | 'kn' | 'ml' | 'pa' | 'or' | 'ur' | 'sa' | 'as' | 'kok'

const LANGUAGES: { code: LangCode; label: string; native: string }[] = [
  { code: 'en', label: 'English', native: 'English' },
  { code: 'hi', label: 'Hindi', native: 'हिंदी' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
  { code: 'mr', label: 'Marathi', native: 'मराठी' },
  { code: 'bn', label: 'Bengali', native: 'বাংলা' },
  { code: 'gu', label: 'Gujarati', native: 'ગુજરાતી' },
  { code: 'kn', label: 'Kannada', native: 'ಕನ್ನಡ' },
  { code: 'ml', label: 'Malayalam', native: 'മലയാളം' },
  { code: 'pa', label: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
  { code: 'or', label: 'Odia', native: 'ଓଡ଼ିଆ' },
  { code: 'ur', label: 'Urdu', native: 'اردو' },
  { code: 'sa', label: 'Sanskrit', native: 'संस्कृतम्' },
  { code: 'as', label: 'Assamese', native: 'অসমীয়া' },
  { code: 'kok', label: 'Konkani', native: 'कोंकणी' },
]

/** English UI + these states → gate "Open Pooja" by Telugu template availability */
const TELUGU_NATIVE_STATES = new Set<string>(['Telangana', 'Andhra Pradesh'])

const STATE_LOCAL_LANGUAGE: Record<string, LangCode> = {
  'Andhra Pradesh': 'te',
  Assam: 'as',
  Bihar: 'hi',
  Chhattisgarh: 'hi',
  Delhi: 'hi',
  Goa: 'kok',
  Gujarat: 'gu',
  Haryana: 'hi',
  'Himachal Pradesh': 'hi',
  Jharkhand: 'hi',
  Karnataka: 'kn',
  Kerala: 'ml',
  'Madhya Pradesh': 'hi',
  Maharashtra: 'mr',
  Odisha: 'or',
  Punjab: 'pa',
  Rajasthan: 'hi',
  'Tamil Nadu': 'ta',
  Telangana: 'te',
  Tripura: 'bn',
  'Uttar Pradesh': 'hi',
  Uttarakhand: 'hi',
  'West Bengal': 'bn',
}

const COUNTRY_OPTIONS = ['India', 'United States', 'Canada', 'United Kingdom', 'Australia']

const T: Record<string, Partial<Record<LangCode, string>>> = {
  pageTitle: { en: 'Pooja Calendar', hi: 'पूजा कैलेंडर', te: 'పూజ క్యాలెండర్', ta: 'பூஜை நாள்காட்டி', mr: 'पूजा कॅलेंडर', bn: 'পূজা ক্যালেন্ডার', gu: 'પૂજા કેલેન્ડર', kn: 'ಪೂಜಾ ಕ್ಯಾಲೆಂಡರ್', ml: 'പൂജ കലണ്ടർ', pa: 'ਪੂਜਾ ਕੈਲੰਡਰ', or: 'ପୂଜା କ୍ୟାଲେଣ୍ଡର', ur: 'پوجا کیلنڈر', sa: 'पूजाकालदर्शिका' },
  country: { en: 'Current Location (Country)', hi: 'वर्तमान स्थान (देश)', te: 'ప్రస్తుత స్థానం (దేశం)', ta: 'தற்போதைய இடம் (நாடு)', mr: 'सध्याचे स्थान (देश)', bn: 'বর্তমান অবস্থান (দেশ)', gu: 'હાલનું સ્થાન (દેશ)', kn: 'ಪ್ರಸ್ತುತ ಸ್ಥಳ (ದೇಶ)', ml: 'നിലവിലെ സ്ഥലം (രാജ്യം)', pa: 'ਮੌਜੂਦਾ ਟਿਕਾਣਾ (ਦੇਸ਼)', or: 'ବର୍ତ୍ତମାନ ଅବସ୍ଥାନ (ଦେଶ)', ur: 'موجودہ مقام (ملک)', sa: 'वर्तमानस्थानम् (देशः)' },
  state: { en: 'Native State', hi: 'मूल राज्य', te: 'స్వస్థల రాష్ట్రం', ta: 'சொந்த மாநிலம்', mr: 'मूळ राज्य', bn: 'নিজ রাজ্য', gu: 'મૂળ રાજ્ય', kn: 'ಸ್ವಂತ ರಾಜ್ಯ', ml: 'സ്വദേശ സംസ്ഥാനം', pa: 'ਮੂਲ ਰਾਜ', or: 'ମୂଳ ରାଜ୍ୟ', ur: 'آبائی ریاست', sa: 'मूलराज्यम्' },
  year: { en: 'Year of Pooja', hi: 'पूजा का वर्ष', te: 'పూజ సంవత్సరం', ta: 'பூஜை ஆண்டு', mr: 'पूजेचे वर्ष', bn: 'পূজার বছর', gu: 'પૂજાનું વર્ષ', kn: 'ಪೂಜೆಯ ವರ್ಷ', ml: 'പൂജാ വർഷം', pa: 'ਪੂਜਾ ਦਾ ਸਾਲ', or: 'ପୂଜାର ବର୍ଷ', ur: 'پوجا کا سال', sa: 'पूजावर्षम्' },
  typeOfPooja: { en: 'Type of Pooja', hi: 'पूजा का प्रकार', te: 'పూజ రకం', ta: 'பூஜை வகை', mr: 'पूजेचा प्रकार', bn: 'পূজার ধরন', gu: 'પૂજાનો પ્રકાર', kn: 'ಪೂಜಾ ಪ್ರಕಾರ', ml: 'പൂജയുടെ തരം', pa: 'ਪੂਜਾ ਦੀ ਕਿਸਮ', or: 'ପୂଜାର ପ୍ରକାର', ur: 'پوجا کی قسم', sa: 'पूजाप्रकारः' },
  selectState: { en: 'Select state', hi: 'राज्य चुनें', te: 'రాష్ట్రం ఎంచుకోండి', ta: 'மாநிலம் தேர்ந்தெடு', mr: 'राज्य निवडा', bn: 'রাজ্য নির্বাচন করুন', gu: 'રાજ્ય પસંદ કરો', kn: 'ರಾಜ್ಯ ಆಯ್ಕೆಮಾಡಿ', ml: 'സംസ്ഥാനം തിരഞ്ഞെടുക്കുക', pa: 'ਰਾਜ ਚੁਣੋ', or: 'ରାଜ୍ୟ ବାଛନ୍ତୁ', ur: 'ریاست منتخب کریں', sa: 'राज्यं चिनुत' },
  allYears: { en: 'All years', hi: 'सभी वर्ष', te: 'అన్ని సంవత్సరాలు', ta: 'அனைத்து ஆண்டுகள்', mr: 'सर्व वर्षे', bn: 'সমস্ত বছর', gu: 'બધાં વર્ષો', kn: 'ಎಲ್ಲಾ ವರ್ಷಗಳು', ml: 'എല്ലാ വർഷങ്ങളും', pa: 'ਸਾਰੇ ਸਾਲ', or: 'ସମସ୍ତ ବର୍ଷ', ur: 'تمام سالیں', sa: 'सर्वाणि वर्षाणि' },
  allTypes: { en: 'All types', hi: 'सभी प्रकार', te: 'అన్ని రకాలు', ta: 'அனைத்து வகைகள்', mr: 'सर्व प्रकार', bn: 'সমস্ত ধরন', gu: 'બધા પ્રકારો', kn: 'ಎಲ್ಲಾ ಪ್ರಕಾರಗಳು', ml: 'എല്ലാ തരങ്ങളും', pa: 'ਸਾਰੀਆਂ ਕਿਸਮਾਂ', or: 'ସମସ୍ତ ପ୍ରକାର', ur: 'تمام اقسام', sa: 'सर्वाणि प्रकाराणि' },
  language: { en: 'Language', hi: 'भाषा', te: 'భాష', ta: 'மொழி', mr: 'भाषा', bn: 'ভাষা', gu: 'ભાષા', kn: 'ಭಾಷೆ', ml: 'ഭാഷ', pa: 'ਭਾਸ਼ਾ', or: 'ଭାଷା', ur: 'زبان', sa: 'भाषा' },
  selectLanguage: { en: 'Select language', hi: 'भाषा चुनें', te: 'భాష ఎంచుకోండి', ta: 'மொழியைத் தேர்ந்தெடு', mr: 'भाषा निवडा', bn: 'ভাষা নির্বাচন করুন', gu: 'ભાષા પસંદ કરો', kn: 'ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ', ml: 'ഭാഷ തിരഞ്ഞെടുക്കുക', pa: 'ਭਾਸ਼ਾ ਚੁਣੋ', or: 'ଭାଷା ବାଛନ୍ତୁ', ur: 'زبان منتخب کریں', sa: 'भाषां चिनुत' },
  poojaName: { en: 'Pooja Name', hi: 'पूजा का नाम', te: 'పూజ పేరు', ta: 'பூஜை பெயர்', mr: 'पूजेचे नाव', bn: 'পূজার নাম', gu: 'પૂજાનું નામ', kn: 'ಪೂಜಾ ಹೆಸರು', ml: 'പൂജയുടെ പേര്', pa: 'ਪੂਜਾ ਦਾ ਨਾਮ', or: 'ପୂଜାର ନାମ', ur: 'پوجا کا نام', sa: 'पूजानाम' },
  poojaDate: { en: 'Pooja Date', hi: 'पूजा तिथि', te: 'పూజ తేదీ', ta: 'பூஜை தேதி', mr: 'पूजेची तारीख', bn: 'পূজার তারিখ', gu: 'પૂજાની તારીખ', kn: 'ಪೂಜೆಯ ದಿನಾಂಕ', ml: 'പൂജ തീയതി', pa: 'ਪੂਜਾ ਦੀ ਤਾਰੀਖ', or: 'ପୂଜା ତାରିଖ', ur: 'پوجا کی تاریخ', sa: 'पूजातिथिः' },
  freq: { en: 'Freq', hi: 'आवृत्ति', te: 'పౌనఃపున్యం', ta: 'அதிர்வெண்', mr: 'वारंवारता', bn: 'ঘনত্ব', gu: 'આવર્તન', kn: 'ಆವರ್ತನ', ml: 'ആവൃത്തി', pa: 'ਤਰਤੀਬ', or: 'ଆବୃତ୍ତି', ur: 'تعدد', sa: 'आवृत्तिः' },
  cal: { en: 'Cal', hi: 'कैलेंडर', te: 'క్యాలెండర్', ta: 'நாள்காட்டி', mr: 'कॅलेंडर', bn: 'ক্যালেন্ডার', gu: 'કેલેન્ડર', kn: 'ಕ್ಯಾಲೆಂಡರ್', ml: 'കലണ്ടർ', pa: 'ਕੈਲੰਡਰ', or: 'କ୍ୟାଲେଣ୍ଡର', ur: 'کیلنڈر', sa: 'पञ्चाङ्गम्' },
  localLanguage: { en: 'Local Language / Calendar Ref', hi: 'स्थानीय भाषा / कैलेंडर संदर्भ', te: 'స్థానిక భాష / క్యాలెండర్ ప్రస్తావన', ta: 'உள்ளூர் மொழி / நாள்காட்டி குறிப்பு', mr: 'स्थानीय भाषा / कॅलेंडर संदर्भ', bn: 'স্থানীয় ভাষা / ক্যালেন্ডার রেফারেন্স', gu: 'સ્થાનિક ભાષા / કેલેન્ડર સંદર્ભ', kn: 'ಸ್ಥಳೀಯ ಭಾಷೆ / ಕ್ಯಾಲೆಂಡರ್ ಉಲ್ಲೇಖ', ml: 'പ്രാദേശിക ഭാഷ / കലണ്ടർ റഫറൻസ്', pa: 'ਸਥਾਨਕ ਭਾਸ਼ਾ / ਕੈਲੰਡਰ ਰੈਫਰੈਂਸ', or: 'ସ୍ଥାନୀୟ ଭାଷା / କ୍ୟାଲେଣ୍ଡର ରେଫରେନ୍ସ', ur: 'مقامی زبان / کیلنڈر حوالہ', sa: 'देशीयभाषा / पञ्चाङ्गसन्दर्भः' },
  loading: { en: 'Loading...', hi: 'लोड हो रहा है...', te: 'లోడ్ అవుతోంది...', ta: 'ஏற்றுகிறது...', mr: 'लोड होत आहे...', bn: 'লোড হচ্ছে...', gu: 'લોડ થઈ રહ્યું છે...', kn: 'ಲೋಡ್ ಆಗುತ್ತಿದೆ...', ml: 'ലോഡ് ചെയ്യുന്നു...', pa: 'ਲੋਡ ਹੋ ਰਿਹਾ ਹੈ...', or: 'ଲୋଡ୍ ହେଉଛି...', ur: 'لوڈ ہو رہا ہے...', sa: 'आरोप्यते...' },
  noRows: { en: 'No rows for this selection.', hi: 'इस चयन के लिए कोई पंक्ति नहीं।', te: 'ఈ ఎంపికకు వరుసలు లేవు.', ta: 'இந்தத் தேர்வுக்கான வரிசைகள் இல்லை.', mr: 'या निवडीसाठी पंक्ती नाहीत.', bn: 'এই নির্বাচনের জন্য কোন সারি নেই।', gu: 'આ પસંદગી માટે કોઈ પંક્તિ નથી.', kn: 'ಈ ಆಯ್ಕೆಗೆ ಸಾಲುಗಳಿಲ್ಲ.', ml: 'ഈ തിരഞ്ഞെടുപ്പിന് വരികളില്ല.', pa: 'ਇਸ ਚੋਣ ਲਈ ਕੋਈ ਕਤਾਰ ਨਹੀਂ।', or: 'ଏହି ପସନ୍ଦ ପାଇଁ କୌଣସି ଧାଡି ନାହିଁ।', ur: 'اس انتخاب کے لیے کوئی قطاریں نہیں ہیں۔', sa: 'अस्य निवचनस्य पङ्क्तयः न सन्ति।' },
  selectStateToView: { en: 'Select a state to view the calendar.', hi: 'कैलेंडर देखने के लिए राज्य चुनें।', te: 'క్యాలెండర్ చూడటానికి రాష్ట్రం ఎంచుకోండి.', ta: 'நாள்காட்டியைக் காண மாநிலத்தைத் தேர்ந்தெடுக்கவும்.', mr: 'कॅलेंडर पाहण्यासाठी राज्य निवडा.', bn: 'ক্যালেন্ডার দেখতে রাজ্য নির্বাচন করুন।', gu: 'કેલેન્ડર જોવા રાજ્ય પસંદ કરો.', kn: 'ಕ್ಯಾಲೆಂಡರ್ ನೋಡಲು ರಾಜ್ಯ ಆಯ್ಕೆಮಾಡಿ.', ml: 'കലണ്ടർ കാണാൻ സംസ്ഥാനം തിരഞ്ഞെടുക്കുക.', pa: 'ਕੈਲੰਡਰ ਵੇਖਣ ਲਈ ਰਾਜ ਚੁਣੋ।', or: 'କ୍ୟାଲେଣ୍ଡର ଦେଖିବାକୁ ରାଜ୍ୟ ବାଛନ୍ତୁ।', ur: 'کیلنڈر دیکھنے کے لیے ریاست منتخب کریں۔', sa: 'कालदर्शिकां द्रष्टुं राज्यं चिनुत।' },
  sankalpam: { en: 'Sankalpam', hi: 'संकल्पम', te: 'సంకల్పం', ta: 'சங்கல்பம்', mr: 'संकल्प', bn: 'সংকল্পম', gu: 'સંકલ્પમ', kn: 'ಸಂಕಲ್ಪಂ', ml: 'സങ്കല്പം', pa: 'ਸੰਕਲਪਮ', or: 'ସଂକଳ୍ପମ', ur: 'سنکلپم', sa: 'संकल्पम्' },
  welcome: { en: 'Welcome, ', hi: 'स्वागत है, ', te: 'స్వాగతం, ', ta: 'வரவேற்பு, ', mr: 'स्वागत आहे, ', bn: 'স্বাগতম, ', gu: 'સ્વાગત છે, ', kn: 'ಸ್ವಾಗತ, ', ml: 'സ്വാഗതം, ', pa: 'ਜੀ ਆਇਆਂ ਨੂੰ, ', or: 'ସ୍ୱାଗତ, ', ur: 'خوش آمدید، ', sa: 'स्वागतम्, ' },
  dashboard: { en: 'Dashboard', hi: 'डैशबोर्ड', te: 'డాష్‌బోర్డ్', ta: 'டாஷ்போர்டு', mr: 'डॅशबोर्ड', bn: 'ড্যাশবোর্ড', gu: 'ડૅશબોર્ડ', kn: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', ml: 'ഡാഷ്ബോർഡ്', pa: 'ਡੈਸ਼ਬੋਰਡ', or: 'ଡ୍ୟାସବୋର୍ଡ', ur: 'ڈیش بورڈ', sa: 'नियन्त्रणपट्टम्' },
  selectPooja: { en: 'Select Pooja', hi: 'पूजा चुनें', te: 'పూజ ఎంచుకోండి', ta: 'பூஜையைத் தேர்ந்தெடு', mr: 'पूजा निवडा', bn: 'পূজা নির্বাচন করুন', gu: 'પૂજા પસંદ કરો', kn: 'ಪೂಜಾ ಆಯ್ಕೆಮಾಡಿ', ml: 'പൂജ തിരഞ്ഞെടുക്കുക', pa: 'ਪੂਜਾ ਚੁਣੋ', or: 'ପୂଜା ବାଛନ୍ତୁ', ur: 'پوجا منتخب کریں', sa: 'पूजां चिनुत' },
  /** Nav link to /pooja (full list) — not the same as clicking a calendar row */
  browseAllPoojas: { en: 'Browse all poojas', hi: 'सभी पूजा देखें', te: 'అన్ని పూజలను చూడండి', ta: 'அனைத்து பூஜைகளும்', mr: 'सर्व पूजा पहा', bn: 'সব পূজা ব্রাউজ করুন', gu: 'બધી પૂજાઓ જુઓ', kn: 'ಎಲ್ಲಾ ಪೂಜೆಗಳನ್ನು ನೋಡಿ', ml: 'എല്ലാ പൂജകളും', pa: 'ਸਾਰੀਆਂ ਪੂਜਾਵਾਂ', or: 'ସମସ୍ତ ପୂଜା', ur: 'تمام پوجا', sa: 'सर्वाः पूजाः' },
  logout: { en: 'Logout', hi: 'लॉग आउट', te: 'లాగౌట్', ta: 'வெளியேறு', mr: 'लॉग आउट', bn: 'লগ আউট', gu: 'લૉગ આઉટ', kn: 'ಲಾಗ್ ಔಟ್', ml: 'ലോഗ് ഔട്ട്', pa: 'ਲੌਗ ਆਉਟ', or: 'ଲଗ୍ ଆଉଟ୍', ur: 'لاگ آؤٹ', sa: 'बहिर्गमनम्' },
  apiNotFound: { en: 'API not found. Is the backend running?', hi: 'API नहीं मिला। क्या बैकएंड चल रहा है?', te: 'API దొరకలేదు. బ్యాకెండ్ పని చేస్తోందా?', ta: 'API காணப்படவில்லை. பின்னணி இயங்குகிறதா?', mr: 'API आढळली नाही. बॅकएंड चालू आहे का?', bn: 'API পাওয়া যায়নি। ব্যাকএন্ড চলছে কি?', gu: 'API મળ્યો નથી. શું બેકએન્ડ ચાલી રહ્યું છે?', kn: 'API ಸಿಗಲಿಲ್ಲ. ಬ್ಯಾಕ್‌ಎಂಡ್ ಚಾಲನೆಯಲ್ಲಿದೆಯೇ?', ml: 'API കണ്ടെത്തിയില്ല. ബാക്ക്എൻഡ് പ്രവർത്തിക്കുന്നുണ്ടോ?', pa: 'API ਨਹੀਂ ਮਿਲੀ। ਕੀ ਬੈਕਐਂਡ ਚੱਲ ਰਿਹਾ ਹੈ?', or: 'API ମିଳିଲା ନାହିଁ। ବ୍ୟାକଏଣ୍ଡ ଚାଲୁଛି କି?', ur: 'API نہیں ملی۔ کیا بیک اینڈ چل رہا ہے؟', sa: 'API न प्राप्ता। पृष्ठतः प्रचलति वा?' },
  openPooja: { en: 'Open Pooja', hi: 'पूजा खोलें', te: 'పూజ తెరవండి', ta: 'பூஜையைத் திற', mr: 'पूजा उघडा', bn: 'পূজা খুলুন', gu: 'પૂજા ખોલો', kn: 'ಪೂಜೆ ತೆರೆಯಿರಿ', ml: 'പൂജ തുറക്കുക', pa: 'ਪੂਜਾ ਖੋਲੋ', or: 'ପୂଜା ଖୋଲନ୍ତୁ', ur: 'پوجا کھولیں', sa: 'पूजां उद्घाटयतु' },
  comingSoon: { en: 'Coming Soon', hi: 'जल्द आ रहा है', te: 'త్వరలో', ta: 'விரைவில்', mr: 'लवकरच', bn: 'শীঘ্রই আসছে', gu: 'ટૂંક સમયમાં', kn: 'ಶೀಘ್ರದಲ್ಲೇ', ml: 'ഉടൻ വരുന്നു', pa: 'ਜਲਦੀ ਆ ਰਿਹਾ ਹੈ', or: 'ଶୀଘ୍ର ଆସୁଛି', ur: 'جلد آرہا ہے', sa: 'अचिरेण' },
}

function preferredLanguageToCode(preferred: string | undefined): LangCode | '' {
  if (!preferred || !preferred.trim()) return ''
  const s = preferred.trim().toLowerCase()
  const validCodes: LangCode[] = ['en', 'hi', 'te', 'ta', 'mr', 'bn', 'gu', 'kn', 'ml', 'pa', 'or', 'ur', 'sa', 'as', 'kok']
  if (validCodes.includes(s as LangCode)) return s as LangCode
  const nameToCode: Record<string, LangCode> = {
    english: 'en',
    hindi: 'hi',
    telugu: 'te',
    tamil: 'ta',
    marathi: 'mr',
    bengali: 'bn',
    gujarati: 'gu',
    kannada: 'kn',
    malayalam: 'ml',
    punjabi: 'pa',
    odia: 'or',
    oriya: 'or',
    urdu: 'ur',
    sanskrit: 'sa',
    assamese: 'as',
    konkani: 'kok',
    kokani: 'kok',
  }
  return nameToCode[s] ?? ''
}

function getAllowedLanguageCodesForState(state: string): LangCode[] {
  if (!state) return LANGUAGES.map((l) => l.code)
  const local = STATE_LOCAL_LANGUAGE[state]
  if (!local || local === 'en') return ['en']
  return ['en', local]
}

function normalizeCountry(country: string | undefined): string {
  const c = (country || '').trim().toLowerCase()
  if (!c) return 'India'
  if (c === 'india') return 'India'
  if (c === 'usa' || c === 'us' || c === 'united states' || c === 'united states of america') return 'United States'
  if (c === 'uk' || c === 'united kingdom' || c === 'great britain') return 'United Kingdom'
  if (c === 'canada') return 'Canada'
  if (c === 'australia') return 'Australia'
  return country?.trim() || 'India'
}

function t(key: keyof typeof T, lang: LangCode): string {
  const val = T[key]?.[lang] ?? T[key]?.en
  return val ?? String(key)
}

/**
 * Language code used to filter poojas by sankalpam template availability (same as /api/pooja/list).
 * — Any non-English calendar language → gate by that language.
 * — English + Telangana / Andhra Pradesh → gate by Telugu (te), per regional expectation.
 */
function templateLanguageForCalendarAvailability(lang: LangCode, state: string): LangCode | null {
  if (lang !== 'en') return lang
  if (TELUGU_NATIVE_STATES.has(state)) return 'te'
  return null
}

function getLinkedPoojaPath(row: CalendarRow): string {
  const slug = resolveCalendarRowSlug(row)
  if (!slug) {
    return '/pooja'
  }
  return `/pooja/${encodeURIComponent(slug)}`
}

type PoojaAvailabilityState =
  | { kind: 'off' }
  | { kind: 'loading' }
  | { kind: 'ready'; slugs: Set<string> }
  | { kind: 'error' }

function isCalendarOpenPoojaEnabled(row: CalendarRow, availability: PoojaAvailabilityState): boolean {
  if (availability.kind === 'off' || availability.kind === 'error') {
    return true
  }
  if (availability.kind === 'loading') {
    return false
  }
  const slug = resolveCalendarRowSlug(row)
  if (!slug) return false
  return availability.slugs.has(getCanonicalPoojaSlug(slug))
}

export default function PoojaCalendarPage() {
  const { user, loading: authLoading, logout } = useAuth()
  const router = useRouter()
  const [country, setCountry] = useState('India')
  const [states, setStates] = useState<string[]>([])
  const [state, setState] = useState('')
  const [year, setYear] = useState<number | ''>('')
  const [poojaType, setPoojaType] = useState('')
  const [rows, setRows] = useState<CalendarRow[]>([])
  const [loadingStates, setLoadingStates] = useState(true)
  const [loadingData, setLoadingData] = useState(false)
  const [statesError, setStatesError] = useState<string | null>(null)
  const [lang, setLang] = useState<LangCode>('en')
  const [langInitialized, setLangInitialized] = useState(false)
  const [poojaAvailability, setPoojaAvailability] = useState<PoojaAvailabilityState>({ kind: 'off' })
  const allowedLanguageCodes = getAllowedLanguageCodesForState(state)
  const availableLanguages = LANGUAGES.filter((l) => allowedLanguageCodes.includes(l.code))
  const templateLangForGate = useMemo(
    () => templateLanguageForCalendarAvailability(lang, state),
    [lang, state],
  )

  useEffect(() => {
    if (authLoading || langInitialized) return
    if (user) {
      const fromProfile = preferredLanguageToCode(user.preferred_language)
      if (fromProfile) setLang(fromProfile)
      setCountry(normalizeCountry(user.current_country || user.birth_country))
    } else {
      setCountry('India')
      setLang('en')
    }
    setLangInitialized(true)
  }, [authLoading, user, langInitialized])

  useEffect(() => {
    if (!allowedLanguageCodes.includes(lang)) {
      const profileLang = preferredLanguageToCode(user?.preferred_language)
      if (profileLang && allowedLanguageCodes.includes(profileLang)) {
        setLang(profileLang)
      } else {
        setLang(allowedLanguageCodes[1] || allowedLanguageCodes[0] || 'en')
      }
    }
  }, [state, lang, user, allowedLanguageCodes])

  useEffect(() => {
    if (authLoading) return
    setStatesError(null)
    api.get<{ states: string[] }>('/api/pooja-calendar/states')
      .then((res) => {
        const list = res.data?.states ?? []
        setStates(list)
        if (list.length && !state) setState(list[0])
      })
      .catch((err) => {
        setStates([])
        const msg = err.response?.status === 404
          ? t('apiNotFound', lang)
          : err.response?.data?.detail ?? err.message ?? 'Failed to load states'
        setStatesError(String(msg))
      })
      .finally(() => setLoadingStates(false))
  }, [authLoading])

  useEffect(() => {
    if (!state) {
      setRows([])
      return
    }
    setLoadingData(true)
    const params = new URLSearchParams({ state })
    if (year !== '') params.set('year', String(year))
    if (poojaType) params.set('type', poojaType)
    if (lang) params.set('language_code', lang)
    if (country) params.set('country', country)
    api.get<{ rows: CalendarRow[] }>(`/api/pooja-calendar/data?${params}`)
      .then((res) => setRows(res.data.rows || []))
      .catch(() => setRows([]))
      .finally(() => setLoadingData(false))
  }, [state, year, poojaType, lang, country])

  useEffect(() => {
    if (!user || !templateLangForGate) {
      setPoojaAvailability({ kind: 'off' })
      return
    }
    let cancelled = false
    setPoojaAvailability({ kind: 'loading' })
    api
      .get<{ name: string }[]>('/api/pooja/list', { params: { language_code: templateLangForGate } })
      .then((res) => {
        if (cancelled) return
        const list = Array.isArray(res.data) ? res.data : []
        const slugs = new Set(list.map((p) => getCanonicalPoojaSlug(p.name)))
        setPoojaAvailability({ kind: 'ready', slugs })
      })
      .catch(() => {
        if (!cancelled) setPoojaAvailability({ kind: 'error' })
      })
    return () => {
      cancelled = true
    }
  }, [user, templateLangForGate])

  if (authLoading) {
    return <div className="min-h-screen flex items-center justify-center">{t('loading', lang)}</div>
  }

  return (
    <div className="page-bg">
      <nav className="sacred-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:h-16 items-stretch sm:items-center gap-3 sm:gap-3 py-3 sm:py-0">
            <h1 className="font-cinzel text-xl font-bold text-gold-400 truncate">{t('sankalpam', lang)}</h1>
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 justify-end">
              <HomeButton />
              {user ? (
                <>
                  <span className="text-cream-300/70 text-sm hidden sm:inline">{t('welcome', lang)}<span className="text-gold-400 font-medium">{user.first_name}</span>!</span>
                  <Link href="/dashboard" className="btn-glossy btn-glossy-purple">{t('dashboard', lang)}</Link>
                  <Link href="/pooja" className="gold-btn" title={t('browseAllPoojas', lang)}>
                    {t('browseAllPoojas', lang)}
                  </Link>
                  <button onClick={() => { logout(); router.push('/login') }} className="btn-glossy btn-glossy-red">{t('logout', lang)}</button>
                </>
              ) : (
                <Link href="/login" className="gold-btn text-sm py-1.5">Login</Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="font-cinzel text-2xl font-bold text-sacred-800 mb-6">{t('pageTitle', lang)}</h2>

        <div className="sacred-card p-4 mb-6 flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-sacred-700 mb-1">{t('country', lang)}</label>
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="border border-cream-300 rounded-md px-3 py-2 min-w-[200px] bg-white text-stone-800 focus:border-gold-500 focus:ring-1 focus:ring-gold-500"
            >
              {Array.from(new Set([...COUNTRY_OPTIONS, country])).map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-sacred-700 mb-1">{t('state', lang)}</label>
            <select
              value={state}
              onChange={(e) => setState(e.target.value)}
              disabled={loadingStates}
              className="border border-cream-300 rounded-md px-3 py-2 min-w-[180px] bg-white text-stone-800 focus:border-gold-500 focus:ring-1 focus:ring-gold-500"
            >
              <option value="">{t('selectState', lang)}</option>
              {states.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            {statesError && (
              <p className="mt-1 text-sm text-red-600">{statesError}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-sacred-700 mb-1">{t('year', lang)}</label>
            <select
              value={year}
              onChange={(e) => setYear(e.target.value === '' ? '' : Number(e.target.value))}
              className="border border-cream-300 rounded-md px-3 py-2 min-w-[120px] bg-white text-stone-800 focus:border-gold-500 focus:ring-1 focus:ring-gold-500"
            >
              <option value="">{t('allYears', lang)}</option>
              {YEARS.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-sacred-700 mb-1">{t('typeOfPooja', lang)}</label>
            <select
              value={poojaType}
              onChange={(e) => setPoojaType(e.target.value)}
              className="border border-cream-300 rounded-md px-3 py-2 min-w-[140px] bg-white text-stone-800 focus:border-gold-500 focus:ring-1 focus:ring-gold-500"
            >
              <option value="">{t('allTypes', lang)}</option>
              {POOJA_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-sacred-700 mb-1">{t('language', lang)}</label>
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value as LangCode)}
              className="border border-cream-300 rounded-md px-3 py-2 min-w-[180px] bg-white text-stone-800 focus:border-gold-500 focus:ring-1 focus:ring-gold-500"
            >
              {availableLanguages.map((l) => (
                <option key={l.code} value={l.code}>{l.native}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="sacred-card overflow-hidden">
          {loadingData ? (
            <div className="p-8 text-center text-stone-500">{t('loading', lang)}</div>
          ) : rows.length === 0 ? (
            <div className="p-8 text-center text-stone-500">
              {state ? t('noRows', lang) : t('selectStateToView', lang)}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-cream-300">
                <thead className="bg-sacred-800">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-cinzel font-semibold text-gold-400 uppercase">{t('poojaName', lang)}</th>
                    <th className="px-4 py-3 text-left text-xs font-cinzel font-semibold text-gold-400 uppercase">{t('freq', lang)}</th>
                    {poojaType === 'Yearly' && (
                      <th className="px-4 py-3 text-left text-xs font-cinzel font-semibold text-gold-400 uppercase">{t('poojaDate', lang)}</th>
                    )}
                    <th className="px-4 py-3 text-left text-xs font-cinzel font-semibold text-gold-400 uppercase">{t('localLanguage', lang)}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cream-200">
                  {rows.map((row, i) => {
                    const poojaPath = getLinkedPoojaPath(row)
                    const rowSlug = resolveCalendarRowSlug(row)
                    const stopRowNav = (e: MouseEvent) => e.stopPropagation()
                    const openEnabled = isCalendarOpenPoojaEnabled(row, poojaAvailability)
                    return (
                    <tr
                      key={i}
                      className={
                        openEnabled
                          ? 'hover:bg-cream-200/50 cursor-pointer'
                          : 'hover:bg-cream-200/40 cursor-default'
                      }
                      onClick={() => {
                        if (openEnabled) router.push(poojaPath)
                      }}
                      title={poojaPath}
                    >
                      <td className="px-4 py-3 text-sm text-stone-800">
                        <div className="flex items-center flex-wrap gap-2">
                          {openEnabled ? (
                            <Link href={poojaPath} onClick={stopRowNav} className="gold-link font-medium underline">
                              {row.pooja_name}
                            </Link>
                          ) : (
                            <span className="font-medium text-stone-500">{row.pooja_name}</span>
                          )}
                          {openEnabled ? (
                            <Link
                              href={poojaPath}
                              onClick={stopRowNav}
                              className="px-2 py-1 text-xs bg-gold-600 text-sacred-900 rounded hover:bg-gold-500 font-semibold"
                            >
                              {t('openPooja', lang)}
                            </Link>
                          ) : (
                            <span
                              className="px-2 py-1 text-xs rounded font-semibold bg-stone-200 text-stone-500 cursor-not-allowed select-none"
                              aria-disabled
                            >
                              {t('comingSoon', lang)}
                            </span>
                          )}
                          <Link
                            href={
                              rowSlug ? `/pooja-readiness/${encodeURIComponent(rowSlug)}` : '#'
                            }
                            onClick={stopRowNav}
                            className={`px-2 py-1 text-xs rounded ${
                              rowSlug
                                ? 'bg-sacred-700 text-cream-100 hover:bg-sacred-600'
                                : 'bg-stone-300 text-stone-500 pointer-events-none cursor-not-allowed'
                            }`}
                            aria-disabled={!rowSlug}
                          >
                            Readiness Info
                          </Link>
                          <Link
                            href={rowSlug ? `/pooja-items/${encodeURIComponent(rowSlug)}` : '#'}
                            onClick={stopRowNav}
                            className={`px-2 py-1 text-xs rounded ${
                              rowSlug
                                ? 'bg-sacred-600 text-cream-100 hover:bg-sacred-500'
                                : 'bg-stone-300 text-stone-500 pointer-events-none cursor-not-allowed'
                            }`}
                            aria-disabled={!rowSlug}
                          >
                            Items List
                          </Link>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-stone-600">{row.freq}</td>
                      {poojaType === 'Yearly' && (
                        <td className="px-4 py-3 text-sm text-stone-600">{row.pooja_date || '-'}</td>
                      )}
                      <td className="px-4 py-3 text-sm text-stone-600">{row.local_language}</td>
                    </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
