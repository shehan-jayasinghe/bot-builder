import { Outlet } from "react-router-dom";

import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";

export function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-shell__main">
        <Header />
        <main className="app-shell__content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
