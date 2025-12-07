/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'opex-navy': '#1a2859',
        'opex-cyan': '#00c4cc',
        'opex-gray': '#6b7280',
      },
    },
  },
  plugins: [],
}
