type ConfirmModalProps = {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  onConfirm: () => void
  onCancel: () => void
  loading?: boolean
  variant?: 'default' | 'danger'
}

export function WorkspaceConfirmModal({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  onConfirm,
  onCancel,
  loading = false,
  variant = 'default',
}: ConfirmModalProps) {
  if (!open) return null

  return (
    <div className="ws-modal-scrim" role="presentation" onClick={onCancel}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="ws-confirm-title"
        className="ws-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="ws-confirm-title" className="text-lg font-semibold text-[var(--ws-text-primary)]">
          {title}
        </h3>
        <p className="mt-2 text-sm text-[var(--ws-text-muted)]">{message}</p>
        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            className="ws-btn ws-btn--secondary"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="button"
            className={variant === 'danger' ? 'ws-btn ws-btn--primary' : 'ws-btn ws-btn--primary'}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? 'Working…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
