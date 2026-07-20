import { CheckCircle2, Loader2, Save, Sparkles, Wand2 } from 'lucide-react'
import type { ICPValidationResult } from '../../api/types'
import { cn } from '../../lib/utils'
import { WsSwitch } from '../workspace'
import { IcpCriteriaForm } from './IcpCriteriaForm'
import { IcpWeightMatrix } from './IcpWeightMatrix'
import type { IcpFormState } from './icpUtils'
import type { IcpWeightKey } from './icpConstants'
import { weightsAreValid } from './icpUtils'

type IcpEditorPanelProps = {
  form: IcpFormState
  onChange: (patch: Partial<IcpFormState>) => void
  onWeightChange: (key: IcpWeightKey, value: number) => void
  useLlm: boolean
  onUseLlmChange: (value: boolean) => void
  selectedIcpId: string | null
  isLoadingDetail: boolean
  validation: ICPValidationResult | null
  onValidate: () => void
  onSuggest: () => void
  onSave: () => void
  onUpdate: () => void
  validatePending: boolean
  suggestPending: boolean
  savePending: boolean
  updatePending: boolean
}

export function IcpEditorPanel({
  form,
  onChange,
  onWeightChange,
  useLlm,
  onUseLlmChange,
  selectedIcpId,
  isLoadingDetail,
  validation,
  onValidate,
  onSuggest,
  onSave,
  onUpdate,
  validatePending,
  suggestPending,
  savePending,
  updatePending,
}: IcpEditorPanelProps) {
  const validWeights = weightsAreValid(form.weights)
  const busy = validatePending || suggestPending || savePending || updatePending

  return (
    <section className="sdr-icp__editor">
      <header className="sdr-icp__editor-header">
        <div>
          <p className="ws-heading-section">Editor</p>
          <h2 className="sdr-icp__pane-title">{selectedIcpId ? 'Edit ICP definition' : 'New ICP definition'}</h2>
          <p className="sdr-icp__pane-desc">
            Structured criteria and scoring weights used across discovery and qualification.
          </p>
        </div>
        <div className="sdr-icp__editor-status" aria-live="polite">
          <span className={cn('sdr-icp__status-chip', validation && 'sdr-icp__status-chip--on')}>
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
            {validation ? validation.status : 'Draft'}
          </span>
        </div>
      </header>

      <div className="sdr-icp__editor-body">
        {isLoadingDetail ? (
          <div className="sdr-icp__editor-loading" aria-busy>
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
            Loading ICP version…
          </div>
        ) : (
          <>
            <IcpCriteriaForm form={form} onChange={onChange} disabled={busy} />
            <IcpWeightMatrix weights={form.weights} onChange={onWeightChange} disabled={busy} />

            <div className="sdr-icp__editor-toolbar">
              <WsSwitch
                id="icp-use-llm"
                checked={useLlm}
                onChange={onUseLlmChange}
                disabled={busy}
                label="Use Ollama for suggestions"
                description="Enable local LLM-assisted persona and pain-point suggestions."
              />
              <div className="sdr-icp__editor-actions">
                <button
                  type="button"
                  className="ws-btn ws-btn--secondary"
                  onClick={onValidate}
                  disabled={!validWeights || busy}
                >
                  {validatePending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <CheckCircle2 className="h-4 w-4" aria-hidden />}
                  Validate
                </button>
                <button type="button" className="ws-btn ws-btn--secondary" onClick={onSuggest} disabled={busy}>
                  {suggestPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Sparkles className="h-4 w-4" aria-hidden />}
                  Suggest
                </button>
                <button
                  type="button"
                  className="ws-btn ws-btn--primary"
                  onClick={onSave}
                  disabled={!validWeights || busy}
                >
                  {savePending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Save className="h-4 w-4" aria-hidden />}
                  Save new
                </button>
                {selectedIcpId ? (
                  <button
                    type="button"
                    className="ws-btn ws-btn--primary"
                    onClick={onUpdate}
                    disabled={!validWeights || busy}
                  >
                    {updatePending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Wand2 className="h-4 w-4" aria-hidden />}
                    Update selected
                  </button>
                ) : null}
              </div>
            </div>

            {validation?.warnings?.length ? (
              <div className="sdr-icp__validation-card">
                <p className="ws-heading-section">Validation notes</p>
                <ul className="sdr-icp__validation-list">
                  {validation.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        )}
      </div>
    </section>
  )
}
