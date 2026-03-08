'use client'

import { useMemo } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────

interface Member {
  id: number
  name: string
  last_name?: string
  relation: string
  gender: string
  unique_id?: string
  date_of_birth?: string | null
  is_deceased?: boolean
}

interface CurrentUser {
  first_name: string
  last_name?: string
  unique_id?: string
}

interface FamilyTreeProps {
  members: Member[]
  currentUser: CurrentUser
}

// ─── Generation config ────────────────────────────────────────────────────────

// Maps each relation to a numeric generation level
// Negative = ancestors, 0 = same generation as user, Positive = descendants
const RELATION_GEN: Record<string, number> = {
  'Great Grand Paternal Father':  -4,
  'Great Grand Paternal Mother':  -4,
  'Great Grand Maternal Father':  -4,
  'Great Grand Maternal Mother':  -4,
  'Grand Paternal Father':        -3,
  'Grand Paternal Mother':        -3,
  'Grand Maternal Father':        -3,
  'Grand Maternal Mother':        -3,
  Father:  -2,
  Mother:  -2,
  Brother:  0,
  Sister:   0,
  Wife:     0,
  Son:      1,
  Daughter: 1,
  'Grand Son':       2,
  'Grand Daughter':  2,
  'Great Grand Son':      3,
  'Great Grand Daughter': 3,
}

// Display order within a generation row
const RELATION_SORT: Record<string, number> = {
  'Great Grand Paternal Father': 0,
  'Great Grand Paternal Mother': 1,
  'Great Grand Maternal Father': 2,
  'Great Grand Maternal Mother': 3,
  'Grand Paternal Father': 0,
  'Grand Paternal Mother': 1,
  'Grand Maternal Father': 2,
  'Grand Maternal Mother': 3,
  Father:  0,
  Mother:  1,
  Brother: 0,
  Sister:  1,
  Wife:    99, // wife renders after the YOU card
  Son:     0,
  Daughter:1,
  'Grand Son':      0,
  'Grand Daughter': 1,
  'Great Grand Son':      0,
  'Great Grand Daughter': 1,
}

const GEN_LABEL: Record<number, string> = {
  '-4': 'Great-Great Grandparents',
  '-3': 'Great Grandparents',
  '-2': 'Grandparents',
  '-1': 'Parents',        // unused tier — kept for completeness
   '0': 'You & Siblings',
   '1': 'Children',
   '2': 'Grandchildren',
   '3': 'Great Grandchildren',
}

// ─── Small helpers ────────────────────────────────────────────────────────────

const genderIcon = (gender: string) =>
  gender === 'female' ? '♀' : gender === 'male' ? '♂' : '⚧'

const genderBg = (gender: string) =>
  gender === 'female'
    ? 'bg-rose-50 border-rose-300 text-rose-700'
    : gender === 'male'
    ? 'bg-sky-50 border-sky-300 text-sky-700'
    : 'bg-gray-50 border-gray-300 text-gray-700'

function fullName(m: { name: string; last_name?: string }) {
  return [m.name, m.last_name].filter(Boolean).join(' ')
}

// ─── Node card ────────────────────────────────────────────────────────────────

interface NodeProps {
  name: string
  last_name?: string
  relation: string
  gender: string
  isYou?: boolean
  isDeceased?: boolean
  uniqueId?: string
}

function TreeNode({ name, last_name, relation, gender, isYou, isDeceased, uniqueId }: NodeProps) {
  const base = isYou
    ? 'bg-sacred-800 border-gold-500 text-white shadow-lg ring-2 ring-gold-400'
    : isDeceased
    ? 'bg-stone-100 border-stone-300 text-stone-500 opacity-75'
    : genderBg(gender) + ' shadow-sm'

  return (
    <div className={`relative flex flex-col items-center rounded-xl border-2 px-3 py-2 min-w-[90px] max-w-[120px] transition-all ${base}`}>
      {/* Avatar circle */}
      <div className={`w-9 h-9 rounded-full flex items-center justify-center text-lg mb-1 font-bold
        ${isYou ? 'bg-gold-500 text-sacred-900' : isDeceased ? 'bg-stone-300 text-stone-500' : 'bg-white/60'}`}>
        {genderIcon(gender)}
      </div>

      {/* Name */}
      <p className={`text-xs font-semibold text-center leading-tight ${isYou ? 'text-gold-300' : ''}`}>
        {fullName({ name, last_name })}
      </p>

      {/* Relation badge */}
      <span className={`mt-1 text-[10px] px-1.5 py-0.5 rounded-full font-medium
        ${isYou ? 'bg-gold-500/20 text-gold-300' : 'bg-white/50 text-current opacity-80'}`}>
        {isYou ? 'You' : relation}
      </span>

      {/* Deceased marker */}
      {isDeceased && (
        <span className="absolute -top-2 -right-2 text-[10px] bg-stone-400 text-white rounded-full px-1">✝</span>
      )}
    </div>
  )
}

// ─── Connector row ────────────────────────────────────────────────────────────
// Renders a centered vertical line between two generation rows.

function Connector({ count }: { count: number }) {
  if (count === 0) return null
  return (
    <div className="flex justify-center py-0">
      <div className="w-px h-6 bg-gold-500/60" />
    </div>
  )
}

// ─── Generation row ───────────────────────────────────────────────────────────

function GenRow({
  label,
  nodes,
  currentUser,
  isUserGen,
}: {
  label: string
  nodes: (NodeProps & { key: string })[]
  currentUser: CurrentUser
  isUserGen: boolean
}) {
  const siblings = nodes.filter(n => n.relation === 'Brother' || n.relation === 'Sister')
  const wife     = nodes.find(n => n.relation === 'Wife')

  return (
    <div>
      {/* Generation label */}
      <div className="flex items-center gap-2 mb-2">
        <div className="h-px flex-1 bg-gold-500/20" />
        <span className="text-[11px] font-semibold text-gold-600 uppercase tracking-widest px-2">
          {label}
        </span>
        <div className="h-px flex-1 bg-gold-500/20" />
      </div>

      {/* Node row */}
      <div className="flex flex-wrap justify-center gap-3 px-2">
        {isUserGen ? (
          <>
            {/* Siblings (left side) */}
            {siblings.map(n => (
              <TreeNode key={n.key} {...n} />
            ))}

            {/* YOU card */}
            <TreeNode
              key="you"
              name={currentUser.first_name}
              last_name={currentUser.last_name}
              relation="You"
              gender="male"
              isYou
              uniqueId={currentUser.unique_id}
            />

            {/* Wife (right side) */}
            {wife && <TreeNode key={wife.key} {...wife} />}
          </>
        ) : (
          nodes.map(n => <TreeNode key={n.key} {...n} />)
        )}
      </div>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function FamilyTree({ members, currentUser }: FamilyTreeProps) {
  // Group members by generation
  const byGen = useMemo(() => {
    const map = new Map<number, Member[]>()
    for (const m of members) {
      const gen = RELATION_GEN[m.relation]
      if (gen === undefined) continue
      if (!map.has(gen)) map.set(gen, [])
      map.get(gen)!.push(m)
    }
    // Sort each generation by RELATION_SORT
    for (const [, list] of map) {
      list.sort((a, b) => (RELATION_SORT[a.relation] ?? 50) - (RELATION_SORT[b.relation] ?? 50))
    }
    return map
  }, [members])

  // Determine which generations exist (always include tier 0 for the user)
  const existingGens = useMemo(() => {
    const gens = new Set([...byGen.keys(), 0])
    return Array.from(gens).sort((a, b) => a - b)
  }, [byGen])

  if (members.length === 0) {
    return (
      <div className="sacred-card p-6 mb-6 text-center">
        <p className="text-stone-400 text-sm">Add family members below to see your family tree.</p>
      </div>
    )
  }

  return (
    <div className="sacred-card p-6 mb-6 overflow-x-auto">
      <h3 className="font-cinzel text-xl font-bold text-sacred-800 mb-5 text-center">Family Tree</h3>

      <div className="min-w-[320px] flex flex-col gap-1">
        {existingGens.map((gen, idx) => {
          const membersInGen = byGen.get(gen) ?? []
          const nodes: (NodeProps & { key: string })[] = membersInGen.map(m => ({
            key: `${m.id}`,
            name: m.name,
            last_name: m.last_name,
            relation: m.relation,
            gender: m.gender,
            isDeceased: m.is_deceased,
            uniqueId: m.unique_id,
          }))

          const label = GEN_LABEL[String(gen)] ?? `Generation ${gen}`
          const isUserGen = gen === 0

          return (
            <div key={gen}>
              {/* Connector between generations */}
              {idx > 0 && <Connector count={membersInGen.length + (isUserGen ? 1 : 0)} />}

              <GenRow
                label={label}
                nodes={nodes}
                currentUser={currentUser}
                isUserGen={isUserGen}
              />
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-3 mt-5 pt-4 border-t border-cream-300">
        <span className="flex items-center gap-1 text-[11px] text-stone-500">
          <span className="inline-block w-3 h-3 rounded-full bg-sky-200 border border-sky-400" /> Male
        </span>
        <span className="flex items-center gap-1 text-[11px] text-stone-500">
          <span className="inline-block w-3 h-3 rounded-full bg-rose-200 border border-rose-400" /> Female
        </span>
        <span className="flex items-center gap-1 text-[11px] text-stone-500">
          <span className="inline-block w-3 h-3 rounded-full bg-stone-200 border border-stone-400" /> Deceased ✝
        </span>
        <span className="flex items-center gap-1 text-[11px] text-stone-500">
          <span className="inline-block w-3 h-3 rounded-full bg-gold-500" /> You
        </span>
      </div>
    </div>
  )
}
