import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8123';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    // /assets/ es el árbol de Dirección de Arte (symlink en public/);
    // los bundles van a /static/ para no mezclarse
    assetsDir: 'static',
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: BACKEND, changeOrigin: true },
      '/health': { target: BACKEND, changeOrigin: true },
      '/ws': { target: BACKEND, ws: true },
    },
  },
  test: {
    environment: 'node',
    include: ['src/tests/**/*.test.ts'],
  },
});
