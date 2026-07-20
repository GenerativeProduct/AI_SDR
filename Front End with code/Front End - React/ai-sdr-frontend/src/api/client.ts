const ENV_API_BASE = import.meta.env.VITE_API_URL ?? '/api'
const STORAGE_KEY = 'sdr_api_base'

export function getApiBase(): string {
  if (typeof localStorage !== 'undefined') {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored?.trim()) return stored.trim()
  }
  return ENV_API_BASE
}

export function setApiBase(url: string) {
  const trimmed = url.trim()
  if (trimmed) localStorage.setItem(STORAGE_KEY, trimmed)
  else localStorage.removeItem(STORAGE_KEY)
}

export function clearApiBaseOverride() {
  localStorage.removeItem(STORAGE_KEY)
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function getTokens() {
  return {
    access: localStorage.getItem('sdr_access_token'),
    refresh: localStorage.getItem('sdr_refresh_token'),
  }
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem('sdr_access_token', access)
  localStorage.setItem('sdr_refresh_token', refresh)
}

export function clearTokens() {
  localStorage.removeItem('sdr_access_token')
  localStorage.removeItem('sdr_refresh_token')
}

async function refreshAccessToken(): Promise<string | null> {
  const { refresh } = getTokens()
  if (!refresh) return null
  const res = await fetch(`${getApiBase()}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  })
  if (!res.ok) {
    clearTokens()
    return null
  }
  const data = await res.json()
  setTokens(data.access_token, data.refresh_token)
  return data.access_token as string
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const { access } = getTokens()
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (access) headers.set('Authorization', `Bearer ${access}`)

  const res = await fetch(`${getApiBase()}${path}`, { ...options, headers })
  if (res.status === 401 && retry) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      headers.set('Authorization', `Bearer ${newToken}`)
      const retryRes = await fetch(`${getApiBase()}${path}`, { ...options, headers })
      if (!retryRes.ok) {
        const err = await retryRes.text()
        throw new ApiError(retryRes.status, err || retryRes.statusText)
      }
      return retryRes.json() as Promise<T>
    }
  }
  if (!res.ok) {
    const err = await res.text()
    throw new ApiError(res.status, err || res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
}
