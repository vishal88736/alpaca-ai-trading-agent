import { useEffect, useRef, useState } from "react";

/**
 * Connects to the backend's /ws/live endpoint for live automation status
 * pushes. Falls back gracefully — if the socket can't connect (e.g. backend
 * not running), `connected` stays false and callers should keep using
 * polling/REST for that data instead of blocking on this.
 */
export function useLiveAutomationStatus(sessionId) {
  const [status, setStatus] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!sessionId) return undefined;

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${protocol}://${window.location.host}/ws/live?session_id=${encodeURIComponent(sessionId)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (event) => {
      try {
        setStatus(JSON.parse(event.data));
      } catch {
        /* ignore malformed frame */
      }
    };

    return () => {
      ws.close();
    };
  }, [sessionId]);

  return { status, connected };
}
