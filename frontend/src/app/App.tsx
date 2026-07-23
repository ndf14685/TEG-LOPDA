import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { LandingPage } from '../pages/LandingPage';
import { AdminPage } from '../pages/AdminPage';
import { JoinPage } from '../pages/JoinPage';
import { LobbyPage } from '../pages/LobbyPage';
import { GamePage } from '../pages/GamePage';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/admin/:gameId" element={<AdminPage />} />
        <Route path="/join/:code/:token" element={<JoinPage />} />
        <Route path="/join/:code" element={<LandingPage />} />
        <Route path="/lobby/:code" element={<LobbyPage />} />
        <Route path="/game/:code" element={<GamePage />} />
        <Route path="*" element={<LandingPage />} />
      </Routes>
    </BrowserRouter>
  );
}
