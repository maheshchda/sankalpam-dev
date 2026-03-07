/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        sacred: {
          900: '#0f0404',
          800: '#1a0808',
          700: '#2d1010',
          600: '#4a1a1a',
          500: '#6b2020',
        },
        gold: {
          300: '#ffd700',
          400: '#f0b429',
          500: '#d4a017',
          600: '#c8860a',
          700: '#a06808',
        },
        cream: {
          50: '#fefcf9',
          100: '#fdf8f0',
          200: '#f5ede0',
          300: '#edddc8',
        },
        // Keep primary for backward compat
        primary: {
          50: '#fef3e2',
          100: '#fde4b8',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
      },
      fontFamily: {
        cinzel: ['Cinzel', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}
