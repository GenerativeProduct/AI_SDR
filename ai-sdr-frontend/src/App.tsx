import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthGuard } from './components/auth/AuthGuard'
import { AppLayout } from './components/layout/AppLayout'
import { ThemedToaster } from './components/ui/ThemedToaster'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { ConversationsPage } from './pages/ConversationsPage'
import { DashboardPage } from './pages/DashboardPage'
import { IcpPage } from './pages/IcpPage'
import { LoginPage } from './pages/LoginPage'
import { MeetingsPage } from './pages/MeetingsPage'
import { DiscoveryPage } from './pages/DiscoveryPage'
import { EnrichmentPage } from './pages/EnrichmentPage'
import { IntelligencePage } from './pages/IntelligencePage'
import { QualificationPage } from './pages/QualificationPage'
import { FollowUpPage } from './pages/FollowUpPage'
import { CrmPage } from './pages/CrmPage'
import { OutreachPage } from './pages/OutreachPage'
import { PipelinePage } from './pages/PipelinePage'
import { SettingsPage } from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <ThemedToaster />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<AuthGuard />}>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="pipeline" element={<PipelinePage />} />
            <Route path="icp" element={<IcpPage />} />
            <Route path="discovery" element={<DiscoveryPage />} />
            <Route path="enrichment" element={<EnrichmentPage />} />
            <Route path="intelligence" element={<IntelligencePage />} />
            <Route path="qualification" element={<QualificationPage />} />
            <Route path="outreach" element={<OutreachPage />} />
            <Route path="conversations" element={<ConversationsPage />} />
            <Route path="follow-up" element={<FollowUpPage />} />
            <Route path="meetings" element={<MeetingsPage />} />
            <Route path="crm" element={<CrmPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
