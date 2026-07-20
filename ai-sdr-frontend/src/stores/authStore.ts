import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UserPublic } from '../api/types'

interface AuthState {
  user: UserPublic | null
  setUser: (user: UserPublic | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      setUser: (user) => set({ user }),
      logout: () => {
        localStorage.removeItem('sdr_access_token')
        localStorage.removeItem('sdr_refresh_token')
        set({ user: null })
      },
    }),
    { name: 'sdr-auth', partialize: (s) => ({ user: s.user }) },
  ),
)

interface PipelineState {
  lastResult: Record<string, unknown> | null
  setLastResult: (result: Record<string, unknown> | null) => void
  icpDraft: Record<string, unknown> | null
  setIcpDraft: (draft: Record<string, unknown> | null) => void
}

export const usePipelineStore = create<PipelineState>((set) => ({
  lastResult: null,
  setLastResult: (lastResult) => set({ lastResult }),
  icpDraft: null,
  setIcpDraft: (icpDraft) => set({ icpDraft }),
}))
