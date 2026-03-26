'use client'

/* eslint-disable @next/next/no-img-element */
import { useEffect, useState } from 'react'
import SiteHeader from '@/components/SiteHeader'
import SiteFooter from '@/components/SiteFooter'

type DeityCard = {
  name: string
  image: string
}

const DEITY_CARDS: DeityCard[] = [
  { name: 'Ganesha', image: '/images/deities/ganesha.png' },
  { name: 'Lakshmi', image: '/images/deities/lakshmi.png' },
  { name: 'Saraswati', image: '/images/deities/saraswati.jpg' },
  { name: 'Shiva', image: '/images/deities/shiva.svg' },
  { name: 'Durga', image: '/images/deities/durga.svg' },
  { name: 'Venkateswara', image: '/images/deities/venkateswara.png' },
  { name: 'Subramanya', image: '/images/deities/subramanya.svg' },
  { name: 'Dattatreya', image: '/images/deities/dattatreya.svg' },
  { name: 'Gorakhnath', image: '/images/deities/gorakhnath.svg' },
  { name: 'Sri Rama', image: '/images/deities/rama.svg' },
  { name: 'Sri Krishna', image: '/images/deities/krishna.svg' },
  { name: 'Hanuman', image: '/images/deities/hanuman.png' },
  { name: 'Vishnu', image: '/images/deities/vishnu.svg' },
  { name: 'Khatu Shyam Ji', image: '/images/deities/khatushyam.svg' },
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
    <div className="page-bg flex flex-col">
      <SiteHeader />

      <main className="mx-auto max-w-7xl w-full px-4 py-10 flex-1">
        <section className="text-center mb-8 sm:mb-10 px-2">
          <h2 className="font-cinzel text-2xl sm:text-3xl md:text-5xl font-bold text-sacred-800 leading-tight">
            Welcome to Pooja Sankalpam
          </h2>
          <div className="gold-divider mx-auto max-w-xs my-4" />
          <p className="text-stone-600 text-lg max-w-2xl mx-auto">
            Explore divine inspiration and begin your pooja journey with personalized Sankalpam guidance.
          </p>
        </section>

        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {cards.map((deity) => (
            <article
              key={deity.name}
              className="sacred-card overflow-hidden hover:shadow-xl transition-shadow"
            >
              <div className="h-56 w-full bg-cream-100 flex items-center justify-center">
                <img
                  src={deity.image}
                  alt={deity.name}
                  className="h-full w-full object-contain"
                />
              </div>
              <div className="p-4 bg-cream-100">
                <p className="font-cinzel text-lg font-bold text-sacred-700">{deity.name}</p>
              </div>
            </article>
          ))}
        </section>
      </main>

      <SiteFooter />
    </div>
  )
}
