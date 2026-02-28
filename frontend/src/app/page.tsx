import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
      {/* Hero */}
      <div className="mb-4 w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-700 flex items-center justify-center text-white font-bold text-3xl shadow-2xl glow">
        N
      </div>
      <h1 className="text-5xl font-bold tracking-tight mb-4">
        <span className="gradient-text">NeuroTutor</span> AI
      </h1>
      <p className="text-lg text-gray-400 max-w-lg mb-10 leading-relaxed">
        Your adaptive learning companion. Personalized teaching, intelligent practice,
        real-time mastery tracking — all powered by Google Gemini.
      </p>

      {/* CTA Buttons */}
      <div className="flex gap-4">
        <Link
          href="/chat"
          className="px-8 py-3.5 rounded-full bg-gradient-to-r from-violet-600 to-purple-600 text-white font-semibold text-sm hover:from-violet-500 hover:to-purple-500 transition-smooth glow"
        >
          💬 Start Learning
        </Link>
        <Link
          href="/dashboard"
          className="px-8 py-3.5 rounded-full border border-white/10 text-gray-300 font-medium text-sm hover:bg-white/5 transition-smooth"
        >
          📊 View Dashboard
        </Link>
      </div>

      {/* Feature grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-16 max-w-3xl w-full">
        <FeatureCard emoji="🧠" title="Adaptive Tutor" desc="Explains concepts in your cognitive style" />
        <FeatureCard emoji="📈" title="Mastery Tracking" desc="5-tier progression from Beginner to Mastered" />
        <FeatureCard emoji="📅" title="Study Planner" desc="AI-generated spaced repetition schedules" />
      </div>
    </div>
  );
}

function FeatureCard({ emoji, title, desc }: { emoji: string; title: string; desc: string }) {
  return (
    <div className="glass-card p-5 text-center hover:border-violet-500/30 transition-smooth cursor-default">
      <div className="text-2xl mb-2">{emoji}</div>
      <h3 className="font-semibold text-white text-sm mb-1">{title}</h3>
      <p className="text-xs text-gray-400 leading-relaxed">{desc}</p>
    </div>
  );
}
