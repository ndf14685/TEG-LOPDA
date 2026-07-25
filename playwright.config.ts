import { defineConfig } from '@playwright/test';

/**
 * E2E contra el backend FastAPI real (backend/) + frontend Vite.
 * Puertos aislados (8124/5174) para no chocar con los servicios de dev
 * que corren en 8123/5173. DB efímera por corrida.
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  use: {
    baseURL: 'http://localhost:5174',
    screenshot: 'only-on-failure',
  },
  webServer: [
    {
      command:
        'cd backend && TEG_ADMIN_TOKEN=dev-admin TEG_COMMENTATOR_PROVIDER=mock TEG_AI_PLAYER_THINK_SECONDS=0.05 TEG_DB_PATH=$(mktemp -d)/teg-e2e.db TEG_CORS_ORIGINS=http://localhost:5174 uv run uvicorn teg_backend.main:app --port 8124',
      url: 'http://localhost:8124/health',
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: 'BACKEND_URL=http://localhost:8124 pnpm --filter @teg/frontend exec vite --port 5174 --strictPort',
      url: 'http://localhost:5174',
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
