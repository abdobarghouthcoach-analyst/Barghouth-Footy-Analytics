import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#0d1117',
        surface: '#161b22',
        surface2: '#1f2937',
        border: '#30363d',
        muted: '#8b949e',
        text: '#c9d1d9',
        accent: '#58a6ff',
        accent2: '#9cf1ff',
      },
      boxShadow: {
        card: '0 8px 30px rgba(0, 0, 0, 0.35)',
      },
    },
  },
  plugins: [],
} satisfies Config
