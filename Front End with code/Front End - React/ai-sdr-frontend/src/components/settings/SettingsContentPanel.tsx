import type { UserPublic } from '../../api/types'
import { WorkspaceField, WorkspaceSelect } from '../workspace'
import type { SettingsSection } from './SettingsNavPanel'

type ProviderCard = {
  name: string
  data: unknown
}

type SettingsContentPanelProps = {
  section: SettingsSection
  user: UserPublic | null
  theme: 'light' | 'dark'
  onThemeChange: (theme: 'light' | 'dark') => void
  apiUrl: string
  onApiUrlChange: (value: string) => void
  onSaveApi: () => void
  onResetApi: () => void
  activeApiBase: string
  adminEmail: string
  adminPassword: string
  adminRole: string
  onAdminEmailChange: (value: string) => void
  onAdminPasswordChange: (value: string) => void
  onAdminRoleChange: (value: string) => void
  onCreateUser: () => void
  createUserPending: boolean
  providers: ProviderCard[]
}

export function SettingsContentPanel({
  section,
  user,
  theme,
  onThemeChange,
  apiUrl,
  onApiUrlChange,
  onSaveApi,
  onResetApi,
  activeApiBase,
  adminEmail,
  adminPassword,
  adminRole,
  onAdminEmailChange,
  onAdminPasswordChange,
  onAdminRoleChange,
  onCreateUser,
  createUserPending,
  providers,
}: SettingsContentPanelProps) {
  return (
    <section className="sdr-split__right">
      <header className="sdr-split__right-header">
        <div>
          <p className="ws-heading-section">Configuration</p>
          <h2 className="sdr-split__pane-title capitalize">{section}</h2>
          <p className="sdr-split__pane-desc">Manage your workspace {section} settings.</p>
        </div>
      </header>

      <div className="sdr-split__canvas-scroll">
        {section === 'profile' ? (
          <article className="sdr-split__canvas-card">
            <h3 className="sdr-split__canvas-card__title">Profile</h3>
            <p className="mt-3 text-lg font-semibold text-[var(--ws-text-primary)]">{user?.display_name}</p>
            <p className="mt-1 text-sm text-[var(--ws-text-muted)]">
              {user?.email} · {user?.role}
            </p>
          </article>
        ) : null}

        {section === 'appearance' ? (
          <article className="sdr-split__canvas-card">
            <h3 className="sdr-split__canvas-card__title">Appearance</h3>
            <div className="mt-4 max-w-md">
              <WorkspaceSelect
                id="theme-select"
                label="Theme"
                value={theme}
                options={[
                  { value: 'light', label: 'Light (chatbase workspace)' },
                  { value: 'dark', label: 'Dark' },
                ]}
                onChange={(v) => onThemeChange(v as 'light' | 'dark')}
              />
            </div>
          </article>
        ) : null}

        {section === 'api' ? (
          <article className="sdr-split__canvas-card">
            <h3 className="sdr-split__canvas-card__title">API base URL</h3>
            <p className="mt-2 text-sm text-[var(--ws-text-muted)]">
              Default: Vite proxy at /api. Override for direct backend (e.g. http://127.0.0.1:8011).
            </p>
            <div className="mt-4 max-w-lg sdr-split__form">
              <WorkspaceField id="api-url" label="Base URL" value={apiUrl} onChange={onApiUrlChange} />
              <div className="flex gap-2">
                <button type="button" className="ws-btn ws-btn--primary" onClick={onSaveApi}>
                  Save
                </button>
                <button type="button" className="ws-btn ws-btn--secondary" onClick={onResetApi}>
                  Reset
                </button>
              </div>
              <p className="text-xs text-[var(--ws-text-caption)]">Active: {activeApiBase}</p>
            </div>
          </article>
        ) : null}

        {section === 'admin' ? (
          <article className="sdr-split__canvas-card">
            <h3 className="sdr-split__canvas-card__title">Create user</h3>
            <div className="mt-4 grid max-w-2xl gap-4 md:grid-cols-2 sdr-split__form">
              <WorkspaceField id="admin-email" label="Email" value={adminEmail} onChange={onAdminEmailChange} />
              <WorkspaceField
                id="admin-password"
                label="Password"
                type="password"
                value={adminPassword}
                onChange={onAdminPasswordChange}
              />
              <WorkspaceSelect
                id="admin-role"
                label="Role"
                value={adminRole}
                options={[
                  { value: 'operator', label: 'Operator' },
                  { value: 'manager', label: 'Manager' },
                  { value: 'admin', label: 'Admin' },
                ]}
                onChange={onAdminRoleChange}
              />
            </div>
            <button
              type="button"
              className="ws-btn ws-btn--primary mt-4"
              disabled={!adminEmail || !adminPassword || createUserPending}
              onClick={onCreateUser}
            >
              Create user
            </button>
          </article>
        ) : null}

        {section === 'providers' ? (
          <div className="grid gap-4 md:grid-cols-2">
            {providers.map((p) => (
              <article key={p.name} className="sdr-split__canvas-card">
                <h3 className="sdr-split__canvas-card__title">{p.name}</h3>
                <pre className="mt-3 max-h-48 overflow-auto text-xs text-[var(--ws-text-muted)]">
                  {JSON.stringify(p.data ?? { loading: true }, null, 2)}
                </pre>
              </article>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  )
}
