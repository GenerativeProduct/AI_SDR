import { Sparkles } from 'lucide-react'
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api, setTokens } from '../api/client'
import type { TokenPair, UserPublic } from '../api/types'
import { AuthPasswordField } from '../components/auth/AuthPasswordField'
import { AuthTextField } from '../components/auth/AuthTextField'
import { useAuthStore } from '../stores/authStore'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const setUser = useAuthStore((s) => s.setUser)
  const from = (location.state as { from?: string } | null)?.from ?? '/'
  const [email, setEmail] = useState('admin@sdr.local')
  const [password, setPassword] = useState('admin123')

  const login = useMutation({
    mutationFn: async () => {
      const tokens = await api.post<TokenPair>('/auth/login', { email, password })
      setTokens(tokens.access_token, tokens.refresh_token)
      const user = await api.get<UserPublic>('/auth/me')
      return user
    },
    onSuccess: (user) => {
      setUser(user)
      toast.success('Signed in')
      navigate(from, { replace: true })
    },
    onError: () => toast.error('Invalid credentials'),
  })

  return (
    <div className="auth-page auth-main">
      <div className="auth-form-stage auth-form-stage--narrow book-demo-form-stage flex min-h-svh items-center justify-center px-4 py-12">
        <div className="auth-form-card book-demo-form-card w-full max-w-md">
          <header className="book-demo-form-card__header">
            <div className="book-demo-form-card__meta">
              <span className="book-demo-form-card__kicker flex items-center gap-2">
                <Sparkles className="h-3.5 w-3.5" aria-hidden />
                AI SDR Platform
              </span>
            </div>
            <h1 className="book-demo-form-card__title">Sign in</h1>
            <p className="book-demo-form-card__subtitle">
              Access the <span className="book-demo-form-card__subtitle-accent">operator console</span>
            </p>
          </header>

          <div className="auth-form-card__body book-demo-form-card__body">
            <form
              className="auth-form__fields book-demo-form__fields px-[var(--auth-pad-x,1.5rem)] pb-6"
              onSubmit={(e) => {
                e.preventDefault()
                login.mutate()
              }}
            >
              <AuthTextField
                id="login-email"
                name="email"
                label="Email"
                type="email"
                value={email}
                onChange={setEmail}
                autoComplete="email"
              />
              <AuthPasswordField
                id="login-password"
                name="password"
                label="Password"
                value={password}
                onChange={setPassword}
              />
              <div className="book-demo-form__actions mt-4">
                <button
                  type="submit"
                  disabled={login.isPending}
                  className="book-demo-submit w-full"
                >
                  {login.isPending ? 'Signing in…' : 'Sign in'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
