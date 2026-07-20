import type { DiscoveredAccount, DiscoveredContact } from '../../api/types'

export function formatCount(value: number) {
  return value.toLocaleString()
}

export function contactsByAccount(contacts: DiscoveredContact[]) {
  const map = new Map<string, DiscoveredContact[]>()
  for (const contact of contacts) {
    const list = map.get(contact.account_id) ?? []
    list.push(contact)
    map.set(contact.account_id, list)
  }
  return map
}

export function averageFitScore(accounts: DiscoveredAccount[]) {
  if (accounts.length === 0) return 0
  const total = accounts.reduce((sum, account) => sum + account.fit_score, 0)
  return Math.round(total / accounts.length)
}

export function accountsWithContacts(accounts: DiscoveredAccount[], contactMap: Map<string, DiscoveredContact[]>) {
  return accounts.filter((account) => (contactMap.get(account.account_id)?.length ?? 0) > 0).length
}

export function fitTone(score: number): 'default' | 'success' | 'risk' {
  if (score >= 70) return 'success'
  if (score < 40) return 'risk'
  return 'default'
}
