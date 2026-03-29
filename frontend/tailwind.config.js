/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        serif: ["'Spectral'", "Georgia", "serif"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
        /* Opening: thin high-contrast serif (FAQ / editorial reference) */
        display: ["'Cormorant Garamond'", "Georgia", "serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      colors: {
        /* Warm cream paper & charcoal ink (off-black, not pure black) */
        ink: "#2c2c2a",
        paper: {
          DEFAULT: "#f2f0e9",
          2: "#ebe8e0",
          3: "#e3dfd4",
          4: "#d9d4c8",
        },
        forest: {
          950: "#141c17",
          900: "#1e2a22",
          800: "#2a3830",
          700: "#3d4d42",
          600: "#4f6256",
        },
        sage: {
          50: "#f4faf6",
          100: "#e3f0e8",
          200: "#c5ddcf",
          300: "#9cbfaa",
          400: "#6b9a82",
          500: "#4a7c62",
          600: "#3a634e",
          700: "#2f4f40",
        },
        wash: {
          peach: "#f3e4dc",
          mist: "#e8eef0",
          lilac: "#ebe4f0",
          leaf: "#dceee0",
        },
      },
      backgroundImage: {
        /* Soft “illustration / canvas” wash — light, layered, not dark UI */
        "experience-wash":
          "radial-gradient(ellipse 100% 80% at 10% 5%, rgba(210, 228, 218, 0.55) 0%, transparent 55%), radial-gradient(ellipse 90% 70% at 92% 12%, rgba(228, 222, 236, 0.45) 0%, transparent 50%), linear-gradient(180deg, #f2f0e9 0%, #ebe8e0 45%, #e6e2d8 100%)",
        "subtle-grid":
          "linear-gradient(to right, rgba(74, 124, 98, 0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(74, 124, 98, 0.06) 1px, transparent 1px)",
      },
      boxShadow: {
        glass:
          "0 12px 48px rgba(30, 42, 34, 0.08), 0 2px 8px rgba(30, 42, 34, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.85)",
        "glass-inner": "inset 0 1px 0 rgba(255, 255, 255, 0.9)",
      },
    },
  },
  plugins: [],
};
