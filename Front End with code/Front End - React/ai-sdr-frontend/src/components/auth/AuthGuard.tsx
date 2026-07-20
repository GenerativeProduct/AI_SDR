import { useEffect } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { UserPublic } from '../../api/types'
import { PageLoading } from '../workspace/loading'
import { useAuthStore } from '../../stores/authStore'

export function AuthGuard() {
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const logout = useAuthStore((s) => s.logout)
  const location = useLocation()
  const hasToken = Boolean(localStorage.getItem('sdr_access_token'))

  const meQuery = useQuery({
    queryKey: ['auth-me'],
    queryFn: () => api.get<UserPublic>('/auth/me'),
    enabled: hasToken && !user,
    retry: false,
  })

  useEffect(() => {
    if (meQuery.data) setUser(meQuery.data)
    if (meQuery.isError) logout()
  }, [meQuery.data, meQuery.isError, setUser, logout])

  if (!hasToken) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (!user && meQuery.isLoading) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-[var(--ws-canvas)]">
        <PageLoading label="Restoring session" />
      </div>
    )
  }

  if (!user && meQuery.isError) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
