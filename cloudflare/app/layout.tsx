import type { ReactNode } from "react";

export const metadata = {
  title: "AgentForge",
  description: "Build smarter teams with AI",
  icons: {
    icon: "/brand/agentforge-icon.svg",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
