import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: {
    port: 5173,
    // Host permitido atrás do reverse proxy (Caddy); Vite 6 bloqueia Host desconhecido por padrão.
    allowedHosts: [
      "localhost",
      "127.0.0.1",
      "ttv-dev.evolvetechbr.cloud",
    ],
    proxy: {
      "/api": {
        // No Docker Compose use DEV_API_PROXY_TARGET=http://backend:8000
        target: process.env.DEV_API_PROXY_TARGET ?? "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
