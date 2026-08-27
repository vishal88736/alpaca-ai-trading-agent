import { NavLink } from "react-router-dom";
import { useSession } from "../../context/SessionContext";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/strategy", label: "Strategy" },
  { to: "/assets", label: "Assets" },
  { to: "/automation", label: "Automation" },
  { to: "/decisions", label: "Decision Log" },
];

export function TopNav() {
  const { connected, disconnect } = useSession();

  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "14px 28px",
        borderBottom: "1px solid var(--hairline)",
        background: "var(--surface-glass)",
        backdropFilter: "blur(14px)",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
        <NavLink to="/dashboard" style={{ display: "flex", alignItems: "center", gap: 9 }}>
          <span
            style={{
              width: 9,
              height: 9,
              borderRadius: 2,
              background: "linear-gradient(135deg, var(--accent), var(--buy))",
              display: "inline-block",
            }}
          />
          <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 15, letterSpacing: "-0.01em" }}>
            SIGNAL<span style={{ color: "var(--accent)" }}>/</span>TERMINAL
          </span>
        </NavLink>

        <nav style={{ display: "flex", gap: 4 }}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                fontSize: 13,
                fontWeight: 500,
                padding: "7px 12px",
                borderRadius: 7,
                color: isActive ? "var(--text-primary)" : "var(--text-muted)",
                background: isActive ? "var(--surface-raised)" : "transparent",
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span className="badge badge--paper">
          <span className="dot dot--pulse" />
          Paper Trading
        </span>
        {connected && (
          <button className="btn btn--ghost btn--sm" onClick={disconnect}>
            Disconnect
          </button>
        )}
      </div>
    </header>
  );
}
