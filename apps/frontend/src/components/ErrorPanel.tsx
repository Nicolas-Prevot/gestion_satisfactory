import { useMemo } from "react";

import { useErrorStore } from "../features/errorStore";

export function ErrorPanel() {
  const latestError = useErrorStore((state) => state.latestError);
  const clearError = useErrorStore((state) => state.clearError);

  const title = useMemo(() => {
    if (!latestError) return null;
    return latestError.error_type ? `${latestError.error_type}: ${latestError.message ?? ""}` : latestError.message;
  }, [latestError]);

  if (!latestError) {
    return null;
  }

  return (
    <section className="error-panel">
      <header>
        <strong>Debug Error</strong>
        <button type="button" onClick={clearError}>
          Dismiss
        </button>
      </header>
      <p>{title}</p>
      {latestError.trace_id ? <p className="trace-id">Trace ID: {latestError.trace_id}</p> : null}
      {latestError.stack ? (
        <details>
          <summary>Stack trace</summary>
          <pre>{latestError.stack}</pre>
        </details>
      ) : null}
    </section>
  );
}
