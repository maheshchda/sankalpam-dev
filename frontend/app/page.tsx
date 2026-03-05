'use client'

/* eslint-disable @next/next/no-img-element */
import Link from 'next/link'
import { useEffect, useState } from 'react'

type DeityCard = {
  name: string
  image: string
}

const DEITY_CARDS: DeityCard[] = [
  { name: 'Ganesha', image: '/images/deities/ganesha.svg' },
  { name: 'Lakshmi', image: '/images/deities/lakshmi.svg' },
  { name: 'Saraswati', image: '/images/deities/saraswati.svg' },
  { name: 'Shiva', image: '/images/deities/shiva.svg' },
  { name: 'Durga', image: '/images/deities/durga.svg' },
  { name: 'Venkateswara', image: '/images/deities/venkateswara.svg' },
  { name: 'Subramanya', image: '/images/deities/subramanya.svg' },
  { name: 'Dattatreya', image: '/images/deities/dattatreya.svg' },
  { name: 'Gorakhnath', image: '/images/deities/gorakhnath.svg' },
  { name: 'Sri Rama', image: '/images/deities/rama.svg' },
  { name: 'Sri Krishna', image: '/images/deities/krishna.svg' },
  { name: 'Hanuman', image: '/images/deities/hanuman.svg' },
  { name: 'Vishnu', image: '/images/deities/vishnu.svg' },
  { name: 'Khatu Shyam Ji', image: '/images/deities/khatushyam.svg' },
]

const QUICK_MENU = [
  { label: 'Poojas', href: '/pooja-calendar' },
  { label: 'Invitations', href: '/invitations' },
  { label: 'About Sankalpam', href: '/about-sankalpam' },
]

function shuffle<T>(list: T[]): T[] {
  const arr = [...list]
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    const temp = arr[i]
    arr[i] = arr[j]
    arr[j] = temp
  }
  return arr
}

export default function Home() {
  const [cards, setCards] = useState<DeityCard[]>(DEITY_CARDS)

  useEffect(() => {
    setCards(shuffle(DEITY_CARDS))
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 via-amber-50 to-yellow-50">
      <header className="border-b border-orange-100 bg-white/90 backdrop-blur">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-11 w-11 rounded-full bg-orange-600 text-white font-bold flex items-center justify-center">
                PS
              </div>
              <div>
                <h1 className="text-2xl md:text-4xl font-extrabold text-orange-900">Pooja Sankalpam</h1>
                <p className="text-sm md:text-base text-orange-700">(Your personal Assistant for Poojas)</p>
              </div>
            </div>
            <Link
              href="/login"
              className="rounded-md bg-orange-600 px-4 py-2 text-sm font-semibold text-white hover:bg-orange-700"
            >
              Login
            </Link>
          </div>

          <nav className="mt-4 flex flex-wrap items-center gap-2">
            {QUICK_MENU.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-full border border-orange-200 bg-white px-4 py-1.5 text-sm font-medium text-orange-800 hover:bg-orange-100"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-10">
        <section className="text-center mb-8">
          <h2 className="text-3xl md:text-5xl font-bold text-orange-900">Welcome to Pooja Sankalpam</h2>
          <p className="mt-3 text-orange-800">
            Explore divine inspiration and begin your pooja journey with personalized Sankalpam guidance.
          </p>
        </section>

        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {cards.map((deity) => (
            <article
              key={deity.name}
              className="overflow-hidden rounded-2xl bg-white shadow-md ring-1 ring-orange-100 hover:shadow-xl transition-shadow"
            >
              <img src={deity.image} alt={deity.name} className="h-56 w-full object-cover" />
              <div className="p-4">
                <p className="text-xl font-bold text-orange-900">{deity.name}</p>
              </div>
            </article>
          ))}
        </section>
      </main>

      <footer className="border-t border-orange-100 bg-white/90">
        <div className="mx-auto max-w-7xl px-4 py-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <p className="text-sm text-slate-600">© {new Date().getFullYear()} Pooja Sankalpam</p>
          <div className="flex flex-wrap gap-4 text-sm">
            <Link href="/about-us" className="text-slate-700 hover:text-orange-700">About Us</Link>
            <Link href="/contact-us" className="text-slate-700 hover:text-orange-700">Contact Us</Link>
            <Link href="/privacy-policy" className="text-slate-700 hover:text-orange-700">Privacy Policy</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}

