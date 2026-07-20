import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import {
  KeyRound,
  Monitor,
  Plug,
  RefreshCw,
  User,
  UserPlus,
} from 'lucide-react'
import { toast } from 'sonner'
import { api, clearApiBaseOverride, getApiBase, setApiBase } from '../api/client'
import {
  useCrmStatus,
  useDiscoveryStatus,
  useEnrichmentStatus,
  useHealth,
  useMeetingsStatus,
} from '../api/hooks'
import type { UserPublic } from '../api/types'
import { SettingsContentPanel } from '../components/settings/SettingsContentPanel'
import { SettingsNavPanel, type SettingsSection } from '../components/settings/SettingsNavPanel'
import { PageHeader } from '../components/workspace'
import { pageTitles } from '../config/navigation'
import { useAuthStore } from '../stores/authStore'
import { useUiStore } from '../stores/uiStore'

export function SettingsPage() {
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const theme = useUiStore((s) => s.theme)
  const setTheme = useUiStore((s) => s.setTheme)
  const [section, setSection] = useState<SettingsSection>('profile')
  const [apiUrl, setApiUrl] = useState(() => getApiBase())
  const [adminEmail, setAdminEmail] = useState('')
  const [adminPassword, setAdminPassword] = useState('')
  const [adminRole, setAdminRole] = useState('operator')

  const health = useHealth()
  const discoveryStatus = useDiscoveryStatus()
  const enrichmentStatus = useEnrichmentStatus()
  const meetingStatus = useMeetingsStatus()
  const crmStatus = useCrmStatus()

  useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      const me = await api.get<UserPublic>('/auth/me')
      setUser(me)
      return me
    },
  })

  const createUser = useMutation({
    mutationFn: () =>
      api.post('/auth/users', {
        email: adminEmail,
        password: adminPassword,
        display_name: adminEmail.split('@')[0],
        role: adminRole,
      }),
    onSuccess: () => {
      toast.success('User created')
      setAdminEmail('')
      setAdminPassword('')
    },
    onError: () => toast.error('Create user failed (admin only)'),
  })

  const providers = [
    { name: 'API Health', data: health.data },
    { name: 'Discovery', data: discoveryStatus.data },
    { name: 'Enrichment', data: enrichmentStatus.data },
    { name: 'Meetings', data: meetingStatus.data },
    { name: 'CRM', data: crmStatus.data },
  ]

  const refreshProviders = () => {
    health.refetch()
    discoveryStatus.refetch()
    enrichmentStatus.refetch()
    meetingStatus.refetch()
    crmStatus.refetch()
  }

  const navItems = [
    { id: 'profile' as const, label: 'Profile', icon: User },
    { id: 'appearance' as const, label: 'Appearance', icon: Monitor },
    { id: 'api' as const, label: 'API', icon: KeyRound },
    ...(user?.role === 'admin' ? [{ id: 'admin' as const, label: 'Admin', icon: UserPlus }] : []),
    { id: 'providers' as const, label: 'Providers', icon: Plug },
  ]

  return (
    <section className="sdr-split sdr-settings">
      <PageHeader
        embedded
        flush
        className="sdr-split__header"
        eyebrow="Workspace"
        title={pageTitles['/settings'] ?? 'Settings'}
        description="Profile, theme, API configuration, and provider health."
        actions={
          <button type="button" className="ws-btn ws-btn--secondary" onClick={refreshProviders}>
            <RefreshCw className="h-4 w-4" aria-hidden />
            Refresh providers
          </button>
        }
      />

      <div className="sdr-split__workspace">
        <SettingsNavPanel section={section} items={navItems} onSectionChange={setSection} />
        <SettingsContentPanel
          section={section}
          user={user}
          theme={theme}
          onThemeChange={setTheme}
          apiUrl={apiUrl}
          onApiUrlChange={setApiUrl}
          onSaveApi={() => {
            setApiBase(apiUrl)
            toast.success('Saved — reload to apply everywhere')
          }}
          onResetApi={() => {
            clearApiBaseOverride()
            setApiUrl(import.meta.env.VITE_API_URL ?? '/api')
            toast.success('Reset — reload to apply')
          }}
          activeApiBase={getApiBase()}
          adminEmail={adminEmail}
          adminPassword={adminPassword}
          adminRole={adminRole}
          onAdminEmailChange={setAdminEmail}
          onAdminPasswordChange={setAdminPassword}
          onAdminRoleChange={setAdminRole}
          onCreateUser={() => createUser.mutate()}
          createUserPending={createUser.isPending}
          providers={providers}
        />
      </div>
    </section>
  )
}
