import Link from "next/link";

export default function Home() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
            {/* Hero */}
            <div className="mb-4">
                <img src="/logo.png" alt="NeuroTutor AI Logo" className="w-24 h-24 object-contain mx-auto" />
            </div>
            <h1 className="text-5xl font-bold tracking-tight mb-4">
                <span className="gradient-text">NeuroTutor</span> AI
            </h1>
            <p className="text-lg text-gray-600 max-w-lg mb-10 leading-relaxed">
                Your adaptive learning companion. Personalized teaching, intelligent practice,
                real-time mastery tracking — all powered by Google Gemini.
            </p>

            {/* CTA Buttons */}
            <div className="flex gap-4">
                <Link
                    href="/chat"
                    className="px-8 py-3.5 rounded-full bg-gradient-to-r from-emerald-600 to-green-600 text-gray-900 font-semibold text-sm hover:from-emerald-500 hover:to-green-500 transition-smooth glow"
                >
                    Start Learning
                </Link>
                <Link
                    href="/dashboard"
                    className="px-8 py-3.5 rounded-full border border-black/10 text-gray-700 font-medium text-sm hover:bg-black/5 transition-smooth"
                >
                    View Dashboard
                </Link>
            </div>

            {/* Feature grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-16 max-w-3xl w-full">
                <FeatureCard title="Adaptive Tutor" desc="Explains concepts in your cognitive style" />
                <FeatureCard title="Mastery Tracking" desc="5-tier progression from Beginner to Mastered" />
                <FeatureCard title="Study Planner" desc="AI-generated spaced repetition schedules" />
            </div>
        </div>
    );
}

function FeatureCard({ title, desc }: { title: string; desc: string }) {
    return (
        <div className="glass-card p-5 text-center hover:border-emerald-500/30 transition-smooth cursor-default">
            <div className="h-6 mb-2 flex items-center justify-center text-emerald-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            <h3 className="font-semibold text-gray-900 text-sm mb-1">{title}</h3>
            <p className="text-xs text-gray-600 leading-relaxed">{desc}</p>
        </div>
    );
}
