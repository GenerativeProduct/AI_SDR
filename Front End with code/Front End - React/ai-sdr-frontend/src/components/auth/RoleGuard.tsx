import type { ReactNode } from 'react'
import type { UserRole } from '../../api/types'
import { useAuthStore } from '../../stores/authStore'

const APPROVE_ROLES: UserRole[] = ['operator', 'admin']

export function RoleGuard({
  children,
  requireApprove = false,
}: {
  children: ReactNode
  requireApprove?: boolean
}) {
  const user = useAuthStore((s) => s.user)
  if (!requireApprove) return children
  if (!user || !APPROVE_ROLES.includes(user.role)) {
    return (
      <p className="text-sm text-amber-400">
        Operator or admin role required for this action.
      </p>
    )
  }
  return children
}
