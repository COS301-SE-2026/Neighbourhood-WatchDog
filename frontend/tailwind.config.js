/** @type {import('tailwindcss').Config} */
const config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: "var(--font-inter, 'Inter', system-ui, -apple-system, sans-serif)",
        mono: "var(--font-jetbrains-mono, 'JetBrains Mono', Consolas, monospace)",
      },
      colors: {
        navy: "var(--color-navy)",
        blue: "var(--color-blue)",
        sky: "var(--color-sky)",
        steel: "var(--color-steel)",
        white: "var(--color-white)",
        fog: "var(--color-fog)",
        mist: "var(--color-mist)",
        ink: "var(--color-ink)",
        body: "var(--color-body)",
        threat: "var(--color-threat)",
        caution: "var(--color-caution)",
        safe: "var(--color-safe)",
        info: "var(--color-info)",
        sidebar: "var(--color-navy)",
        "sidebar-foreground": "var(--color-white)",
      },
      spacing: {
        1: "var(--space-1)",
        2: "var(--space-2)",
        3: "var(--space-3)",
        4: "var(--space-4)",
        5: "var(--space-5)",
        6: "var(--space-6)",
        8: "var(--space-8)",
        10: "var(--space-10)",
        12: "var(--space-12)",
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
        fast: "var(--motion-fast)",
        normal: "var(--motion-normal)",
        slow: "var(--motion-slow)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

module.exports = config;