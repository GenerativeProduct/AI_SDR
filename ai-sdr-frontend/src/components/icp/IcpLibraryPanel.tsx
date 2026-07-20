import { FileStack, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { cn } from '../../lib/utils'
import { EmptyState, ListLoading, WsSearchInput } from '../workspace'

export type IcpListItem = {
  icp_id: string
  icp_name: string
  version: number
}

type IcpLibraryPanelProps = {
  items: IcpListItem[]
  total: number
  selectedId: string | null
  isLoading: boolean
  onSelect: (id: string) => void
  onCreateNew: () => void
}

export function IcpLibraryPanel({
  items,
  total,
  selectedId,
  isLoading,
  onSelect,
  onCreateNew,
}: IcpLibraryPanelProps) {
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return items
    return items.filter((item) => item.icp_name.toLowerCase().includes(q))
  }, [items, query])

  return (
    <aside className="sdr-icp__library">
      <header className="sdr-icp__library-header">
        <div>
          <p className="ws-heading-section">Library</p>
          <h2 className="sdr-icp__pane-title">Saved ICPs</h2>
          <p className="sdr-icp__pane-desc">{total} definition{total === 1 ? '' : 's'} in workspace</p>
        </div>
        <button type="button" className="ws-btn ws-btn--secondary ws-btn--compact" onClick={onCreateNew}>
          <Plus className="h-4 w-4" aria-hidden />
          New
        </button>
      </header>

      <div className="sdr-icp__library-search">
        <WsSearchInput
          value={query}
          onChange={setQuery}
          placeholder="Search ICPs…"
          aria-label="Search saved ICPs"
        />
      </div>

      <div className="sdr-icp__library-body">
        {isLoading ? (
          <ListLoading rows={5} />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<FileStack className="h-7 w-7" aria-hidden />}
            title={query ? 'No matching ICPs' : 'No saved ICPs yet'}
            description={
              query
                ? 'Try a different search term or create a new definition.'
                : 'Build criteria on the right and save your first ideal customer profile.'
            }
            action={
              !query ? (
                <button type="button" className="ws-btn ws-btn--primary" onClick={onCreateNew}>
                  Start new ICP
                </button>
              ) : null
            }
          />
        ) : (
          <ul className="sdr-icp-library-list">
            {filtered.map((item) => {
              const active = selectedId === item.icp_id
              return (
                <li key={item.icp_id}>
                  <button
                    type="button"
                    className={cn('sdr-icp-library-item ws-focus-ring', active && 'sdr-icp-library-item--active')}
                    onClick={() => onSelect(item.icp_id)}
                  >
                    <span className="sdr-icp-library-item__icon" aria-hidden>
                      <TargetIcon />
                    </span>
                    <span className="sdr-icp-library-item__copy min-w-0">
                      <span className="sdr-icp-library-item__name">{item.icp_name}</span>
                      <span className="sdr-icp-library-item__meta">Version {item.version}</span>
                    </span>
                    {active ? <span className="sdr-icp-library-item__badge">Active</span> : null}
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </aside>
  )
}

function TargetIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}
