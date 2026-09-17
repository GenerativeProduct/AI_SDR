import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './lib/ThemeContext';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Ingestion } from './pages/Ingestion';
import { Intelligence } from './pages/Intelligence';
import { Profiles } from './pages/Profiles';
import { Orchestration } from './pages/Orchestration';
import { Settings } from './pages/Settings';
import { LiveOps } from './pages/LiveOps';

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/ingestion" element={<Ingestion />} />
            <Route path="/intelligence" element={<Intelligence />} />
            <Route path="/profiles" element={<Profiles />} />
            <Route path="/orchestration" element={<Orchestration />} />
            <Route path="/live-ops" element={<LiveOps />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
