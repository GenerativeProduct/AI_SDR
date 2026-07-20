import { History, Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

export type IcpVersionItem = {
  version: number
  status: string
  label: string
}

type IcpVersionPanelProps = {
  versions: IcpVersionItem[]
  selectedVersion?: number
  onSelectVersion: (version: number) => void
  isLoading?: boolean
  selectedIcpName?: string
}

export function IcpVersionPanel({
  versions,
  selectedVersion,
  onSelectVersion,
  isLoading,
  selectedIcpName,
}: IcpVersionPanelProps) {
  if (!versions.length && !isLoading) return null

  return (
    <aside className="sdr-icp__versions">
      <header className="sdr-icp__versions-header">
        <div>
          <p className="ws-heading-section">History</p>
          <h2 className="sdr-icp__pane-title">Version timeline</h2>
          <p className="sdr-icp__pane-desc">
            {selectedIcpName ? `Revisions for ${selectedIcpName}` : 'Select an ICP to browse versions'}
          </p>
        </div>
        <span className="sdr-icp__versions-count" aria-hidden>
          <History className="h-4 w-4" />
          {versions.length}
        </span>
      </header>

      <div className="sdr-icp__versions-body">
        {isLoading ? (
          <div className="sdr-icp__versions-loading" aria-busy>
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
            Loading versions…
          </div>
        ) : (
          <ol className="sdr-icp-version-list">
            {versions.map((version, index) => {
              const active =
                selectedVersion === version.version ||
                (!selectedVersion && index === 0)
              return (
                <li key={version.version}>
                  <button
                    type="button"
                    className={cn('sdr-icp-version-item ws-focus-ring', active && 'sdr-icp-version-item--active')}
                    onClick={() => onSelectVersion(version.version)}
                  >
                    <span className="sdr-icp-version-item__dot" aria-hidden />
                    <span className="min-w-0 flex-1 text-left">
                      <span className="sdr-icp-version-item__title">v{version.version}</span>
                      <span className="sdr-icp-version-item__status">{version.status}</span>
                    </span>
                  </button>
                </li>
              )
            })}
          </ol>
        )}
      </div>
    </aside>
  )
}
