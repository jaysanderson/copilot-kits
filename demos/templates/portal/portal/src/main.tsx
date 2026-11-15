import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { initColorScheme } from './lib/theme';
import './index.css';

// Fix 4 (flagship rebuild, Section 3.B): only load the Kendo theme when the
// Shell actually renders a Kendo component (UI_MODE=kendo). Unconditionally
// importing this pulled Roboto from Google Fonts (404s in a locked network)
// and shipped 764KB of dead CSS in opensource mode (ResearchOS finding,
// CLAUDE.md). Vite's static string import can't be conditional, so this
// loads it dynamically and only when needed.
if (import.meta.env.VITE_UI_MODE === 'kendo') {
  import('@progress/kendo-theme-default/dist/all.css');
}

// Set light/dark before first paint to avoid a flash.
initColorScheme();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
