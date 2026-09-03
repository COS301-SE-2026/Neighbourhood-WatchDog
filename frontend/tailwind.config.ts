import type { Config } from "tailwindcss"

const config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: "var(--font-inter, 'Inter', system-ui, -apple-system, sans-serif)",
        mono: "var(--font-jetbrains-mono, 'JetBrains Mono', Consolas, monospace)",
      },
      colors: {
        brand: {
          void: "var(--color-void)",
          abyss: "var(--color-abyss)",
          depth: "var(--color-depth)",
          slate: "var(--color-slate)",
          gunmetal: "var(--color-gunmetal)",
          ash: "var(--color-ash)",
          frost: "var(--color-frost)",
          green: "var(--color-green)",
          pulse: "var(--color-pulse)",
          ice: "var(--color-ice)",
          threat: "var(--color-threat)",
          caution: "var(--color-caution)",
          safe: "var(--color-safe)",
          info: "var(--color-info)",
        },
      },
      spacing: {
        "1": "var(--space-1)",
        "2": "var(--space-2)",
        "3": "var(--space-3)",
        "4": "var(--space-4)",
        "5": "var(--space-5)",
        "6": "var(--space-6)",
        "8": "var(--space-8)",
        "10": "var(--space-10)",
        "12": "var(--space-12)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        full: "var(--radius-full)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
        alert: "var(--shadow-alert)",
      },
      transitionDuration: {
        fast: "var(--duration-fast: 100ms;)",
        normal: "var(--duration-normal: 200ms;)",
        slow: "var(--duration-slow: 350ms;)",
      },
    },
  },
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  plugins: [require("tailwindcss-animate")],
} satisfies Config

export default config