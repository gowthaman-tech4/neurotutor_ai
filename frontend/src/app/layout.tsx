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
        <html lang="en" className="light" suppressHydrationWarning>
            <body className={`${inter.variable} ${geistMono.variable} antialiased bg-white text-gray-900 min-h-screen`}>
                {/* Top Navigation Bar */}
                <nav className="fixed top-0 left-0 right-0 z-50 glass-card" style={{ borderRadius: 0, borderTop: "none", borderLeft: "none", borderRight: "none" }}>
                    <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                        {/* Logo */}
                        <Link href="/" className="flex items-center gap-3 transition-smooth hover:opacity-80">
                            <img src="/logo.svg" alt="NeuroTutor AI Logo" className="w-10 h-10 object-contain" />
                            <span className="text-xl font-bold tracking-tight text-emerald-900">
                                Neuro<span className="gradient-text">Tutor</span> AI
                            </span>
                        </Link>

                        {/* Tab Navigation */}
                        <div className="flex items-center gap-1 bg-black/5 rounded-full p-1">
                            <NavTab href="/learn" label="Learn" />
                            <NavTab href="/chat" label="Chat" />
                            <NavTab href="/review" label="Review" />
                            <NavTab href="/dashboard" label="Dashboard" />
                        </div>

                        {/* Profile Badge */}
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-indigo-600 flex items-center justify-center text-gray-900 text-xs font-bold">
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
            className="px-5 py-2 rounded-full text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-black/10 transition-smooth"
        >
            {label}
        </Link>
    );
}
