import { Building2, Globe2, Target, Zap } from 'lucide-react'
import { WsCommaField } from '../workspace'
import { ICP_CRITERIA_PRESETS } from './icpConstants'
import type { IcpFormState } from './icpUtils'

type IcpCriteriaFormProps = {
  form: IcpFormState
  onChange: (patch: Partial<IcpFormState>) => void
  disabled?: boolean
}

const CRITERIA_SECTIONS = [
  {
    key: 'industriesText' as const,
    id: 'icp-industries',
    label: 'Industries',
    icon: Building2,
    hint: 'Comma-separated verticals',
    placeholder: 'SaaS, B2B Software',
  },
  {
    key: 'geographiesText' as const,
    id: 'icp-geographies',
    label: 'Geographies',
    icon: Globe2,
    hint: 'Target regions and countries',
    placeholder: 'US, Canada',
  },
  {
    key: 'personasText' as const,
    id: 'icp-personas',
    label: 'Target personas',
    icon: Target,
    hint: 'Titles and buying roles',
    placeholder: 'RevOps, VP Sales',
  },
  {
    key: 'painPointsText' as const,
    id: 'icp-pain',
    label: 'Pain points',
    icon: Zap,
    hint: 'Problems your offer solves',
    placeholder: 'Pipeline visibility, forecast accuracy',
  },
]

export function IcpCriteriaForm({ form, onChange, disabled }: IcpCriteriaFormProps) {
  return (
    <section className="sdr-icp-criteria" aria-labelledby="icp-criteria-heading">
      <header className="sdr-icp-section__header">
        <div>
          <h3 id="icp-criteria-heading" className="sdr-icp-section__title">
            Account & persona criteria
          </h3>
          <p className="sdr-icp-section__desc">Structured fields that feed discovery, scoring, and qualification.</p>
        </div>
      </header>

      <div className="sdr-icp-criteria__presets">
        <p className="sdr-icp-criteria__presets-label">Quick presets</p>
        <div className="sdr-icp-criteria__preset-list">
          {ICP_CRITERIA_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              className="sdr-icp-preset-chip ws-focus-ring"
              disabled={disabled}
              onClick={() =>
                onChange({
                  industriesText: preset.industries,
                  geographiesText: preset.geographies,
                  personasText: preset.personas,
                  painPointsText: preset.painPoints,
                })
              }
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <div className="sdr-icp-criteria__grid">
        {CRITERIA_SECTIONS.map(({ key, id, label, icon: Icon, hint, placeholder }) => (
          <article key={key} className="sdr-icp-criteria__card">
            <div className="sdr-icp-criteria__card-icon" aria-hidden>
              <Icon className="h-4 w-4" />
            </div>
            <WsCommaField
              id={id}
              label={label}
              value={form[key]}
              onChange={(value) => onChange({ [key]: value })}
              hint={hint}
              placeholder={placeholder}
              disabled={disabled}
            />
          </article>
        ))}
      </div>
    </section>
  )
}
