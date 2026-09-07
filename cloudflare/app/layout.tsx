import type { ReactNode } from "react";

export const metadata = {
  title: "Bot Builder",
  description: "Bot Builder on Cloudflare Workers",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
