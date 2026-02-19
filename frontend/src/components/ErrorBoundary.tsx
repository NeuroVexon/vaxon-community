import { Component, type ReactNode, type ErrorInfo } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-nv-black flex items-center justify-center p-8">
          <div className="max-w-md w-full bg-nv-black-200 rounded-2xl border border-red-500/20 p-8 text-center">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <h1 className="text-xl font-bold text-white mb-2">Something went wrong</h1>
            <p className="text-sm text-gray-400 mb-6">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <button
              onClick={this.handleReset}
              className="px-6 py-3 bg-nv-accent text-nv-black font-semibold rounded-xl
                         hover:bg-opacity-90 flex items-center justify-center gap-2 mx-auto
                         shadow-nv-glow transition-all"
            >
              <RefreshCw className="w-5 h-5" />
              Retry
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
