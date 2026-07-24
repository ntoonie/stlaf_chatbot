export const metadata = {
  title: "STLAF | Philippine Labor Law AI Assistant",
  description: "AI-powered legal information assistant for Philippine labor law.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
