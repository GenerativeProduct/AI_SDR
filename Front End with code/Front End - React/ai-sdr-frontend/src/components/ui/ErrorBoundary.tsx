import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from './Button'

type Props = { children: ReactNode }
type State = { error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('UI error:', error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="rounded-xl border border-danger/20 bg-danger-muted p-6 text-center">
          <p className="font-medium text-danger-foreground">Something went wrong</p>
          <p className="mt-2 text-sm text-danger-foreground/80">{this.state.error.message}</p>
          <Button className="mt-4" variant="secondary" onClick={() => this.setState({ error: null })}>
            Try again
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}
