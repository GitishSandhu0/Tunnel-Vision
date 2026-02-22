import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-geist",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Tunnel Vision – Map Your Mind. Explore the Unknown.",
    template: "%s | Tunnel Vision",
  },
  description:
    "Tunnel Vision maps your knowledge, discovers hidden connections, and recommends what to learn next using AI-powered knowledge graphs.",
  keywords: [
    "knowledge graph",
    "AI",
    "learning",
    "mind mapping",
    "SaaS",
    "Tunnel Vision",
  ],
  authors: [{ name: "Tunnel Vision" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    title: "Tunnel Vision",
    description: "Map your mind. Explore the unknown.",
    siteName: "Tunnel Vision",
  },
  twitter: {
    card: "summary_large_image",
    title: "Tunnel Vision",
    description: "Map your mind. Explore the unknown.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  themeColor: "#0a0a0f",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} dark`} suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
      </head>
      <body className="bg-obsidian text-white antialiased font-geist min-h-screen">
        {children}
      </body>
    </html>
  );
}
