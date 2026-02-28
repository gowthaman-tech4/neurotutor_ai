"use client";

import { useState } from "react";

const API_URL = "http://localhost:8000/api/engine/route";
const TEST_USER_ID = "8b40ebcf-92aa-43a2-8def-bee49247cebc";

type SubmissionType = "essay" | "code" | "presentation" | "lab_report";
type ReviewMode = "feedback" | "originality" | "citations";
type Phase = "submit" | "analyzing" | "results";

interface CriterionScore {
    name: string; score: number; max_score: number; explanation: string;
    weakness_quote: string | null; suggestion: string; improved_example: string | null;
}

interface FeedbackResult {
    submission_type: string; total_score: number; total_possible: number;
    criteria_scores: CriterionScore[]; overall_feedback: string; top_priority_fix: string;
}

interface FlaggedSection {
    text: string; issue_type: string; severity: string; explanation: string; rewrite_hint: string;
}

interface UncitedClaim { claim: string; reason: string; }

interface OriginalityResult {
    originality_score: number; similarity_score: number; ai_detection_score: number;
    flagged_sections: FlaggedSection[]; uncited_claims: UncitedClaim[];
    overall_assessment: string; is_safe_to_submit: boolean;
}

interface CitationItem {
    claim_text: string; why_citation_needed: string; suggested_citation: string; citation_type: string;
}

interface CitationResult {
    total_claims_found: number; citations_needed: CitationItem[];
    citation_tips: string[]; format_used: string;
}

const SUBMISSION_TYPES: { key: SubmissionType; label: string; emoji: string; ph: string }[] = [
    { key: "essay", label: "Essay", emoji: "📄", ph: "Paste your essay here..." },
    { key: "code", label: "Code", emoji: "💻", ph: "Paste your code here..." },
    { key: "presentation", label: "Presentation", emoji: "📊", ph: "Paste your slide content..." },
    { key: "lab_report", label: "Lab Report", emoji: "🔬", ph: "Paste your lab report..." },
];

const REVIEW_MODES: { key: ReviewMode; label: string; emoji: string }[] = [
    { key: "feedback", label: "Rubric Feedback", emoji: "✅" },
    { key: "originality", label: "Check Originality", emoji: "🔍" },
    { key: "citations", label: "Add Citations", emoji: "📚" },
];

export default function ReviewPage() {
    const [phase, setPhase] = useState<Phase>("submit");
    const [subType, setSubType] = useState<SubmissionType>("essay");
    const [reviewMode, setReviewMode] = useState<ReviewMode>("feedback");
    const [content, setContent] = useState("");
    const [loading, setLoading] = useState(false);
    const [revision, setRevision] = useState(1);

    // Results
    const [feedbackResult, setFeedbackResult] = useState<FeedbackResult | null>(null);
    const [origResult, setOrigResult] = useState<OriginalityResult | null>(null);
    const [citResult, setCitResult] = useState<CitationResult | null>(null);
    const [expandedItem, setExpandedItem] = useState<string | null>(null);

    const submit = async () => {
        if (!content.trim()) return;
        setLoading(true);
        setPhase("analyzing");

        try {
            let taskType = "rubric_feedback";
            let taskInput: Record<string, string> = { submission_type: subType, content };

            if (reviewMode === "originality") {
                taskType = "originality_check";
                taskInput = { content, check_type: "originality" };
            } else if (reviewMode === "citations") {
                taskType = "originality_check";
                taskInput = { content, check_type: "citations" };
            }

            const res = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    task_type: taskType,
                    user_profile: { user_id: TEST_USER_ID },
                    task_input: taskInput,
                }),
            });
            const data = await res.json();
            const output = data.output || {};

            if (reviewMode === "feedback") setFeedbackResult(output as FeedbackResult);
            else if (reviewMode === "originality") setOrigResult(output as OriginalityResult);
            else if (reviewMode === "citations") setCitResult(output as CitationResult);

            setPhase("results");
        } catch {
            alert("Failed to reach API.");
            setPhase("submit");
        } finally {
            setLoading(false);
        }
    };

    const handleRevise = () => {
        setRevision((r) => r + 1);
        setPhase("submit");
        setFeedbackResult(null);
        setOrigResult(null);
        setCitResult(null);
        setExpandedItem(null);
    };

    return (
        <div className="max-w-3xl mx-auto px-6 py-8">
            {/* SUBMIT PHASE */}
            {phase === "submit" && (
                <div>
                    <div className="text-center mb-6">
                        <div className="text-4xl mb-3">📝</div>
                        <h1 className="text-2xl font-bold mb-1"><span className="gradient-text">Review & Integrity</span></h1>
                        <p className="text-gray-400 text-sm">
                            Get rubric feedback, check originality, or add citations.
                            {revision > 1 && <span className="text-violet-400 ml-2">Draft {revision}</span>}
                        </p>
                    </div>

                    {/* Review Mode Selector */}
                    <div className="flex gap-2 justify-center mb-4">
                        {REVIEW_MODES.map((m) => (
                            <button key={m.key} onClick={() => setReviewMode(m.key)}
                                className={`px-4 py-2 rounded-full text-sm font-medium transition-smooth ${reviewMode === m.key ? "bg-violet-600 text-white glow" : "bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white"
                                    }`}>
                                {m.emoji} {m.label}
                            </button>
                        ))}
                    </div>

                    {/* Submission Type (only for rubric feedback) */}
                    {reviewMode === "feedback" && (
                        <div className="flex gap-2 justify-center mb-4">
                            {SUBMISSION_TYPES.map((t) => (
                                <button key={t.key} onClick={() => setSubType(t.key)}
                                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-smooth ${subType === t.key ? "bg-cyan-600/30 text-cyan-300" : "bg-white/5 text-gray-500 hover:bg-white/10"
                                        }`}>
                                    {t.emoji} {t.label}
                                </button>
                            ))}
                        </div>
                    )}

                    <div className="glass-card p-4 mb-4">
                        <textarea value={content} onChange={(e) => setContent(e.target.value)}
                            placeholder={reviewMode === "feedback" ? SUBMISSION_TYPES.find((t) => t.key === subType)?.ph : "Paste your work here..."}
                            className="w-full bg-transparent text-white placeholder-gray-500 outline-none text-sm resize-none min-h-[200px] font-mono leading-relaxed" />
                    </div>

                    <div className="flex gap-3 justify-end">
                        <button onClick={submit} disabled={!content.trim() || loading}
                            className="px-6 py-2.5 rounded-full bg-gradient-to-r from-violet-600 to-purple-600 text-white text-sm font-medium transition-smooth disabled:opacity-40 glow">
                            {reviewMode === "feedback" ? "✅ Submit for Feedback" : reviewMode === "originality" ? "🔍 Check Originality" : "📚 Find Citations"}
                        </button>
                    </div>
                </div>
            )}

            {/* ANALYZING PHASE */}
            {phase === "analyzing" && (
                <div className="flex flex-col items-center justify-center min-h-[50vh]">
                    <div className="text-4xl mb-6 animate-pulse">{reviewMode === "originality" ? "🔍" : reviewMode === "citations" ? "📚" : "📝"}</div>
                    <h2 className="text-lg font-semibold text-white mb-2">
                        {reviewMode === "originality" ? "Checking originality…" : reviewMode === "citations" ? "Finding citations…" : "Analyzing your submission…"}
                    </h2>
                    <div className="w-64 bg-white/5 rounded-full h-2 overflow-hidden">
                        <div className="h-2 bg-gradient-to-r from-violet-500 to-purple-500 rounded-full animate-pulse" style={{ width: "75%" }} />
                    </div>
                </div>
            )}

            {/* RESULTS PHASE */}
            {phase === "results" && (
                <div>
                    {/* ==== ORIGINALITY RESULTS ==== */}
                    {reviewMode === "originality" && origResult && (
                        <div>
                            <div className="glass-card p-6 mb-6 text-center">
                                <div className="text-xs uppercase tracking-wider text-gray-500 mb-1">Originality Score</div>
                                <div className={`text-5xl font-bold mb-1 ${(origResult.originality_score ?? 0) >= 80 ? "text-emerald-400" : (origResult.originality_score ?? 0) >= 60 ? "text-amber-400" : "text-red-400"
                                    }`}>{origResult.originality_score ?? 0}%</div>
                                <div className="w-full bg-white/5 rounded-full h-2.5 mt-3 mb-3 overflow-hidden">
                                    <div className={`h-2.5 rounded-full transition-all duration-1000 ${(origResult.originality_score ?? 0) >= 80 ? "bg-emerald-500" : (origResult.originality_score ?? 0) >= 60 ? "bg-amber-500" : "bg-red-500"
                                        }`} style={{ width: `${origResult.originality_score ?? 0}%` }} />
                                </div>
                                <div className="flex justify-center gap-6 text-xs text-gray-500">
                                    <span>Similarity: <span className="text-amber-400">{origResult.similarity_score ?? 0}%</span></span>
                                    <span>AI Detection: <span className="text-red-400">{origResult.ai_detection_score ?? 0}%</span></span>
                                </div>
                                <div className={`mt-3 text-sm font-medium ${origResult.is_safe_to_submit ? "text-emerald-400" : "text-red-400"}`}>
                                    {origResult.is_safe_to_submit ? "✅ Safe to submit" : "⚠️ Needs revision"}
                                </div>
                            </div>

                            {origResult.overall_assessment && (
                                <div className="glass-card p-4 mb-4">
                                    <p className="text-sm text-gray-300">{origResult.overall_assessment}</p>
                                </div>
                            )}

                            {/* Flagged Sections */}
                            {origResult.flagged_sections && origResult.flagged_sections.length > 0 && (
                                <div className="space-y-2 mb-4">
                                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">⚠️ Flagged Sections</h3>
                                    {origResult.flagged_sections.map((f, i) => {
                                        const key = `flag-${i}`;
                                        const isExp = expandedItem === key;
                                        const sevColor = f.severity === "high" ? "border-red-500/30 bg-red-500/5" : f.severity === "medium" ? "border-amber-500/30 bg-amber-500/5" : "border-yellow-500/20 bg-yellow-500/5";
                                        return (
                                            <div key={i} className={`rounded-xl border ${sevColor} overflow-hidden`}>
                                                <button onClick={() => setExpandedItem(isExp ? null : key)}
                                                    className="w-full text-left p-4 hover:bg-white/5 transition-smooth">
                                                    <div className="flex items-start gap-2">
                                                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${f.severity === "high" ? "bg-red-500/20 text-red-400" : f.severity === "medium" ? "bg-amber-500/20 text-amber-400" : "bg-yellow-500/20 text-yellow-400"
                                                            }`}>{f.severity}</span>
                                                        <p className="text-sm text-gray-300 italic flex-1">&ldquo;{f.text}&rdquo;</p>
                                                    </div>
                                                </button>
                                                {isExp && (
                                                    <div className="px-4 pb-4 space-y-2 border-t border-white/5 pt-3">
                                                        <p className="text-sm text-gray-400">{f.explanation}</p>
                                                        <div className="bg-violet-500/10 border border-violet-500/20 rounded-lg p-3">
                                                            <div className="text-xs font-semibold text-violet-400 mb-1">💡 Rewrite Guidance</div>
                                                            <p className="text-sm text-gray-300">{f.rewrite_hint}</p>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Uncited Claims */}
                            {origResult.uncited_claims && origResult.uncited_claims.length > 0 && (
                                <div className="glass-card p-4 mb-4">
                                    <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">📚 Needs Citation</div>
                                    {origResult.uncited_claims.map((c, i) => (
                                        <div key={i} className="text-sm text-gray-300 mb-2">
                                            <span className="text-gray-400">•</span> &ldquo;{c.claim}&rdquo; — <span className="text-gray-500">{c.reason}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* ==== CITATION RESULTS ==== */}
                    {reviewMode === "citations" && citResult && (
                        <div>
                            <div className="glass-card p-6 mb-6 text-center">
                                <div className="text-xs uppercase tracking-wider text-gray-500 mb-1">Citations Needed</div>
                                <div className="text-4xl font-bold text-violet-400">{citResult.total_claims_found}</div>
                                <p className="text-xs text-gray-500 mt-1">Format: {citResult.format_used}</p>
                            </div>

                            <div className="space-y-3 mb-4">
                                {citResult.citations_needed?.map((c, i) => (
                                    <div key={i} className="glass-card p-4">
                                        <p className="text-sm text-gray-300 mb-2">&ldquo;{c.claim_text}&rdquo;</p>
                                        <p className="text-xs text-gray-500 mb-2">{c.why_citation_needed}</p>
                                        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3">
                                            <div className="text-xs font-semibold text-emerald-400 mb-1">📖 Suggested Citation</div>
                                            <p className="text-sm text-gray-200 font-mono">{c.suggested_citation}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {citResult.citation_tips && citResult.citation_tips.length > 0 && (
                                <div className="bg-violet-500/10 border border-violet-500/20 rounded-xl p-4 mb-4">
                                    <div className="text-xs font-semibold text-violet-400 uppercase tracking-wider mb-2">💡 Citation Tips</div>
                                    {citResult.citation_tips.map((t, i) => (
                                        <p key={i} className="text-sm text-gray-300 mb-1">• {t}</p>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* ==== RUBRIC FEEDBACK RESULTS ==== */}
                    {reviewMode === "feedback" && feedbackResult && (
                        <div>
                            <div className="glass-card p-6 mb-6 text-center">
                                <div className="text-xs uppercase tracking-wider text-gray-500 mb-1">
                                    {SUBMISSION_TYPES.find((t) => t.key === subType)?.emoji} {feedbackResult.submission_type} — Draft {revision}
                                </div>
                                <div className={`text-5xl font-bold mb-1 ${Math.round((feedbackResult.total_score / feedbackResult.total_possible) * 100) >= 80 ? "text-emerald-400"
                                        : Math.round((feedbackResult.total_score / feedbackResult.total_possible) * 100) >= 60 ? "text-amber-400" : "text-red-400"
                                    }`}>{feedbackResult.total_score}/{feedbackResult.total_possible}</div>
                                <div className="w-full bg-white/5 rounded-full h-2.5 mt-3 overflow-hidden">
                                    <div className={`h-2.5 rounded-full transition-all duration-1000 ${Math.round((feedbackResult.total_score / feedbackResult.total_possible) * 100) >= 80 ? "bg-emerald-500"
                                            : Math.round((feedbackResult.total_score / feedbackResult.total_possible) * 100) >= 60 ? "bg-amber-500" : "bg-red-500"
                                        }`} style={{ width: `${(feedbackResult.total_score / feedbackResult.total_possible) * 100}%` }} />
                                </div>
                            </div>

                            {feedbackResult.top_priority_fix && (
                                <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-4">
                                    <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1">🎯 Top Priority</div>
                                    <p className="text-sm text-gray-300">{feedbackResult.top_priority_fix}</p>
                                </div>
                            )}

                            <div className="space-y-3 mb-4">
                                {feedbackResult.criteria_scores?.map((cs) => {
                                    const pct = Math.round((cs.score / cs.max_score) * 100);
                                    const isExp = expandedItem === cs.name;
                                    return (
                                        <div key={cs.name} className="glass-card overflow-hidden">
                                            <button onClick={() => setExpandedItem(isExp ? null : cs.name)}
                                                className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-smooth text-left">
                                                <div className="flex items-center gap-3">
                                                    <div className={`text-lg font-bold ${pct >= 80 ? "text-emerald-400" : pct >= 60 ? "text-amber-400" : "text-red-400"}`}>
                                                        {cs.score}/{cs.max_score}
                                                    </div>
                                                    <span className="text-sm text-white font-medium">{cs.name}</span>
                                                </div>
                                                <svg className={`w-4 h-4 text-gray-500 transition-transform ${isExp ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                            </button>
                                            {isExp && (
                                                <div className="px-4 pb-4 space-y-3 border-t border-white/5 pt-3">
                                                    <p className="text-sm text-gray-300">{cs.explanation}</p>
                                                    {cs.weakness_quote && (
                                                        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                                                            <div className="text-xs font-semibold text-red-400 mb-1">⚠️ Weak point</div>
                                                            <p className="text-sm text-gray-400 italic">&ldquo;{cs.weakness_quote}&rdquo;</p>
                                                        </div>
                                                    )}
                                                    <div className="bg-violet-500/10 border border-violet-500/20 rounded-lg p-3">
                                                        <div className="text-xs font-semibold text-violet-400 mb-1">💡 Suggestion</div>
                                                        <p className="text-sm text-gray-300">{cs.suggestion}</p>
                                                    </div>
                                                    {cs.improved_example && (
                                                        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3">
                                                            <div className="text-xs font-semibold text-emerald-400 mb-1">✨ Improved</div>
                                                            <p className="text-sm text-gray-200">{cs.improved_example}</p>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>

                            {feedbackResult.overall_feedback && (
                                <div className="glass-card p-4 mb-4">
                                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Overall Feedback</div>
                                    <p className="text-sm text-gray-300">{feedbackResult.overall_feedback}</p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex gap-3 justify-end">
                        <button onClick={() => { setPhase("submit"); setContent(""); setFeedbackResult(null); setOrigResult(null); setCitResult(null); setRevision(1); }}
                            className="px-5 py-2.5 rounded-full border border-white/10 text-gray-400 text-sm hover:bg-white/5 transition-smooth">
                            New Submission
                        </button>
                        <button onClick={handleRevise}
                            className="px-5 py-2.5 rounded-full bg-gradient-to-r from-violet-600 to-purple-600 text-white text-sm font-medium transition-smooth glow">
                            ✏️ Revise & Resubmit
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
