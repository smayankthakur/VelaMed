import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VelaMed — DPDP & security check for hospital websites",
  description:
    "Free passive check of your hospital or clinic website for DPDP readiness and basic security — in under a minute.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
