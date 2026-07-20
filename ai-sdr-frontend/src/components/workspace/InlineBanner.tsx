import { AlertCircle, RefreshCw } from 'lucide-react'
import { cn } from '../../lib/cn'

type InlineBannerProps = {
  message: string
  onRetry?: () => void
  variant?: 'error' | 'info'
}

export function InlineBanner({ message, onRetry, variant = 'error' }: InlineBannerProps) {
  return (
    <div
      role="alert"
      className={cn(
        'ws-banner',
        variant === 'error' ? 'ws-banner--error' : 'ws-banner--info',
      )}
    >
      <span className="flex items-center gap-2">
        <AlertCircle className="h-4 w-4 shrink-0" aria-hidden />
        {message}
      </span>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="ws-focus-ring touch-target inline-flex items-center gap-1 rounded-md px-2 py-1.5 text-xs font-medium hover:bg-black/5"
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden />
          Retry
        </button>
      ) : null}
    </div>
  )
}
