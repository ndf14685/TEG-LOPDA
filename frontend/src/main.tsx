import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './app/App';
import { assetRegistry } from './services/assets/AssetRegistry';
import './styles/index.css';

import { applyPalette } from './utils/playerColors';

// Los manifests de Dirección de Arte se cargan antes del primer render;
// si alguno falta, la app arranca igual con fallbacks.
void assetRegistry.load().then(() => {
  if (assetRegistry.palette) applyPalette(assetRegistry.palette);
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
});
