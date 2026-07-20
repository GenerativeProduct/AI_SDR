import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { ConversionFunnelChart } from './ConversionFunnelChart'
import { StageVolumeChart } from './StageVolumeChart'
import type { FunnelStage } from './ConversionFunnelChart'
import type { StageBarDatum } from './StageVolumeChart'

type PipelineAnalyticsPanelProps = {
  funnelStages: FunnelStage[]
  stageBars: StageBarDatum[]
  isLoading: boolean
}

export function PipelineAnalyticsPanel({
  funnelStages,
  stageBars,
  isLoading,
}: PipelineAnalyticsPanelProps) {
  return (
    <article className="sdr-dash-panel sdr-dash-panel--analytics">
      <header className="sdr-analytics-header">
        <div className="min-w-0">
          <p className="ws-heading-section">Pipeline analytics</p>
          <h2 className="sdr-dash-panel__title-lg">Funnel & module volume</h2>
          <p className="sdr-dash-panel__desc">
            Stage throughput and drop-off across your SDR progression.
          </p>
        </div>
        <Link to="/analytics" className="sdr-analytics-header__cta group">
          <span>Full analytics</span>
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden />
        </Link>
      </header>

      <div className="sdr-analytics-body">
        <section className="sdr-analytics-section sdr-analytics-section--primary">
          <div className="sdr-analytics-section__head">
            <h3 className="ws-heading-panel">Stage volume</h3>
            <p className="ws-heading-panel-sub">Active records per module</p>
          </div>
          <div className="sdr-analytics-section__chart">
            {isLoading ? (
              <div className="sdr-dash-chart-skeleton sdr-dash-chart-skeleton--bars" aria-busy />
            ) : (
              <StageVolumeChart data={stageBars} />
            )}
          </div>
        </section>

        <section className="sdr-analytics-section">
          <div className="sdr-analytics-section__head">
            <h3 className="ws-heading-panel">Conversion funnel</h3>
            <p className="ws-heading-panel-sub">Volume relative to peak stage — hover for detail</p>
          </div>
          <div className="sdr-analytics-section__chart">
            {isLoading ? (
              <div className="sdr-dash-chart-skeleton sdr-dash-chart-skeleton--tall" aria-busy />
            ) : (
              <ConversionFunnelChart stages={funnelStages} />
            )}
          </div>
        </section>
      </div>
    </article>
  )
}
