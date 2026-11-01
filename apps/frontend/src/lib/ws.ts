import { useEffect, useMemo } from "react";

import { apiBaseUrl } from "./api";

export function useScenarioWebSocket(
  scenarioId: number | null,
  onEvent: (event: {
    event_type?: string;
    scenario_id?: number;
    entity_type?: string;
    entity_id?: number;
    action?: string;
    new_version?: number;
    changed_at?: string;
  }) => void,
) {
  const wsUrl = useMemo(() => {
    if (!scenarioId) return null;
    const base = apiBaseUrl() || window.location.origin;
    const url = new URL(`/ws/scenarios/${scenarioId}`, base);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    return url.toString();
  }, [scenarioId]);

  useEffect(() => {
    if (!wsUrl) return;

    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        onEvent(payload);
      } catch {
        // Ignore malformed events.
      }
    };

    const pingTimer = window.setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 15000);

    return () => {
      window.clearInterval(pingTimer);
      ws.close();
    };
  }, [wsUrl, onEvent]);
}
