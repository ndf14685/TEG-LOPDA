import { Component, type ErrorInfo, type ReactNode } from 'react';
import { playtestClient } from '../../services/playtest/playtestClient';

export class PlaytestBoundary extends Component<{ children: ReactNode }, { crashed: boolean }> {
  state = { crashed: false };

  componentDidCatch(error: Error, info: ErrorInfo): void {
    playtestClient.reportTechnical({
      category: 'other',
      title: `React crash: ${error.message}`,
      message: error.message,
      error_type: 'react-error-boundary',
      component: 'React',
      context: { stack: error.stack, componentStack: info.componentStack },
    });
    this.setState({ crashed: true });
  }

  render() {
    if (this.state.crashed) {
      return (
        <main className="flex min-h-screen items-center justify-center bg-war-950 p-6 text-stone-100">
          <section className="max-w-lg rounded-lg border border-red-700 bg-war-900 p-5">
            <h1 className="font-display text-xl text-red-200">Error de pantalla registrado</h1>
            <p className="mt-2 text-sm text-stone-300">Recargá para volver a la partida. El incidente quedó guardado en modo playtest.</p>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}
