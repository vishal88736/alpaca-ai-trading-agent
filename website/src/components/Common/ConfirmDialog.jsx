export function ConfirmDialog({ open, title, description, confirmLabel = "Confirm", danger, onConfirm, onCancel }) {
  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(6,7,10,0.7)",
        backdropFilter: "blur(3px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1100,
        padding: 20,
      }}
      onClick={onCancel}
    >
      <div
        className="card"
        style={{ maxWidth: 420, width: "100%", padding: 24 }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontSize: 18, marginBottom: 10 }}>{title}</h3>
        <p style={{ fontSize: 13.5, marginBottom: 20 }}>{description}</p>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <button className="btn btn--ghost btn--sm" onClick={onCancel}>
            Cancel
          </button>
          <button className={`btn btn--sm ${danger ? "btn--danger" : "btn--primary"}`} onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
