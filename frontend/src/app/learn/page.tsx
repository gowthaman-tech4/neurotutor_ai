"use client";

import { useState, useCallback } from "react";

const API_URL = "http://localhost:8000/api/engine/route";
const TEST_USER_ID = "8b40ebcf-92aa-43a2-8def-bee49247cebc";

type Phase = "topic" | "lesson" | "qa" | "practice" | "hint" | "evaluate" | "mastery";

interface ThoughtResult {
  understanding_score: number;
  understanding_feedback: string;
  missing_concepts: string[];
  thought_patterns: Record<string, number>;
  detected_style: string;
  style_confidence: number;
  personalization_hints: { preferred_examples: string; explanation_approach: string; avoid: string };
  encouragement: string;
}

interface LessonStep {
  step_number: number;
  title: string;
  explanation: string;
  example: string;
  visual_hint: string;
  mini_check: string;
}

export default function LearnPage() {
  const [phase, setPhase] = useState<Phase>("topic");
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);

  // Lesson state
  const [steps, setSteps] = useState<LessonStep[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [practiceMessage, setPracticeMessage] = useState("");

  // Practice state
  const [question, setQuestion] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [answer, setAnswer] = useState("");
  const [hintsUsed, setHintsUsed] = useState(0);
  const [attempts, setAttempts] = useState(0);
  const [hintText, setHintText] = useState("");

  // Q&A state
  const [qaAnswer, setQaAnswer] = useState("");
  const [qaStep, setQaStep] = useState(0);
  const [thoughtResult, setThoughtResult] = useState<ThoughtResult | null>(null);
  const [qaLoading, setQaLoading] = useState(false);

  // Evaluation state
  const [evalResult, setEvalResult] = useState<Record<string, unknown> | null>(null);
  const [masteryData, setMasteryData] = useState<{ level: string; score: number; prevScore: number } | null>(null);

  const apiCall = useCallback(async (taskType: string, taskInput: Record<string, unknown>) => {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_type: taskType,
        user_profile: { user_id: TEST_USER_ID, target_exam: "IIT JEE", current_class: "12th", language_pref: "English" },
        learning_state: { mastery_level: masteryData?.level || "beginner", topic: topic },
        learning_pattern: { style: "visual" },
        task_input: taskInput,
      }),
    });
    const data = await res.json();
    return data.output || {};
  }, [topic, masteryData]);

  // ---- Phase handlers ----

  const startLesson = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    try {
      const output = await apiCall("concept_coach", { topic });
      setSteps(output.steps || []);
      setPracticeMessage(output.practice_ready_message || "Ready to practice!");
      setCurrentStep(0);
      setPhase("lesson");
    } catch { alert("API error"); }
    finally { setLoading(false); }
  };

  const QA_QUESTIONS = [
    { type: "explain", text: `Explain ${topic} in your own words` },
    { type: "example", text: `Give a real-life example of ${topic}` },
    { type: "importance", text: `Why is ${topic} important?` },
  ];

  const startQA = () => {
    setQaStep(0);
    setQaAnswer("");
    setThoughtResult(null);
    setPhase("qa");
  };

  const submitQA = async () => {
    if (!qaAnswer.trim()) return;
    setQaLoading(true);
    try {
      const output = await apiCall("thought_analyze", {
        topic,
        explanation: qaAnswer,
        question_type: QA_QUESTIONS[qaStep].type,
      });
      setThoughtResult(output as ThoughtResult);
    } catch { /* silent */ }
    finally { setQaLoading(false); }
  };

  const nextQAOrPractice = () => {
    if (qaStep < QA_QUESTIONS.length - 1) {
      setQaStep((p) => p + 1);
      setQaAnswer("");
      setThoughtResult(null);
    } else {
      startPractice();
    }
  };

  const startPractice = async () => {
    setLoading(true);
    setHintsUsed(0);
    setAttempts(0);
    setHintText("");
    setAnswer("");
    setEvalResult(null);
    try {
      const output = await apiCall("practice", { topic });
      setQuestion(output.question || "Practice question unavailable.");
      setDifficulty(output.difficulty_assigned || "Medium");
      setPhase("practice");
    } catch { alert("API error"); }
    finally { setLoading(false); }
  };

  const requestHint = async () => {
    setLoading(true);
    try {
      const output = await apiCall("hint", { topic, hint_level: hintsUsed + 1 });
      setHintText(output.hint_text || "Think carefully...");
      setHintsUsed((prev) => prev + 1);
      setPhase("hint");
    } catch { alert("API error"); }
    finally { setLoading(false); }
  };

  const submitAnswer = async () => {
    if (!answer.trim()) return;
    setLoading(true);
    const newAttempts = attempts + 1;
    setAttempts(newAttempts);
    try {
      const output = await apiCall("evaluate", {
        answer,
        topic,
        hints_used: hintsUsed,
        attempts: newAttempts,
      });
      setEvalResult(output);

      const masteryUpdate = output.mastery_update;
      if (masteryUpdate) {
        setMasteryData((prev) => ({
          level: masteryUpdate.updated_mastery_level,
          score: masteryUpdate.new_confidence_score,
          prevScore: prev?.score || 0,
        }));
      }
      setPhase("evaluate");
    } catch { alert("API error"); }
    finally { setLoading(false); }
  };

  // ---- Renders ----

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      {/* Phase: Topic Select */}
      {phase === "topic" && (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
          <div className="text-5xl mb-4">📚</div>
          <h1 className="text-3xl font-bold mb-2">
            <span className="gradient-text">Concept Coach</span>
          </h1>
          <p className="text-gray-600 text-sm mb-8 max-w-md">
            Choose a topic and I&apos;ll guide you step-by-step from understanding to mastery.
          </p>
          <div className="glass-card flex items-center gap-3 px-4 py-3 w-full max-w-lg glow">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && startLesson()}
              placeholder="e.g. Quadratic Equations, Newton's Laws..."
              className="flex-1 bg-transparent text-gray-900 placeholder-gray-500 outline-none text-sm"
            />
            <button
              onClick={startLesson}
              disabled={loading || !topic.trim()}
              className="px-5 py-2 rounded-full bg-gradient-to-r from-emerald-600 to-green-600 text-gray-900 text-sm font-medium transition-smooth disabled:opacity-40"
            >
              {loading ? "Loading..." : "📖 Learn"}
            </button>
          </div>
          {/* Quick topic suggestions */}
          <div className="flex flex-wrap gap-2 mt-6 justify-center">
            {["Quadratic Equations", "Newton's Laws", "Photosynthesis", "Trigonometry", "Chemical Bonding"].map((t) => (
              <button key={t} onClick={() => setTopic(t)}
                className="px-3 py-1.5 rounded-full bg-black/5 text-gray-600 text-xs hover:bg-black/10 hover:text-gray-900 transition-smooth">
                {t}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Phase: Lesson Steps */}
      {phase === "lesson" && steps.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">📖 {topic}</h2>
            <span className="text-xs text-gray-500">Step {currentStep + 1} of {steps.length}</span>
          </div>

          {/* Progress dots */}
          <div className="flex gap-2 mb-6">
            {steps.map((_, i) => (
              <div key={i} className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${i <= currentStep ? "bg-emerald-500" : "bg-black/10"}`} />
            ))}
          </div>

          <div className="glass-card p-6 mb-4">
            <h3 className="text-lg font-semibold text-emerald-300 mb-3">
              Step {steps[currentStep].step_number}: {steps[currentStep].title}
            </h3>
            <p className="text-gray-700 text-sm leading-relaxed mb-4">{steps[currentStep].explanation}</p>

            {steps[currentStep].example && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 mb-4">
                <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">Example</div>
                <p className="text-sm text-gray-800">{steps[currentStep].example}</p>
              </div>
            )}

            {steps[currentStep].visual_hint && steps[currentStep].visual_hint !== "N/A" && (
              <div className="bg-teal-500/10 border border-teal-500/20 rounded-xl p-4 mb-4">
                <div className="text-xs font-semibold text-teal-400 uppercase tracking-wider mb-1">🎨 Visual</div>
                <p className="text-sm text-gray-700">{steps[currentStep].visual_hint}</p>
              </div>
            )}

            {steps[currentStep].mini_check && (
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
                <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1">🧪 Quick Check</div>
                <p className="text-sm text-gray-700">{steps[currentStep].mini_check}</p>
              </div>
            )}
          </div>

          <div className="flex gap-3 justify-end">
            {currentStep > 0 && (
              <button onClick={() => setCurrentStep((p) => p - 1)}
                className="px-5 py-2.5 rounded-full border border-black/10 text-gray-600 text-sm hover:bg-black/5 transition-smooth">
                 Back
              </button>
            )}
            {currentStep < steps.length - 1 ? (
              <button onClick={() => setCurrentStep((p) => p + 1)}
                className="px-5 py-2.5 rounded-full bg-gradient-to-r from-emerald-600 to-green-600 text-gray-900 text-sm font-medium transition-smooth">
                Next 
              </button>
            ) : (
              <button onClick={startQA}
                className="px-5 py-2.5 rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 text-gray-900 text-sm font-medium transition-smooth glow">
                 Concept Complete Q&A
              </button>
            )}
          </div>
        </div>
      )}

      {/* Phase: Q&A */}
      {phase === "qa" && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">🧠 Understanding Check: {topic}</h2>
            <span className="text-xs text-gray-500">Q {qaStep + 1} of {QA_QUESTIONS.length}</span>
          </div>

          <div className="flex gap-2 mb-6">
            {QA_QUESTIONS.map((_, i) => (
              <div key={i} className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${i <= qaStep ? "bg-teal-500" : "bg-black/10"}`} />
            ))}
          </div>

          <div className="glass-card p-6 mb-4">
            <div className="text-xs font-semibold text-teal-400 uppercase tracking-wider mb-2">Open-Ended Question</div>
            <p className="text-gray-800 text-sm">{QA_QUESTIONS[qaStep].text}</p>
          </div>

          {!thoughtResult ? (
            <>
              <div className="glass-card p-4 mb-4">
                <textarea value={qaAnswer} onChange={(e) => setQaAnswer(e.target.value)}
                  placeholder="Explain in your own words..."
                  className="w-full bg-transparent text-gray-900 placeholder-gray-500 outline-none text-sm resize-none min-h-[100px]" />
              </div>
              <div className="flex gap-3 justify-end">
                <button onClick={() => startPractice()}
                  className="px-4 py-2 rounded-full border border-black/10 text-gray-500 text-xs hover:bg-black/5 transition-smooth">
                  Skip Q&A
                </button>
                <button onClick={submitQA} disabled={qaLoading || !qaAnswer.trim()}
                  className="px-5 py-2.5 rounded-full bg-gradient-to-r from-teal-600 to-teal-600 text-gray-900 text-sm font-medium transition-smooth disabled:opacity-40">
                  {qaLoading ? "Analyzing..." : "Submit Explanation"}
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Understanding Feedback */}
              <div className="glass-card p-5 mb-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`text-3xl font-bold ${(thoughtResult.understanding_score ?? 0) >= 70 ? "text-emerald-400" : (thoughtResult.understanding_score ?? 0) >= 40 ? "text-amber-400" : "text-red-400"}`}>
                    {thoughtResult.understanding_score}%
                  </div>
                  <div>
                    <div className="text-sm text-gray-900 font-medium">Understanding</div>
                    <div className="text-xs text-gray-500">Style: <span className="text-emerald-400">{thoughtResult.detected_style}</span></div>
                  </div>
                </div>
                <p className="text-sm text-gray-700 mb-3">{thoughtResult.understanding_feedback}</p>
                {thoughtResult.missing_concepts && thoughtResult.missing_concepts.length > 0 && (
                  <div className="text-xs text-amber-400 mt-2">
                    Missing: {thoughtResult.missing_concepts.join(", ")}
                  </div>
                )}
              </div>

              {/* Thought Pattern Bars */}
              <div className="glass-card p-5 mb-4">
                <div className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">🧠 Your Thinking Pattern</div>
                <div className="space-y-2">
                  {Object.entries(thoughtResult.thought_patterns || {}).map(([key, val]) => (
                    <div key={key}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-600 capitalize">{key.replace(/_/g, " ")}</span>
                        <span className="text-gray-500">{val}%</span>
                      </div>
                      <div className="w-full bg-black/5 rounded-full h-1.5">
                        <div className="h-1.5 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-700" style={{ width: `${val}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Personalization Hints */}
              {thoughtResult.personalization_hints && (
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 mb-4">
                  <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2"> How I'll Teach You</div>
                  <p className="text-sm text-gray-700 mb-1">📌 {thoughtResult.personalization_hints.preferred_examples}</p>
                  <p className="text-sm text-gray-700 mb-1">📖 {thoughtResult.personalization_hints.explanation_approach}</p>
                </div>
              )}

              {/* Encouragement */}
              {thoughtResult.encouragement && (
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 mb-4">
                  <p className="text-sm text-emerald-300">💪 {thoughtResult.encouragement}</p>
                </div>
              )}

              <div className="flex gap-3 justify-end">
                <button onClick={nextQAOrPractice}
                  className="px-5 py-2.5 rounded-full bg-gradient-to-r from-emerald-600 to-green-600 text-gray-900 text-sm font-medium transition-smooth glow">
                  {qaStep < QA_QUESTIONS.length - 1 ? "Next Question " : " Start Practice"}
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Phase: Practice */}
      {(phase === "practice" || phase === "hint") && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900"> Practice: {topic}</h2>
            <div className="flex items-center gap-3 text-xs text-gray-500">
              <span>Difficulty: <span className="text-emerald-400">{difficulty}</span></span>
              <span>Hints: <span className="text-amber-400">{hintsUsed}</span></span>
              <span>Attempts: <span className="text-teal-400">{attempts}</span></span>
            </div>
          </div>

          <div className="glass-card p-6 mb-4">
            <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Question</div>
            <p className="text-gray-800 text-sm leading-relaxed">{question}</p>
          </div>

          {/* Show hint if in hint phase */}
          {phase === "hint" && hintText && (
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-4">
              <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1">
                💡 Hint {hintsUsed}
              </div>
              <p className="text-sm text-gray-700">{hintText}</p>
            </div>
          )}

          {/* Answer input */}
          <div className="glass-card p-4 mb-4">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer here..."
              className="w-full bg-transparent text-gray-900 placeholder-gray-500 outline-none text-sm resize-none min-h-[80px]"
            />
          </div>

          <div className="flex gap-3 justify-end">
            <button onClick={requestHint} disabled={loading}
              className="px-5 py-2.5 rounded-full border border-amber-500/30 text-amber-400 text-sm hover:bg-amber-500/10 transition-smooth disabled:opacity-40">
              {loading ? "..." : "💡 Need Hint"}
            </button>
            <button onClick={() => setPhase("practice")} disabled={phase !== "hint"}
              className="px-5 py-2.5 rounded-full border border-black/10 text-gray-600 text-sm hover:bg-black/5 transition-smooth disabled:opacity-40">
              Try Again
            </button>
            <button onClick={submitAnswer} disabled={loading || !answer.trim()}
              className="px-5 py-2.5 rounded-full bg-gradient-to-r from-emerald-600 to-green-600 text-gray-900 text-sm font-medium transition-smooth disabled:opacity-40">
              {loading ? "Checking..." : " Submit"}
            </button>
          </div>
        </div>
      )}

      {/* Phase: Evaluate */}
      {phase === "evaluate" && evalResult && (
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-6">📝 Results: {topic}</h2>

          <div className="glass-card p-6 mb-4">
            <div className={`text-2xl font-bold mb-2 ${evalResult.assessment === "Correct" ? "text-emerald-400" :
              evalResult.assessment === "Partially Correct" ? "text-amber-400" : "text-red-400"
              }`}>
              {evalResult.assessment === "Correct" ? " Correct!" :
                evalResult.assessment === "Partially Correct" ? " Partially Correct" : " Incorrect"}
            </div>
            <p className="text-sm text-gray-700 mb-3">{String(evalResult.feedback || "")}</p>
            {evalResult.improvement_tip ? (
              <p className="text-sm text-emerald-300">💡 Tip: {String(evalResult.improvement_tip)}</p>
            ) : null}
          </div>

          {/* Stats card */}
          <div className="glass-card p-4 mb-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-xl font-bold text-teal-400">{attempts}</div>
                <div className="text-xs text-gray-500">Attempts</div>
              </div>
              <div>
                <div className="text-xl font-bold text-amber-400">{hintsUsed}</div>
                <div className="text-xs text-gray-500">Hints Used</div>
              </div>
              <div>
                <div className="text-xl font-bold text-emerald-400">
                  {hintsUsed === 0 ? "+35" : `+${Math.max(0, 15 - hintsUsed * 5)}`}
                </div>
                <div className="text-xs text-gray-500">Score Delta</div>
              </div>
            </div>
          </div>

          {/* Mastery update */}
          {masteryData && (
            <div className="glass-card p-6 mb-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">{topic} Mastery</h3>
                <span className="text-sm font-bold text-emerald-400">{masteryData.score.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-black/5 rounded-full h-3 mb-2 overflow-hidden">
                <div
                  className="h-3 rounded-full bg-gradient-to-r from-emerald-500 to-green-500 transition-all duration-1000"
                  style={{ width: `${masteryData.score}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>{masteryData.prevScore.toFixed(1)}% {masteryData.score.toFixed(1)}%</span>
                <span className="capitalize text-emerald-400">{masteryData.level}</span>
              </div>
            </div>
          )}

          <div className="flex gap-3 justify-end">
            <button onClick={() => setPhase("topic")}
              className="px-5 py-2.5 rounded-full border border-black/10 text-gray-600 text-sm hover:bg-black/5 transition-smooth">
              New Topic
            </button>
            <button onClick={startPractice}
              className="px-5 py-2.5 rounded-full bg-gradient-to-r from-emerald-600 to-green-600 text-gray-900 text-sm font-medium transition-smooth">
              Next Question 
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
