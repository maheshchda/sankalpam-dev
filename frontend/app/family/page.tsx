'use client'

import { useEffect, useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'react-toastify'
import Link from 'next/link'
import Select from 'react-select'
import { Country, State, City } from 'country-state-city'

const NAKSHATRAS = [
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
]

const RAASIS = [
  'Mesha',
  'Vrishabha',
  'Mithuna',
  'Karka',
  'Simha',
  'Kanya',
  'Tula',
  'Vrischika',
  'Dhanu',
  'Makara',
  'Kumbha',
  'Meena',
]

const PADAS = ['1', '2', '3', '4']

const isGrandRelation = (relation: string) =>
  relation.startsWith('Grand') || relation.startsWith('Great Grand')

const UNIQUE_RELATIONS = new Set([
  'Wife', 'Father', 'Mother',
  'Grand Paternal Father', 'Grand Paternal Mother',
  'Great Grand Paternal Father', 'Great Grand Paternal Mother',
  'Grand Maternal Father', 'Grand Maternal Mother',
  'Great Grand Maternal Father', 'Great Grand Maternal Mother',
])

const RELATIONS = [
  'Wife',
  'Son',
  'Daughter',
  'Grand Son',
  'Grand Daughter',
  'Great Grand Son',
  'Great Grand Daughter',
  'Father',
  'Mother',
  'Grand Paternal Father',
  'Grand Paternal Mother',
  'Great Grand Paternal Father',
  'Great Grand Paternal Mother',
  'Grand Maternal Father',
  'Grand Maternal Mother',
  'Great Grand Maternal Father',
  'Great Grand Maternal Mother',
]

interface FamilyMember {
  id: number
  name: string
  relation: string
  gender: string
  date_of_birth: string | null
  birth_time: string | null
  birth_city: string
  birth_state: string
  birth_country: string
  birth_nakshatra?: string
  birth_rashi?: string
  birth_pada?: string
  is_deceased: boolean
  date_of_death: string | null
  time_of_death: string | null
  death_city: string | null
  death_state: string | null
  death_country: string | null
  death_tithi: string | null
  death_paksha: string | null
  death_nakshatra: string | null
  death_vara: string | null
  death_yoga: string | null
  death_karana: string | null
}

export default function FamilyPage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [members, setMembers] = useState<FamilyMember[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  // Death location cascading dropdown codes
  const [deathCountryCode, setDeathCountryCode] = useState('')
  const [deathStateCode, setDeathStateCode]     = useState('')

  const deathStates = useMemo(
    () => deathCountryCode ? State.getStatesOfCountry(deathCountryCode) : [],
    [deathCountryCode]
  )
  const deathCities = useMemo(
    () => deathCountryCode && deathStateCode
      ? City.getCitiesOfState(deathCountryCode, deathStateCode)
      : deathCountryCode
        ? City.getCitiesOfCountry(deathCountryCode) ?? []
        : [],
    [deathCountryCode, deathStateCode]
  )

  const [formData, setFormData] = useState({
    name: '',
    relation: '',
    gender: 'male',
    date_of_birth: '',
    birth_time: '',
    birth_nakshatra: '',
    birth_rashi: '',
    birth_pada: '',
    birth_city: '',
    birth_state: '',
    birth_country: 'India',
    is_deceased: false,
    date_of_death: '',
    time_of_death: '',
    death_city: '',
    death_state: '',
    death_country: '',
    death_tithi: '',
    death_paksha: '',
    death_nakshatra: '',
    death_vara: '',
    death_yoga: '',
    death_karana: '',
  })

  // Relations already in use (excluding the member currently being edited)
  const usedUniqueRelations = useMemo(() => {
    const used = new Set<string>()
    members.forEach(m => {
      if (UNIQUE_RELATIONS.has(m.relation) && m.id !== editingId) {
        used.add(m.relation)
      }
    })
    return used
  }, [members, editingId])

  useEffect(() => {
    if (!user) {
      router.push('/login')
    } else {
      fetchMembers()
    }
  }, [user, router])

  const fetchMembers = async () => {
    try {
      const response = await api.get('/api/family/members')
      setMembers(response.data)
    } catch (error) {
      console.error('Error fetching family members:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      // Prepare data - convert empty strings to null for optional fields
      const submitData = {
        ...formData,
        date_of_birth: formData.date_of_birth || null,
        birth_time: formData.birth_time || null,
        birth_nakshatra: formData.birth_nakshatra || null,
        birth_rashi: formData.birth_rashi || null,
        birth_pada: formData.birth_pada || null,
        date_of_death:   formData.is_deceased ? (formData.date_of_death   || null) : null,
        time_of_death:   formData.is_deceased ? (formData.time_of_death   || null) : null,
        death_city:      formData.is_deceased ? (formData.death_city      || null) : null,
        death_state:     formData.is_deceased ? (formData.death_state     || null) : null,
        death_country:   formData.is_deceased ? (formData.death_country   || null) : null,
        death_tithi:     formData.is_deceased ? (formData.death_tithi     || null) : null,
        death_paksha:    formData.is_deceased ? (formData.death_paksha    || null) : null,
        death_nakshatra: formData.is_deceased ? (formData.death_nakshatra || null) : null,
        death_vara:      formData.is_deceased ? (formData.death_vara      || null) : null,
        death_yoga:      formData.is_deceased ? (formData.death_yoga      || null) : null,
        death_karana:    formData.is_deceased ? (formData.death_karana    || null) : null,
      }
      
      if (editingId) {
        await api.put(`/api/family/members/${editingId}`, submitData)
        toast.success('Family member updated successfully!')
      } else {
        await api.post('/api/family/members', submitData)
        toast.success('Family member added successfully!')
      }
      setShowForm(false)
      setEditingId(null)
      setDeathCountryCode('')
      setDeathStateCode('')
      setFormData({
        name: '',
        relation: '',
        gender: 'male',
        date_of_birth: '',
        birth_time: '',
        birth_nakshatra: '',
        birth_rashi: '',
        birth_pada: '',
        birth_city: '',
        birth_state: '',
        birth_country: 'India',
        is_deceased: false,
        date_of_death: '',
        time_of_death: '',
        death_city: '',
        death_state: '',
        death_country: '',
        death_tithi: '',
        death_paksha: '',
        death_nakshatra: '',
        death_vara: '',
        death_yoga: '',
        death_karana: '',
      })
      fetchMembers()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to add family member')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this family member?')) return
    
    try {
      await api.delete(`/api/family/members/${id}`)
      toast.success('Family member deleted successfully!')
      fetchMembers()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete family member')
    }
  }

  const startEdit = (member: FamilyMember) => {
    setEditingId(member.id)
    setShowForm(true)

    // Restore death location dropdown codes from stored country/state names
    const dCountry = member.death_country || ''
    const dState   = member.death_state   || ''
    const countryObj = dCountry
      ? Country.getAllCountries().find(c => c.name.toLowerCase() === dCountry.toLowerCase())
      : null
    const countryCode = countryObj?.isoCode ?? ''
    const stateObj = countryCode && dState
      ? State.getStatesOfCountry(countryCode).find(s => s.name.toLowerCase() === dState.toLowerCase())
      : null
    const stateCode = stateObj?.isoCode ?? ''
    setDeathCountryCode(countryCode)
    setDeathStateCode(stateCode)

    setFormData({
      name: member.name,
      relation: member.relation,
      gender: member.gender,
      date_of_birth: member.date_of_birth ? member.date_of_birth.slice(0, 10) : '',
      birth_time: member.birth_time || '',
      birth_nakshatra: member.birth_nakshatra || '',
      birth_rashi: member.birth_rashi || '',
      birth_pada: member.birth_pada || '',
      birth_city: member.birth_city,
      birth_state: member.birth_state,
      birth_country: member.birth_country,
      is_deceased: member.is_deceased || false,
      date_of_death: member.date_of_death ? member.date_of_death.slice(0, 10) : '',
      time_of_death: member.time_of_death || '',
      death_city: member.death_city || '',
      death_state: member.death_state || '',
      death_country: member.death_country || '',
      death_tithi: member.death_tithi || '',
      death_paksha: member.death_paksha || '',
      death_nakshatra: member.death_nakshatra || '',
      death_vara: member.death_vara || '',
      death_yoga: member.death_yoga || '',
      death_karana: member.death_karana || '',
    })
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
        <div className="sacred-card p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="font-cinzel text-2xl font-bold text-sacred-800">Family Members</h2>
            <button
              onClick={() => setShowForm(!showForm)}
              className="gold-btn"
            >
              {showForm ? 'Cancel' : 'Add Family Member'}
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleSubmit} className="mb-6 border-b pb-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Name *</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Relation *</label>
                  <select
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.relation}
                    onChange={(e) => setFormData({ ...formData, relation: e.target.value })}
                  >
                    <option value="">— Select Relation —</option>
                    {RELATIONS.map((r) => {
                      const isDisabled = UNIQUE_RELATIONS.has(r) && usedUniqueRelations.has(r)
                      return (
                        <option key={r} value={r} disabled={isDisabled}>
                          {r}{isDisabled ? ' (already added)' : ''}
                        </option>
                      )
                    })}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Gender *</label>
                  <select
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Date of Birth
                    {isGrandRelation(formData.relation)
                      ? <span className="ml-1 text-xs text-gray-400 font-normal">(optional)</span>
                      : <span className="ml-1 text-red-500">*</span>
                    }
                  </label>
                  <input
                    type="date"
                    required={!isGrandRelation(formData.relation)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.date_of_birth}
                    onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Time of Birth (24hr)
                    {isGrandRelation(formData.relation)
                      ? <span className="ml-1 text-xs text-gray-400 font-normal">(optional)</span>
                      : <span className="ml-1 text-red-500">*</span>
                    }
                  </label>
                  <input
                    type="time"
                    required={!isGrandRelation(formData.relation)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_time}
                    onChange={(e) => setFormData({ ...formData, birth_time: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Janma Nakshatra (Birth Star)</label>
                  <select
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_nakshatra}
                    onChange={(e) => setFormData({ ...formData, birth_nakshatra: e.target.value })}
                  >
                    <option value="">Select Nakshatra (optional)</option>
                    {NAKSHATRAS.map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Janma Raasi (Birth Zodiac Sign)</label>
                  <select
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_rashi}
                    onChange={(e) => setFormData({ ...formData, birth_rashi: e.target.value })}
                  >
                    <option value="">Select Raasi (optional)</option>
                    {RAASIS.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Janma Pada (1–4)</label>
                  <select
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                    value={formData.birth_pada}
                    onChange={(e) => setFormData({ ...formData, birth_pada: e.target.value })}
                  >
                    <option value="">Select Pada (optional)</option>
                    {PADAS.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Birth City *</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.birth_city}
                    onChange={(e) => setFormData({ ...formData, birth_city: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Birth State *</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.birth_state}
                    onChange={(e) => setFormData({ ...formData, birth_state: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Birth Country *</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.birth_country}
                    onChange={(e) => setFormData({ ...formData, birth_country: e.target.value })}
                  />
                </div>
              </div>

              {/* Deceased section */}
              <div className="border-t pt-4 mt-2">
                <label className="flex items-center gap-3 cursor-pointer select-none w-fit">
                  <input
                    type="checkbox"
                    checked={formData.is_deceased}
                    onChange={(e) => {
                      if (!e.target.checked) {
                        setDeathCountryCode('')
                        setDeathStateCode('')
                      }
                      setFormData({
                        ...formData,
                        is_deceased: e.target.checked,
                        date_of_death: '',
                        time_of_death: '',
                        death_city: '',
                        death_state: '',
                        death_country: '',
                      })
                    }}
                    className="h-4 w-4 rounded border-gray-300 accent-amber-600"
                  />
                  <span className="text-sm font-medium text-gray-700">Deceased</span>
                </label>

                {formData.is_deceased && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-4">
                    <p className="text-xs text-gray-500 italic">
                      These details are used to calculate the Nakshatra, Tithi and Vaara of the day of passage for Shraaddha and other rituals.
                    </p>

                    {/* Date & Time of Death */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Date of Death
                          <span className="ml-1 text-xs text-gray-400 font-normal">(optional)</span>
                        </label>
                        <input
                          type="date"
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                          value={formData.date_of_death}
                          max={new Date().toISOString().split('T')[0]}
                          onChange={(e) => setFormData({ ...formData, date_of_death: e.target.value })}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Time of Death (24hr)
                          <span className="ml-1 text-xs text-gray-400 font-normal">(optional)</span>
                        </label>
                        <input
                          type="time"
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500"
                          value={formData.time_of_death}
                          onChange={(e) => setFormData({ ...formData, time_of_death: e.target.value })}
                        />
                      </div>
                    </div>

                    {/* Place of Death — cascading dropdowns */}
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-2">Place of Death</p>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

                        {/* Country */}
                        <div>
                          <label className="block text-xs text-gray-600 mb-1">Country</label>
                          <Select
                            options={Country.getAllCountries().map(c => ({ value: c.isoCode, label: c.name }))}
                            value={deathCountryCode ? { value: deathCountryCode, label: formData.death_country } : null}
                            onChange={(opt) => {
                              const code = opt?.value ?? ''
                              const name = opt?.label ?? ''
                              setDeathCountryCode(code)
                              setDeathStateCode('')
                              setFormData(prev => ({ ...prev, death_country: name, death_state: '', death_city: '' }))
                            }}
                            placeholder="Select Country"
                            isClearable
                            isSearchable
                            classNamePrefix="react-select"
                            styles={{ control: (b) => ({ ...b, fontSize: '0.875rem', minHeight: '36px' }) }}
                          />
                        </div>

                        {/* State */}
                        <div>
                          <label className="block text-xs text-gray-600 mb-1">State / Province</label>
                          <Select
                            options={deathStates.map(s => ({ value: s.isoCode, label: s.name }))}
                            value={deathStateCode ? { value: deathStateCode, label: formData.death_state } : null}
                            onChange={(opt) => {
                              const code = opt?.value ?? ''
                              const name = opt?.label ?? ''
                              setDeathStateCode(code)
                              setFormData(prev => ({ ...prev, death_state: name, death_city: '' }))
                            }}
                            placeholder={deathCountryCode ? 'Select State' : 'Select Country first'}
                            isClearable
                            isSearchable
                            isDisabled={!deathCountryCode}
                            classNamePrefix="react-select"
                            styles={{ control: (b) => ({ ...b, fontSize: '0.875rem', minHeight: '36px' }) }}
                          />
                        </div>

                        {/* City */}
                        <div>
                          <label className="block text-xs text-gray-600 mb-1">City</label>
                          <Select
                            options={deathCities.map(c => ({ value: c.name, label: c.name }))}
                            value={formData.death_city ? { value: formData.death_city, label: formData.death_city } : null}
                            onChange={(opt) => {
                              setFormData(prev => ({ ...prev, death_city: opt?.value ?? '' }))
                            }}
                            placeholder={deathCountryCode ? 'Select City' : 'Select Country first'}
                            isClearable
                            isSearchable
                            isDisabled={!deathCountryCode}
                            classNamePrefix="react-select"
                            styles={{ control: (b) => ({ ...b, fontSize: '0.875rem', minHeight: '36px' }) }}
                          />
                        </div>

                  </div>

                    {/* Vaaram & Moon Calendar Day */}
                    <div className="mt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <p className="text-sm font-medium text-gray-700">Day of Passing (Hindu Calendar)</p>
                        <span className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
                          Auto-filled · editable
                        </span>
                      </div>
                      {!formData.death_vara && !formData.death_tithi && (
                        <p className="text-xs text-gray-400 italic mb-2">
                          Save with a date of death to auto-fill. You can also enter manually.
                        </p>
                      )}
                      <div className="grid grid-cols-2 gap-3 max-w-sm">
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Vaaram (Weekday)</label>
                          <input
                            type="text"
                            placeholder="e.g. Monday"
                            className="block w-full rounded-md border-gray-300 bg-white shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
                            value={formData.death_vara}
                            onChange={(e) => setFormData(prev => ({ ...prev, death_vara: e.target.value }))}
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Moon Calendar Day</label>
                          <input
                            type="text"
                            placeholder="e.g. Ekadashi"
                            className="block w-full rounded-md border-gray-300 bg-white shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
                            value={formData.death_tithi}
                            onChange={(e) => setFormData(prev => ({ ...prev, death_tithi: e.target.value }))}
                          />
                        </div>
                      </div>
                    </div>

                </div>
              </div>
            )}
          </div>

              <button type="submit" className="gold-btn">
                {editingId ? 'Update Member' : 'Add Member'}
              </button>
            </form>
          )}

          <div className="space-y-4">
            {members.length === 0 ? (
              <p className="text-stone-500 text-center py-8">No family members added yet.</p>
            ) : (
              members.map((member) => (
                <div key={member.id} className="border border-cream-300 rounded-lg p-4 flex justify-between items-center bg-cream-50">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-cinzel font-bold text-lg text-sacred-700">{member.name}</h3>
                      {member.is_deceased && (
                        <span className="text-xs bg-stone-200 text-stone-600 px-2 py-0.5 rounded-full font-medium">
                          Deceased
                        </span>
                      )}
                    </div>
                    <p className="text-stone-600 text-sm">{member.relation} • {member.gender}</p>
                    {member.date_of_birth && (
                      <p className="text-sm text-stone-500">
                        Born: {new Date(member.date_of_birth).toLocaleDateString()} in {member.birth_city}, {member.birth_state}
                      </p>
                    )}
                    {member.is_deceased && (
                      <div className="mt-1 space-y-0.5">
                        <p className="text-sm text-stone-400">
                          {member.date_of_death
                            ? <>Died: {new Date(member.date_of_death).toLocaleDateString()}
                                {member.time_of_death && <> at {member.time_of_death}</>}
                                {member.death_city && <> · {[member.death_city, member.death_state, member.death_country].filter(Boolean).join(', ')}</>}
                              </>
                            : member.death_city
                              ? <>Place of death: {[member.death_city, member.death_state, member.death_country].filter(Boolean).join(', ')}</>
                              : null
                          }
                        </p>
                        {(member.death_vara || member.death_tithi) && (
                          <div className="flex gap-x-4 text-xs text-sacred-700 bg-gold-500/10 border border-gold-500/30 rounded px-2 py-1 w-fit mt-1">
                            {member.death_vara  && <span>Vaaram: <b>{member.death_vara}</b></span>}
                            {member.death_tithi && <span>Moon Day: <b>{member.death_tithi}</b></span>}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="space-x-2 shrink-0">
                    <button onClick={() => startEdit(member)} className="px-3 py-1 bg-cream-200 text-sacred-700 rounded hover:bg-cream-300 text-sm border border-cream-300">Edit</button>
                    <button onClick={() => handleDelete(member.id)} className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm">Delete</button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

