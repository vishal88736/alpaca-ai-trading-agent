import { NavLink } from "react-router-dom";
import { useSession } from "../../context/SessionContext";
import { useTheme } from "../../context/ThemeContext";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: "📊" },
  { to: "/strategy", label: "Strategy", icon: "⚡" },
  { to: "/assets", label: "Assets", icon: "🪙" },
  { to: "/automation", label: "Automation", icon: "🤖" },
  { to: "/research", label: "Research", icon: "🔬" },
  { to: "/agents", label: "Agents", icon: "🧠" },
  { to: "/decisions", label: "Decision Log", icon: "📜" },
];

export function TopNav() {
  const { connected, disconnect } = useSession();
  const { theme, toggle } = useTheme();

  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 28px",
        borderBottom: "1px solid var(--hairline)",
        background: "rgba(5, 7, 14, 0.82)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
        <NavLink to="/dashboard" style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 26,
              height: 26,
              borderRadius: 8,
              background: "linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 14px rgba(99, 102, 241, 0.45)",
            }}
          >
            <span style={{ fontSize: 13, color: "#fff", fontWeight: 800 }}>⚡</span>
          </div>
          <span style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 15.5, letterSpacing: "-0.02em" }}>
            SIGNAL<span style={{ color: "var(--accent-strong)" }}>/</span>TERMINAL
          </span>
        </NavLink>

        <nav style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontSize: 13,
                fontWeight: isActive ? 600 : 500,
                padding: "7px 14px",
                borderRadius: "var(--radius-sm)",
                color: isActive ? "#ffffff" : "var(--text-secondary)",
                background: isActive ? "rgba(99, 102, 241, 0.16)" : "transparent",
                border: isActive ? "1px solid rgba(99, 102, 241, 0.35)" : "1px solid transparent",
                boxShadow: isActive ? "0 0 12px rgba(99, 102, 241, 0.2)" : "none",
                transition: "all 0.15s ease",
              })}
            >
              <span style={{ fontSize: 13, opacity: 0.85 }}>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <button
          className="btn btn--ghost btn--sm"
          onClick={toggle}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          style={{ fontSize: 14, padding: "5px 10px" }}
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
        <span className="badge badge--paper">
          <span className="dot dot--pulse" />
          Paper Trading
        </span>
        {connected ? (
          <button
            className="btn btn--ghost btn--sm"
            onClick={disconnect}
            style={{ fontSize: 12, padding: "5px 12px" }}
          >
            Disconnect
          </button>
        ) : (
          <NavLink to="/connect" className="btn btn--primary btn--sm" style={{ fontSize: 12, padding: "5px 14px" }}>
            Connect Alpaca
          </NavLink>
        )}
      </div>
    </header>
  );
}

