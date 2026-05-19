import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],

  theme: {
    extend: {
      colors: {
        command: {
          navy: "#1D2A5E",
        },

        alert: {
          blue: "#3B5EDE",
        },

        sky: {
          blue: "#5B8DEF",
        },

        steel: "#2C3E6B",

        fog: "#F4F6FA",
        mist: "#D0D7E8",
        ink: "#1A1A2E",

        threat: {
          red: "#DC2626",
        },

        caution: {
          amber: "#D97706",
        },

        safe: {
          green: "#16A34A",
        },

        info: {
          blue: "#0284C7",
        },
      },

      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },

      boxShadow: {
        sm: "0 1px 3px rgba(29,42,94,0.08)",
        md: "0 4px 12px rgba(29,42,94,0.12)",
        lg: "0 8px 24px rgba(29,42,94,0.16)",
        alert: "0 0 0 3px rgba(220,38,38,0.30)",
      },

      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
    },
  },

  plugins: [],
};

export default config;