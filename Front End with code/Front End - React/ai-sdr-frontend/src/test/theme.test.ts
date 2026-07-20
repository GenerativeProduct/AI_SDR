import { describe, expect, it } from 'vitest'
import { applyTheme, readStoredTheme } from '../lib/theme'

describe('theme', () => {
  it('defaults to light when no storage', () => {
    expect(readStoredTheme()).toBe('light')
  })

  it('applies dark class on document', () => {
    applyTheme('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    applyTheme('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})
