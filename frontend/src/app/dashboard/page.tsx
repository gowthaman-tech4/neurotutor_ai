"use client";

import { useState, useEffect } from "react";

const API_URL = "http://localhost:8000/api/engine/route";
const TEST_USER_ID = "8b40ebcf-92aa-43a2-8def-bee49247cebc";

interface MasteryData {
  mastery_level: string;
  confidence_score: number;
}

// Old LLM-based plan types (kept for backward compat)
interface DayPlan {
  day: number;
  focus_topics: string[];
  learning_mode?: string;
  recommended_activities: string[];
}

interface StudyPlan {
  engine?: string;
  plan_duration_days?: number;
  strategic_advice?: string;
  daily_schedule?: DayPlan[];
  error_fallback?: string;
}

// Smart planner types
interface SmartActivity {
  topic: string;
  activity: string;
  duration_min: number;
  mastery: number | null;
  forgetting_risk: number | null;
}

interface SmartDayPlan {
  date: string;
  day_label: string;
  is_exam_mode: boolean;
  total_minutes: number;
  activities: SmartActivity[];
}

interface SmartTopicInfo {
  topic_name: string;
  mastery_score: number;
  mastery_level: string;
  forgetting_risk: number;
  next_review_days: number;
  priority: number;
}

interface SmartPlanResult {
  engine?: string;
  exam_date?: string;
  days_until_exam?: number;
  is_exam_mode?: boolean;
  readiness?: {
    current_score: number;
    projected_score: number;
    confidence: string;
    total_topics: number;
    weak_topics: number;
  };
  topic_analysis?: SmartTopicInfo[];
  daily_plans?: SmartDayPlan[];
  priority_suggestions?: string[];
  error?: string;
}

const TIER_STYLES: Record<string, { color: string; bg: string; label: string; progress: number }> = {
  beginner: { color: "text-slate-400", bg: "bg-slate-400/15", label: "Beginner", progress: 10 },
  learning: { color: "text-teal-400", bg: "bg-teal-400/15", label: "Learning", progress: 35 },
  improving: { color: "text-yellow-400", bg: "bg-yellow-400/15", label: "Improving", progress: 60 },
  strong: { color: "text-emerald-400", bg: "bg-emerald-400/15", label: "Strong", progress: 85 },
  mastered: { color: "text-green-400", bg: "bg-green-400/15", label: "Mastered", progress: 100 },
};

const EXAM_OPTIONS = [
  { key: "school", label: "🎒 School", short: "School" },
  { key: "jee", label: " JEE", short: "JEE" },
  { key: "neet", label: "🧪 NEET", short: "NEET" },
  { key: "gate", label: "🎓 GATE", short: "GATE" },
  { key: "skills", label: "💻 Skills", short: "Skills" },
  { key: "college", label: "🎓 College", short: "College" },
];

interface ExamConfig {
  label: string; description: string; difficulty: string;
  timer_seconds: number; question_style: string; mock_duration_min: number;
  strategy_prefix: string; syllabus: Record<string, string[]>;
  topic_weights: Record<string, number>;
  priority_topics: [string, number][];
}

export default function DashboardPage() {
  const [mastery, setMastery] = useState<MasteryData | null>(null);
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [smartPlan, setSmartPlan] = useState<SmartPlanResult | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [activeDay, setActiveDay] = useState(0);

  // Exam mode
  const [examMode, setExamMode] = useState("jee");
  const [examConfig, setExamConfig] = useState<ExamConfig | null>(null);

  // Exam setup
  const [examDate, setExamDate] = useState("");
  const [studyHours, setStudyHours] = useState("1.5");
  const [showExamSetup, setShowExamSetup] = useState(false);

  useEffect(() => {
    setMastery({ mastery_level: "beginner", confidence_score: 0 });
  }, []);

  // Fetch exam config when mode changes
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ task_type: "exam_config", task_input: { exam_key: examMode } }),
        });
        const data = await res.json();
        setExamConfig(data.output as ExamConfig);
      } catch { /* silent */ }
    })();
  }, [examMode]);

  const generatePlan = async () => {
    setPlanLoading(true);
    try {
      // If exam date is set, use smart planner
      if (examDate) {
        const res = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            task_type: "smart_plan",
            user_profile: { user_id: TEST_USER_ID },
            task_input: { exam_date: examDate, study_hours: parseFloat(studyHours) },
          }),
        });
        const data = await res.json();
        setSmartPlan(data.output as SmartPlanResult);
        setPlan(null);
      } else {
        // Fallback to original LLM planner
        const res = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            task_type: "plan",
            user_profile: { user_id: TEST_USER_ID, target_exam: "IIT JEE", current_class: "12th", language_pref: "English" },
            learning_state: {},
            learning_pattern: {},
            task_input: { duration: 7 },
          }),
        });
        const data = await res.json();
        setPlan(data.output || {});
        setSmartPlan(null);
      }
    } catch {
      setPlan({ error_fallback: "Failed to reach API. Ensure backend is running." });
    } finally {
      setPlanLoading(false);
    }
  };

  const tier = mastery ? TIER_STYLES[mastery.mastery_level] || TIER_STYLES.beginner : TIER_STYLES.beginner;
  const confColor = smartPlan?.readiness?.confidence === "High" ? "text-emerald-400" : smartPlan?.readiness?.confidence === "Medium" ? "text-amber-400" : "text-red-400";

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-bold mb-1">
        📊 Your <span className="gradient-text">Dashboard</span>
      </h1>
      <p className="text-gray-500 text-sm mb-4">Track your mastery progress, exam readiness, and study plan</p>

      {/* Exam Mode Selector */}
      <div className="flex items-center gap-2 mb-6 flex-wrap">
        <span className="text-xs text-gray-500 uppercase tracking-wider mr-1">Mode:</span>
        {EXAM_OPTIONS.map((e) => (
          <button key={e.key} onClick={() => setExamMode(e.key)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-smooth ${examMode === e.key ? "bg-emerald-600 text-gray-900" : "bg-black/5 text-gray-600 hover:bg-black/10 hover:text-gray-900"
              }`}>
            {e.label}
          </button>
        ))}
      </div>

      {/* Top Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {/* Mastery Card */}
        <div className="glass-card p-6 col-span-1">
          <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">Mastery Level</h3>
          <div className={`text-2xl font-bold mb-1 ${tier.color}`}>{tier.label}</div>
          <div className="text-sm text-gray-500 mb-4">Newton&apos;s Laws</div>
          <div className="w-full bg-black/5 rounded-full h-2.5 mb-2">
            <div className="h-2.5 rounded-full transition-all duration-700 bg-gradient-to-r from-emerald-500 to-green-500"
              style={{ width: `${mastery?.confidence_score || 0}%` }} />
          </div>
          <div className="text-xs text-gray-500">Confidence: {mastery?.confidence_score?.toFixed(1) || 0}%</div>
        </div>

        {/* Cognitive Profile Card */}
        <div className="glass-card p-6 col-span-1">
          <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">Cognitive Profile</h3>
          <div className="space-y-3">
            <ProfileBar label="Reasoning Depth" value={50} color="from-emerald-500 to-teal-500" />
            <ProfileBar label="Memorization Tendency" value={50} color="from-amber-500 to-orange-500" />
          </div>
          <p className="text-xs text-gray-500 mt-3">Style: Visual Learner</p>
        </div>

        {/* Exam Readiness Card (NEW — replaces Quick Stats when smart plan is active) */}
        {smartPlan?.readiness ? (
          <div className="glass-card p-6 col-span-1">
            <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">Exam Readiness</h3>
            <div className={`text-3xl font-bold ${confColor}`}>{smartPlan.readiness.current_score}%</div>
            <div className="w-full bg-black/5 rounded-full h-2 mt-2 mb-2 overflow-hidden">
              <div className="h-2 rounded-full bg-gradient-to-r from-emerald-500 to-green-500 transition-all duration-1000"
                style={{ width: `${smartPlan.readiness.current_score}%` }} />
            </div>
            <div className="text-xs text-gray-500 space-y-1">
              <div className="flex justify-between">
                <span>Projected</span>
                <span className="text-emerald-400">{smartPlan.readiness.projected_score}%</span>
              </div>
              <div className="flex justify-between">
                <span>Days left</span>
                <span className="text-gray-900">{smartPlan.days_until_exam}</span>
              </div>
              <div className="flex justify-between">
                <span>Confidence</span>
                <span className={confColor}>{smartPlan.readiness.confidence}</span>
              </div>
            </div>
            {smartPlan.is_exam_mode && (
              <div className="mt-2 text-xs text-red-400 font-medium">🔥 Exam Mode Active</div>
            )}
          </div>
        ) : (
          <div className="glass-card p-6 col-span-1">
            <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">
              {examConfig?.label || "Quick Stats"}
            </h3>
            <div className="space-y-3">
              <StatRow label="Exam" value={examConfig?.label?.replace(/^[^\s]+\s/, "") || "—"} />
              <StatRow label="Difficulty" value={examConfig?.difficulty || "—"} />
              <StatRow label="Q Style" value={examConfig?.question_style?.split(",")[0] || "—"} />
              <StatRow label="Timer" value={examConfig?.timer_seconds ? `${examConfig.timer_seconds}s` : "None"} />
            </div>
          </div>
        )}
      </div>

      {/* Topic Analysis (NEW — shows when smart plan is active) */}
      {smartPlan?.topic_analysis && smartPlan.topic_analysis.length > 0 && (
        <div className="mb-8">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wider mb-3">📈 Topic Analysis</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {smartPlan.topic_analysis.map((t, i) => (
              <div key={i} className="glass-card p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-900 font-medium">{t.topic_name}</span>
                  <div className="flex items-center gap-3 text-xs">
                    <span className={`font-bold ${t.mastery_score >= 70 ? "text-emerald-400" : t.mastery_score >= 40 ? "text-amber-400" : "text-red-400"
                      }`}>{t.mastery_score}%</span>
                    <span className="text-gray-500">Risk: <span className={t.forgetting_risk > 0.5 ? "text-red-400" : "text-gray-600"}>{(t.forgetting_risk * 100).toFixed(0)}%</span></span>
                  </div>
                </div>
                <div className="w-full bg-black/5 rounded-full h-1.5 overflow-hidden">
                  <div className={`h-1.5 rounded-full transition-all duration-700 ${t.mastery_score >= 70 ? "bg-emerald-500" : t.mastery_score >= 40 ? "bg-amber-500" : "bg-red-500"
                    }`} style={{ width: `${t.mastery_score}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Study Plan Section */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900">📅 Study Plan</h2>
            <p className="text-xs text-gray-500">
              {examDate ? "Smart spaced repetition schedule" : "AI-generated 7-day schedule"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowExamSetup(!showExamSetup)}
              className="px-3 py-2 rounded-full bg-black/5 text-gray-600 text-xs hover:bg-black/10 hover:text-gray-900 transition-smooth">
              {examDate ? "Edit Exam" : "Set Exam"}
            </button>
            <button onClick={generatePlan} disabled={planLoading}
              className="px-5 py-2 rounded-full bg-gradient-to-r from-emerald-600 to-green-600 text-gray-900 text-sm font-medium hover:from-emerald-500 hover:to-green-500 transition-smooth disabled:opacity-50">
              {planLoading ? "Generating..." : "🧠 Generate Plan"}
            </button>
          </div>
        </div>

        {/* Exam Setup (collapsible) */}
        {showExamSetup && (
          <div className="bg-black/5 rounded-xl p-4 mb-4 grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Exam Date</label>
              <input type="date" value={examDate} onChange={(e) => setExamDate(e.target.value)}
                className="w-full bg-black/5 border border-black/10 rounded-lg px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500/50 transition-smooth" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Study hrs/day</label>
              <input type="number" step="0.5" min="0.5" max="8" value={studyHours} onChange={(e) => setStudyHours(e.target.value)}
                className="w-full bg-black/5 border border-black/10 rounded-lg px-3 py-2 text-sm text-gray-900 outline-none focus:border-emerald-500/50 transition-smooth" />
            </div>
          </div>
        )}

        {/* Priority Suggestions */}
        {smartPlan?.priority_suggestions && smartPlan.priority_suggestions.length > 0 && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-4">
            <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">🎯 Priority</div>
            {smartPlan.priority_suggestions.map((s, i) => (
              <p key={i} className="text-sm text-gray-700 mb-1">• {s}</p>
            ))}
          </div>
        )}

        {/* Smart Plan — Daily Schedule Tabs */}
        {smartPlan?.daily_plans && smartPlan.daily_plans.length > 0 && (
          <div>
            <div className="flex gap-2 mb-3 overflow-x-auto pb-1">
              {smartPlan.daily_plans.map((day, i) => (
                <button key={i} onClick={() => setActiveDay(i)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-smooth ${activeDay === i ? "bg-emerald-600 text-gray-900" : "bg-black/5 text-gray-600 hover:bg-black/10"
                    } ${day.is_exam_mode ? "border border-red-500/30" : ""}`}>
                  {day.is_exam_mode && "🔥 "}{day.day_label}
                </button>
              ))}
            </div>

            {smartPlan.daily_plans[activeDay] && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                  <span>{smartPlan.daily_plans[activeDay].day_label}</span>
                  <span>{smartPlan.daily_plans[activeDay].total_minutes} min</span>
                </div>
                {smartPlan.daily_plans[activeDay].activities.map((act, j) => (
                  <div key={j} className="flex items-center gap-3 bg-black/5 rounded-lg p-3">
                    <div className={`w-2 h-2 rounded-full shrink-0 ${act.activity === "Learn" ? "bg-teal-400" :
                      act.activity === "Revise" ? "bg-amber-400" :
                        act.activity.includes("Quiz") ? "bg-emerald-400" : "bg-red-400"
                      }`} />
                    <div className="flex-1">
                      <span className="text-sm text-gray-900">{act.topic}</span>
                      <span className="text-xs text-gray-500 ml-2">— {act.activity}</span>
                    </div>
                    <span className="text-xs text-gray-500">{act.duration_min}m</span>
                    {act.mastery !== null && (
                      <span className={`text-xs font-medium ${act.mastery >= 70 ? "text-emerald-400" : act.mastery >= 40 ? "text-amber-400" : "text-red-400"
                        }`}>{act.mastery}%</span>
                    )}
                  </div>
                ))}
                {smartPlan.daily_plans[activeDay].activities.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">No activities scheduled.</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Old LLM Plan (backward compat) */}
        {plan?.error_fallback && (
          <div className="text-sm text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-4">
            {plan.error_fallback}
          </div>
        )}

        {plan?.strategic_advice && (
          <div className="text-sm text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 mb-4">
            💡 <span className="font-medium">Strategy:</span> {plan.strategic_advice}
          </div>
        )}

        {plan?.daily_schedule && plan.daily_schedule.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {plan.daily_schedule.map((day) => (
              <div key={day.day} className="bg-black/5 rounded-xl p-4 border border-black/5 hover:border-emerald-500/30 transition-smooth">
                <div className="text-xs font-bold text-emerald-400 mb-2">Day {day.day}</div>
                <div className="text-sm text-gray-900 font-medium mb-2">
                  {day.focus_topics?.join(", ") || "Review"}
                </div>
                {day.learning_mode && (
                  <div className="text-xs text-gray-500 mb-2">Mode: {day.learning_mode}</div>
                )}
                <ul className="text-xs text-gray-600 space-y-1">
                  {day.recommended_activities?.map((a, i) => (
                    <li key={i}>• {a}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!plan?.daily_schedule && !smartPlan?.daily_plans && !plan?.error_fallback && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-3">📅</div>
            <p className="text-sm">Click &quot;Generate Plan&quot; to create your personalized study schedule</p>
            <p className="text-xs text-gray-600 mt-1">Set an exam date for smart spaced-repetition planning</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ProfileBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="text-gray-500">{value}%</span>
      </div>
      <div className="w-full bg-black/5 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full bg-gradient-to-r ${color} transition-all duration-700`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-900 font-medium">{value}</span>
    </div>
  );
}
