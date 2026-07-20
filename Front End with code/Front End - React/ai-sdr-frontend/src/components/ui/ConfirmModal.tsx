import { WorkspaceConfirmModal } from '../workspace/ConfirmModal'

export function ConfirmModal(props: {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  onConfirm: () => void
  onCancel: () => void
  loading?: boolean
}) {
  return <WorkspaceConfirmModal {...props} />
}
