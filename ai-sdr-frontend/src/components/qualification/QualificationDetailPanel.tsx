import { useState } from 'react'
import type { BANTAssessment, FrameworkCriterion, MEDDICAssessment, QualificationResult } from '../../api/types'
import { QualificationBadge } from '../workspace'
import { formatPercent } from './qualificationUtils'

type QualificationDetailPanelProps = {
  row: QualificationResult
}

function CriteriaList({ criteria }: { criteria: FrameworkCriterion[] }) {
  return (
    <ul className="sdr-qualification__criteria-list">
      {criteria.map((criterion) => (
        <li key={criterion.name} className="sdr-qualification__criterion">
          <div className="sdr-qualification__criterion__head">
            <span className="sdr-qualification__criterion__name">{criterion.name}</span>
            <span className="sdr-qualification__criterion__score">{Math.round(criterion.score)}</span>
          </div>
          <div className="sdr-qualification__criterion__track" aria-hidden>
            <span className="sdr-qualification__criterion__fill" style={{ width: `${Math.min(100, criterion.score)}%` }} />
          </div>
          {criterion.evidence?.length ? (
            <ul className="sdr-qualification__evidence-list">
              {criterion.evidence.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </li>
      ))}
    </ul>
  )
}

function bantCriteria(assessment: BANTAssessment) {
  return [assessment.budget, assessment.authority, assessment.need, assessment.timeline]
}

function meddicCriteria(assessment: MEDDICAssessment) {
  return [
    assessment.metrics,
    assessment.economic_buyer,
    assessment.decision_criteria,
    assessment.decision_process,
    assessment.identified_pain,
    assessment.champion,
  ]
}

export function QualificationDetailPanel({ row }: QualificationDetailPanelProps) {
  const [framework, setFramework] = useState<'bant' | 'meddic'>(row.bant ? 'bant' : 'meddic')

  return (
    <aside className="sdr-qualification__detail">
      <header className="sdr-qualification__detail-header">
        <div>
          <p className="ws-heading-section">Qualification brief</p>
          <h2 className="sdr-qualification__pane-title">
            {row.contact_name} @ {row.company_name}
          </h2>
          <p className="sdr-qualification__pane-desc">{row.next_action}</p>
        </div>
        <QualificationBadge tier={row.qualification_status} />
      </header>

      <div className="sdr-qualification__detail-body">
        <div className="sdr-qualification__score-grid">
          <div className="sdr-qualification__score-card">
            <span className="sdr-qualification__score-value">{Math.round(row.qualification_score)}</span>
            <span className="sdr-qualification__score-label">Qual score</span>
          </div>
          <div className="sdr-qualification__score-card">
            <span className="sdr-qualification__score-value">{formatPercent(row.ml_qualification_probability)}</span>
            <span className="sdr-qualification__score-label">ML probability</span>
          </div>
          <div className="sdr-qualification__score-card">
            <span className="sdr-qualification__score-value">{row.qualification_tier}</span>
            <span className="sdr-qualification__score-label">Tier</span>
          </div>
        </div>

        <div className="sdr-qualification__framework-tabs" role="tablist" aria-label="Qualification framework">
          <button
            type="button"
            role="tab"
            aria-selected={framework === 'bant'}
            className={framework === 'bant' ? 'sdr-qualification__framework-tab sdr-qualification__framework-tab--active' : 'sdr-qualification__framework-tab'}
            onClick={() => setFramework('bant')}
          >
            BANT {row.bant ? `· ${Math.round(row.bant.score)}` : ''}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={framework === 'meddic'}
            className={framework === 'meddic' ? 'sdr-qualification__framework-tab sdr-qualification__framework-tab--active' : 'sdr-qualification__framework-tab'}
            onClick={() => setFramework('meddic')}
          >
            MEDDIC {row.meddic ? `· ${Math.round(row.meddic.score)}` : ''}
          </button>
        </div>

        {framework === 'bant' ? (
          row.bant ? <CriteriaList criteria={bantCriteria(row.bant)} /> : <p className="sdr-qualification__empty-framework">No BANT assessment data.</p>
        ) : row.meddic ? (
          <CriteriaList criteria={meddicCriteria(row.meddic)} />
        ) : (
          <p className="sdr-qualification__empty-framework">No MEDDIC assessment data.</p>
        )}

        {row.reasoning?.length ? (
          <section className="sdr-qualification__detail-section">
            <h3 className="sdr-qualification__detail-section__title">Reasoning</h3>
            <ul className="sdr-qualification__bullet-list">
              {row.reasoning.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {row.missing_information?.length ? (
          <section className="sdr-qualification__detail-section sdr-qualification__detail-section--warn">
            <h3 className="sdr-qualification__detail-section__title">Missing information</h3>
            <ul className="sdr-qualification__bullet-list">
              {row.missing_information.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </aside>
  )
}
