import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// The browser bundle never talks to Nuclia directly — every /api/* call goes to
// the Express server (server/index.mjs), which holds the service-account token.
// In dev, Vite serves the UI on :5173 and proxies /api to the API server.
const API_PORT = process.env.API_PORT || '4000';

export default defineConfig(({ mode }) => {
  // The app's real .env lives at the project root (one level above portal/),
  // not portal/.env, and UI_MODE isn't VITE_-prefixed (it's a server-side
  // build/runtime flag, not something meant to be a generic browser global).
  // Load it explicitly with an empty prefix and inject only the one value the
  // bundle needs (Fix 4, Section 3.B: gate the Kendo theme import on it).
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '');
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: `http://localhost:${API_PORT}`,
          changeOrigin: true,
        },
      },
    },
    define: {
      'import.meta.env.VITE_UI_MODE': JSON.stringify(env.UI_MODE || 'kendo'),
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
    },
  };
});
