// vite.config.js - configuration for the Vite development server/build tool.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Any request starting with /api is forwarded to the FastAPI backend
    // running on port 8000. This lets our frontend code simply call
    // "/api/..." as if it were on the same server.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
