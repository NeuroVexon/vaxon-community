/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'nv-black': {
          DEFAULT: '#0a0a0a',
          50: '#050505',
          100: '#0f0f0f',
          200: '#1a1a1a',
          300: '#252525',
          light: '#1a1a1a',
          lighter: '#2a2a2a',
        },
        'nv-gray': {
          DEFAULT: '#3a3a3a',
          light: '#4a4a4a',
          lighter: '#5a5a5a',
        },
        'nv-accent': {
          DEFAULT: '#00d4ff',
          glow: 'rgba(0, 212, 255, 0.3)',
        },
        'nv-success': '#00ff88',
        'nv-warning': '#ffaa00',
        'nv-danger': '#ff4444',
      },
      fontFamily: {
        'display': ['Orbitron', 'monospace'],
        'sans': ['Space Grotesk', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'nv-glow': '0 0 20px rgba(0, 212, 255, 0.2)',
        'nv-card': '0 4px 20px rgba(0, 0, 0, 0.5)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.6s ease-out',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 212, 255, 0.2)' },
          '50%': { boxShadow: '0 0 30px rgba(0, 212, 255, 0.4)' },
        },
      },
    },
  },
  plugins: [],
}
