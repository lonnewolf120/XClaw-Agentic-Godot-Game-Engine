import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Archivo Black'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      boxShadow: {
        panel: "0 12px 28px rgba(0, 0, 0, 0.32)",
      },
      colors: {
        panel: "#151d2a",
        ink: "#f0f3f7",
        muted: "#97a8bd",
        accent: "#ffc857",
      },
    },
  },
  plugins: [],
};

export default config;
