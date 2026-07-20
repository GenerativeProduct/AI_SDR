import { ArrowRight, Lightbulb, Radio, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { EnrichmentResult } from '../../api/types'
import { StatusBadge } from '../workspace'
import { formatConfidence } from './enrichmentUtils'

type EnrichmentDetailPanelProps = {
  result: EnrichmentResult
}

export function EnrichmentDetailPanel({ result }: EnrichmentDetailPanelProps) {
  return (
    <aside className="sdr-enrichment__detail">
      <header className="sdr-enrichment__detail-header">
        <div>
          <p className="ws-heading-section">Brief</p>
          <h2 className="sdr-enrichment__pane-title">{result.company_name}</h2>
          <p className="sdr-enrichment__pane-desc">{result.recommended_next_action}</p>
        </div>
        <StatusBadge status={result.status} />
      </header>

      <div className="sdr-enrichment__detail-body">
        <div className="sdr-enrichment__confidence-card">
          <span className="sdr-enrichment__confidence-value">{formatConfidence(result.confidence_score)}</span>
          <span className="sdr-enrichment__confidence-label">Confidence score</span>
        </div>

        <section className="sdr-enrichment__detail-section">
          <h3 className="sdr-enrichment__detail-section__title">Company summary</h3>
          <p className="sdr-enrichment__detail-section__body">{result.company_summary || 'No summary available.'}</p>
        </section>

        {result.pain_point_hypotheses?.length ? (
          <section className="sdr-enrichment__detail-section">
            <h3 className="sdr-enrichment__detail-section__title">
              <Lightbulb className="h-4 w-4" aria-hidden />
              Pain point hypotheses
            </h3>
            <ul className="sdr-enrichment__bullet-list">
              {result.pain_point_hypotheses.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {result.personalization_angles?.length ? (
          <section className="sdr-enrichment__detail-section">
            <h3 className="sdr-enrichment__detail-section__title">
              <Sparkles className="h-4 w-4" aria-hidden />
              Personalization angles
            </h3>
            <ul className="sdr-enrichment__bullet-list">
              {result.personalization_angles.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {result.signals?.length ? (
          <section className="sdr-enrichment__detail-section">
            <h3 className="sdr-enrichment__detail-section__title">
              <Radio className="h-4 w-4" aria-hidden />
              Signals
            </h3>
            <ul className="sdr-enrichment__signal-list">
              {result.signals.map((signal, index) => (
                <li key={`${signal.type}-${index}`} className="sdr-enrichment__signal">
                  <div className="sdr-enrichment__signal__head">
                    <span className="sdr-enrichment__signal__type">{signal.type}</span>
                    <span className="sdr-enrichment__signal__confidence">{formatConfidence(signal.confidence)}</span>
                  </div>
                  <p className="sdr-enrichment__signal__detail">{signal.detail}</p>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <div className="sdr-enrichment__detail-actions">
          <Link to="/intelligence" className="ws-btn ws-btn--secondary w-full">
            Open intelligence
            <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
          <Link to="/qualification" className="ws-btn ws-btn--primary w-full">
            Qualify prospects
            <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
        </div>
      </div>
    </aside>
  )
}
