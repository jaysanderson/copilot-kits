import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

// A route-level error boundary so a single page's render error degrades to a
// friendly, on-brand error state with a retry - never a frozen tab or a blank
// white screen (the Auto-co lesson: a demo must show an error state with a
// retry, not a dead-end). Wraps the composition so one page can never take the
// whole app down.
interface Props { children: ReactNode }
interface State { error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Surfaced in the console for QA; the UI stays friendly.
    console.error('[publisher] route render error:', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="mx-auto flex max-w-xl flex-col items-center gap-4 px-6 py-20 text-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-xl text-white" style={{ background: 'linear-gradient(155deg, var(--brand-strong), var(--brand))' }}>
            <AlertTriangle size={22} />
          </span>
          <div>
            <p className="font-display text-lg font-semibold text-ink-900 dark:text-ink-50">This view hit a snag</p>
            <p className="mt-1 text-sm text-ink-500">The claims desk could not render this screen. Reload to try again - your seeded claims are unchanged.</p>
          </div>
          <button type="button" onClick={() => { this.setState({ error: null }); location.reload(); }} className="btn btn-primary">
            <RotateCcw size={15} /> Reload the desk
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
