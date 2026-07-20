import { DEFAULT_ICP_WEIGHTS, type IcpWeights } from './icpConstants'

export type IcpFormState = {
  industriesText: string
  geographiesText: string
  personasText: string
  painPointsText: string
  weights: IcpWeights
}

export const EMPTY_ICP_FORM: IcpFormState = {
  industriesText: 'SaaS',
  geographiesText: 'US',
  personasText: 'RevOps',
  painPointsText: '',
  weights: { ...DEFAULT_ICP_WEIGHTS },
}

export function joinList(values?: string[]) {
  return (values ?? []).join(', ')
}

export function parseCommaList(value: string) {
  return value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
}

export function toIcpPayload(form: IcpFormState) {
  return {
    industries: parseCommaList(form.industriesText),
    geographies: parseCommaList(form.geographiesText),
    target_personas: parseCommaList(form.personasText),
    pain_points: parseCommaList(form.painPointsText),
    employee_band: 'mid-market',
    revenue_band: 'mid-market',
    scoring_weights: form.weights,
  }
}

export function weightTotal(weights: IcpWeights) {
  return Object.values(weights).reduce((sum, value) => sum + value, 0)
}

export function weightsAreValid(weights: IcpWeights) {
  return Math.abs(weightTotal(weights) - 1) <= 0.01
}

export function formFromIcpDetail(detail: Record<string, unknown>): IcpFormState {
  const account = (detail.account_criteria ?? {}) as Record<string, unknown>
  const persona = (detail.persona_criteria ?? {}) as Record<string, unknown>
  const scoring = detail.scoring_weights as Partial<IcpWeights> | undefined

  return {
    industriesText: joinList(account.industries as string[]),
    geographiesText: joinList(account.geographies as string[]),
    personasText: joinList(persona.target_personas as string[]),
    painPointsText: joinList(detail.pain_points as string[]),
    weights: { ...DEFAULT_ICP_WEIGHTS, ...scoring },
  }
}
