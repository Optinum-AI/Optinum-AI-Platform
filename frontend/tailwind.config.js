/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#050505",
        panel: "#0b0b0d",
        card: "#141414",
        card2: "#1a1a1a",
        line: "#262626",
        accent: "#dc2626",
        accent2: "#ef4444",
        salmon: "#fca5a5",
        pos: "#22c55e",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
