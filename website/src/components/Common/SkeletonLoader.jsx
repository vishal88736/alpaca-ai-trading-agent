export function SkeletonLine({ width = "100%", height = 14 }) {
  return <div className="skeleton" style={{ width, height, borderRadius: 4 }} />;
}

export function SkeletonBlock({ height = 120 }) {
  return <div className="skeleton" style={{ width: "100%", height, borderRadius: "var(--radius-md)" }} />;
}

export function SkeletonCard() {
  return (
    <div className="card" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 10 }}>
      <SkeletonLine width="40%" height={11} />
      <SkeletonLine width="65%" height={24} />
    </div>
  );
}
