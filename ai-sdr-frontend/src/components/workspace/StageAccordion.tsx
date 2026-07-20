import type { ReactNode } from 'react'

export function StageAccordion({
  title,
  children,
  defaultOpen = false,
}: {
  title: string
  children: ReactNode
  defaultOpen?: boolean
}) {
  return (
    <details className="ws-stage-accordion" open={defaultOpen}>
      <summary>{title}</summary>
      <div className="ws-stage-accordion__body">{children}</div>
    </details>
  )
}
