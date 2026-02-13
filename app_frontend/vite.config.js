import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
// Backend URL: use host.docker.internal when running in Docker, localhost otherwise
const BACKEND_URL = process.env.DOCKER_ENV 
  ? 'http://host.docker.internal:8000'
  : 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/camera': {
        target: BACKEND_URL,
        changeOrigin: true
      },
      '/recording': {
        target: BACKEND_URL,
        changeOrigin: true
      },
      '/edge': {
        target: BACKEND_URL,
        changeOrigin: true
      },
      '/health': {
        target: BACKEND_URL,
        changeOrigin: true
      },
      '/labeling': {
        target: BACKEND_URL,
        changeOrigin: true
      },
      '/ml': {
        target: BACKEND_URL,
        changeOrigin: true
      },
      '/defects': {
        target: BACKEND_URL,
        changeOrigin: true
      }
    }
  }
})
