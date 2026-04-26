import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 3000,
    proxy: {
      '/auth':      { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/health':    { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/assets':    { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/risk':      { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/portfolio': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/market':    { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/export':    { target: 'http://127.0.0.1:8000', changeOrigin: true },
    }
  }
})