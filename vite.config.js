import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Env files live at the project root (.env for dev, .env.prod for `--mode prod`)
export default defineConfig({
  plugins: [react()],
  envDir: '..',
  server: { port: 5173, host: '127.0.0.1' },
})
