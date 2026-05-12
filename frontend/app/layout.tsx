import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MagicGPT — Unofficial MTG card assistant",
  description:
    "Chat with an AI to find Magic: The Gathering cards and build Commander decks. Unofficial fan project; not affiliated with Wizards of the Coast.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
