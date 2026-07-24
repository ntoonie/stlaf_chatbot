import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "STLAF | Philippine Labor Law AI Assistant",
  description: "AI-powered legal information assistant for Philippine labor law.",
};

// Runs BEFORE React hydrates - reads saved theme (or falls back to
// system preference on first visit) and sets it on <html> immediately,
// avoiding a flash of the wrong theme on load.
const themeInitScript = `
(function() {
  try {
    var stored = localStorage.getItem('stlaf-theme');
    var theme = stored || (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    document.documentElement.setAttribute('data-theme', theme);
  } catch (e) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
})();
`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    // suppressHydrationWarning is REQUIRED here, specifically on this
    // element - not a hack. The script above intentionally sets
    // data-theme on the client before React hydrates, which will
    // always differ from what the server rendered (the server has no
    // access to localStorage/matchMedia). This attribute tells React
    // "I know this one element's attributes will differ, that's
    // expected" - it does NOT suppress hydration warnings anywhere
    // else in the app, only on this specific <html> tag.
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
