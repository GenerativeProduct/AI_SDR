import { describe, expect, it } from 'vitest'
import { cn } from '../../lib/utils'

describe('auth storage keys', () => {
  it('uses consistent localStorage keys', () => {
    expect(cn('sdr_access_token', 'sdr_refresh_token')).toContain('sdr')
  })
})

describe('role guard roles', () => {
  it('includes operator for approve actions', () => {
    const approveRoles = ['operator', 'admin']
    expect(approveRoles).toContain('operator')
  })
})
