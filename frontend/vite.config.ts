import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "127.0.0.1",
    strictPort: false,
    /** macOS / iCloud Desktop / network drives: native file watch often misses edits — polling fixes HMR */
    watch: {
      usePolling: true,
      interval: 200,
    },
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
    },
  },
});
