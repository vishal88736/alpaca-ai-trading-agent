export function EmptyState({ title, description, action }) {
  return (
    <div
      style={{
        textAlign: "center",
        padding: "40px 20px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 8,
      }}
    >
      <div style={{ fontFamily: "var(--font-display)", fontSize: 16, fontWeight: 600 }}>{title}</div>
      {description && <p style={{ maxWidth: 340, fontSize: 13 }}>{description}</p>}
      {action && <div style={{ marginTop: 10 }}>{action}</div>}
    </div>
  );
}

export function ErrorState({ message = "Data unavailable" }) {
  return (
    <div
      style={{
        padding: "16px",
        borderRadius: "var(--radius-md)",
        background: "var(--sell-soft)",
        border: "1px solid rgba(255,93,118,0.25)",
        color: "var(--sell)",
        fontSize: 13,
      }}
    >
      {message}
    </div>
  );
}
