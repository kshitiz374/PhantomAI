import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PHANTOM — The Ghost in Your Machine",
  description: "Privacy-first fictional digital archaeology investigation",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen grain">{children}</body>
    </html>
  );
}
