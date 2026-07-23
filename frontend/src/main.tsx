import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './app/App';
import { assetRegistry } from './services/assets/AssetRegistry';
import './styles/index.css';

// El manifest se carga antes del primer render; si falla, la app arranca igual con fallbacks.
void assetRegistry.load().then(() => {
  assetRegistry.preloadCritical();
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
});
