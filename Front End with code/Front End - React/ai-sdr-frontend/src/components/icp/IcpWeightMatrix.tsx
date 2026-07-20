import { cn } from '../../lib/utils'
import { WsRange } from '../workspace'
import { ICP_WEIGHT_META, type IcpWeightKey, type IcpWeights } from './icpConstants'
import { weightTotal, weightsAreValid } from './icpUtils'

type IcpWeightMatrixProps = {
  weights: IcpWeights
  onChange: (key: IcpWeightKey, value: number) => void
  disabled?: boolean
}

export function IcpWeightMatrix({ weights, onChange, disabled }: IcpWeightMatrixProps) {
  const total = weightTotal(weights)
  const valid = weightsAreValid(weights)

  return (
    <section className="sdr-icp-weight" aria-labelledby="icp-weight-heading">
      <header className="sdr-icp-weight__header">
        <div>
          <h3 id="icp-weight-heading" className="sdr-icp-section__title">
            Scoring weights
          </h3>
          <p className="sdr-icp-section__desc">Tune how discovery ranks account and persona fit.</p>
        </div>
        <div className={cn('sdr-icp-weight__total', valid ? 'sdr-icp-weight__total--ok' : 'sdr-icp-weight__total--warn')}>
          <span className="sdr-icp-weight__total-label">Total</span>
          <span className="sdr-icp-weight__total-value">{Math.round(total * 100)}%</span>
        </div>
      </header>

      <div className="sdr-icp-weight__grid">
        {(Object.keys(weights) as IcpWeightKey[]).map((key) => {
          const meta = ICP_WEIGHT_META[key]
          const value = weights[key]

          return (
            <div key={key} className="sdr-icp-weight__row">
              <WsRange
                id={`icp-weight-${key}`}
                value={value}
                min={0}
                max={1}
                step={0.05}
                disabled={disabled}
                label={meta.label}
                hint={meta.hint}
                onChange={(next) => onChange(key, next)}
              />
            </div>
          )
        })}
      </div>

      {!valid ? (
        <p className="sdr-icp-weight__warning" role="status">
          Weights must sum to 100% before validate or save.
        </p>
      ) : null}
    </section>
  )
}
