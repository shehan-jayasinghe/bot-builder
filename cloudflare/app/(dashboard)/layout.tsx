import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { auth } from "@/auth";
import { Header } from "@/app/components/layout/Header";
import { Sidebar } from "@/app/components/layout/Sidebar";

import "../dashboard.css";

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const session = await auth();

  if (!session?.user) {
    redirect("/signin");
  }

  return (
    <div className="app-shell">
      <Sidebar
        organizationName="Organization"
        userName={session.user.name ?? "User"}
        userEmail={session.user.email ?? ""}
      />
      <div className="app-shell__main">
        <Header />
        <main className="app-shell__content">{children}</main>
      </div>
    </div>
  );
}
