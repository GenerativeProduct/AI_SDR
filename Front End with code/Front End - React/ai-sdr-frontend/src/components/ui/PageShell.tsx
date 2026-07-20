import type { ReactNode } from 'react'
import { ErrorBoundary } from './ErrorBoundary'
import { PageLayout } from '../layout/PageLayout'

export function PageShell({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <PageLayout>{children}</PageLayout>
    </ErrorBoundary>
  )
}
