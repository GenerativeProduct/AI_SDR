export type ThemeMode = 'light' | 'dark'

const STORAGE_KEY = 'sdr_theme'
const ZUSTAND_KEY = 'sdr-ui'

function readZustandTheme(): ThemeMode | null {
  try {
    const raw = localStorage.getItem(ZUSTAND_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as { state?: { theme?: string } }
    const theme = parsed.state?.theme
    if (theme === 'light' || theme === 'dark') return theme
  } catch {
    /* ignore */
  }
  return null
}

export function readStoredTheme(): ThemeMode {
  const fromZustand = readZustandTheme()
  if (fromZustand) return fromZustand

  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'light' || stored === 'dark') return stored
  } catch {
    /* ignore */
  }
  return 'light'
}

export function applyTheme(theme: ThemeMode) {
  const root = document.documentElement
  root.classList.toggle('dark', theme === 'dark')
  root.style.colorScheme = theme === 'dark' ? 'dark' : 'light'

  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    /* ignore */
  }
}

export function initTheme() {
  applyTheme(readStoredTheme())
}
