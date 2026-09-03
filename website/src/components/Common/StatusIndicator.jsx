const VARIANTS = {
  live: { color: "var(--buy)", pulse: true },
  running: { color: "var(--buy)", pulse: true },
  paused: { color: "var(--warning)", pulse: false },
  stopped: { color: "var(--text-muted)", pulse: false },
  idle: { color: "var(--text-muted)", pulse: false },
  error: { color: "var(--sell)", pulse: true },
  emergency_stopped: { color: "var(--sell)", pulse: false },
};

export function StatusIndicator({ state = "idle", label }) {
  const key = String(state).toLowerCase();
  const variant = VARIANTS[key] || VARIANTS.idle;

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        fontFamily: "var(--font-mono)",
        fontSize: 12,
        letterSpacing: "0.04em",
        color: variant.color,
      }}
    >
      <span className={`dot ${variant.pulse ? "dot--pulse" : ""}`} style={{ color: variant.color }} />
      {label || state.toUpperCase().replace(/_/g, " ")}
    </span>
  );
}
