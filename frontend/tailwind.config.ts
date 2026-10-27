import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        phantom: {
          bg: "#0a0a0c",
          panel: "#141418",
          green: "#3dff8a",
          violet: "#6b4cff",
          red: "#ff3d5a",
          muted: "#8a8a96",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "Consolas", "monospace"],
        sans: ["system-ui", "Segoe UI", "sans-serif"],
      },
      backgroundImage: {
        scanlines:
          "repeating-linear-gradient(0deg, rgba(0,0,0,0.15), rgba(0,0,0,0.15) 1px, transparent 1px, transparent 3px)",
      },
    },
  },
  plugins: [],
};

export default config;
