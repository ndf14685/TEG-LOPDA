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
        <Route path="/join/:gameId/:token" element={<JoinPage />} />
        <Route path="/lobby/:gameId" element={<LobbyPage />} />
        <Route path="/game/:gameId" element={<GamePage />} />
        <Route path="*" element={<LandingPage />} />
      </Routes>
    </BrowserRouter>
  );
}
