import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    // No proxy needed - frontend calls backend directly on port 8010
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})

