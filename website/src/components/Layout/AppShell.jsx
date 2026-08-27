import { TopNav } from "./TopNav";
import { TickerRail } from "./TickerRail";

export function AppShell({ children, tickerItems = [] }) {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <TickerRail items={tickerItems} />
      <TopNav />
      <main style={{ flex: 1, padding: "28px", maxWidth: 1440, width: "100%", margin: "0 auto" }}>{children}</main>
    </div>
  );
}
