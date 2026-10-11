import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const demo = process.env.VITE_DEMO_MODE === 'true';

export default defineConfig({
  plugins: [react()],
  base: demo ? './' : '/',
  build: demo ? { outDir: '../docs', emptyOutDir: false } : undefined,
  server: {
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
});
