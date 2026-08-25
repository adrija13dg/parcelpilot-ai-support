import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { SessionProvider, useSession } from './context/SessionContext';
import { ThemeProvider } from './context/ThemeContext';
import { api } from './api/client';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import IssuesPage from './pages/IssuesPage';
import SourcesPage from './pages/SourcesPage';
import Sidebar from './components/Sidebar';

function AppShell() {
  const { session } = useSession();
  const [backendOk, setBackendOk] = useState(null);

  useEffect(() => {
    api.health()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false));
  }, []);

  if (!session) {
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    );
  }

  return (
    <div className="app-shell">
      <div className="ambient-bg" aria-hidden="true">
        <div className="orb" />
      </div>
      {backendOk === false && (
        <div className="backend-banner">
          Backend offline — open <strong>http://localhost:8000</strong> after running Start ParcelPilot.bat
        </div>
      )}
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/issues" element={<IssuesPage />} />
          <Route path="/sources" element={<SourcesPage />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <SessionProvider>
        <BrowserRouter>
          <AppShell />
        </BrowserRouter>
      </SessionProvider>
    </ThemeProvider>
  );
}
