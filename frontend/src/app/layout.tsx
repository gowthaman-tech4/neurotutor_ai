import type { Metadata } from "next";
import { Inter, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NeuroTutor AI — Adaptive Learning Platform",
  description: "Personalized AI tutoring with mastery tracking and study planning.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} ${geistMono.variable} antialiased`}>
        {/* Top Navigation Bar */}
        <nav className="fixed top-0 left-0 right-0 z-50 glass-card" style={{ borderRadius: 0, borderTop: "none", borderLeft: "none", borderRight: "none" }}>
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3 transition-smooth hover:opacity-80">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-700 flex items-center justify-center text-white font-bold text-sm shadow-lg">
                N
              </div>
              <span className="text-lg font-semibold tracking-tight text-white">
                Neuro<span className="gradient-text">Tutor</span> AI
              </span>
            </Link>

            {/* Tab Navigation */}
            <div className="flex items-center gap-1 bg-white/5 rounded-full p-1">
              <NavTab href="/learn" label="📚 Learn" />
              <NavTab href="/chat" label="💬 Chat" />
              <NavTab href="/review" label="📝 Review" />
              <NavTab href="/dashboard" label="📊 Dashboard" />
            </div>

            {/* Profile Badge */}
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold">
                T
              </div>
              <span className="hidden sm:inline">TestStudent</span>
            </div>
          </div>
        </nav>

        {/* Page Content */}
        <main className="pt-20 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}

function NavTab({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="px-5 py-2 rounded-full text-sm font-medium text-gray-300 hover:text-white hover:bg-white/10 transition-smooth"
    >
      {label}
    </Link>
  );
}
