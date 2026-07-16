import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Philippine Labor Law Chatbot",
  description: "AI-powered legal information assistant for Philippine labor law.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
