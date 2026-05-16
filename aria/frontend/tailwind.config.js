/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#6C63FF',
          light: '#8B84FF',
          dark: '#4B43CC',
        },
        accent: '#FF6B6B',
        surface: {
          DEFAULT: '#FFFFFF',
          alt: '#F8F8FC',
        },
      },
      fontFamily: {
        sans: ['Syne', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        sm: '6px',
        md: '12px',
        lg: '20px',
      },
      // Minimum 44px touch targets (WCAG 2.5.5 / Uma_UX requirement)
      minHeight: { tap: '44px' },
      minWidth: { tap: '44px' },
    },
  },
  plugins: [],
}
