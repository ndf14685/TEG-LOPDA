import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { LandingPage } from '../pages/LandingPage';
import { AdminPage } from '../pages/AdminPage';
import { JoinPage } from '../pages/JoinPage';
import { LobbyPage } from '../pages/LobbyPage';
import { GamePage } from '../pages/GamePage';
import { ProfilePage } from '../pages/ProfilePage';
import { ReplayPage } from '../pages/ReplayPage';
import { PlaytestWidget } from '../components/playtest/PlaytestWidget';
import { PlaytestBoundary } from '../components/playtest/PlaytestBoundary';
import { AdminPlaytestPage } from '../pages/AdminPlaytestPage';

export function App() {
  return (
    <PlaytestBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/admin/playtest" element={<AdminPlaytestPage />} />
          <Route path="/admin/:gameId" element={<AdminPage />} />
          <Route path="/join/:code/:token" element={<JoinPage />} />
          <Route path="/join/:code" element={<LandingPage />} />
          <Route path="/lobby/:code" element={<LobbyPage />} />
          <Route path="/game/:code" element={<GamePage />} />
          <Route path="/p/:token" element={<ProfilePage />} />
          <Route path="/replay/:code" element={<ReplayPage />} />
          <Route path="*" element={<LandingPage />} />
        </Routes>
        <PlaytestWidget />
      </BrowserRouter>
    </PlaytestBoundary>
  );
}
