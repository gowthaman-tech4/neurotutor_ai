"use client";

import { useState, useRef, useEffect, useCallback } from "react";

const API_URL = "http://localhost:8000/api/engine/route";
const TEST_USER_ID = "8b40ebcf-92aa-43a2-8def-bee49247cebc";

type TaskType = "teach" | "practice" | "hint" | "evaluate";
type LangMode = "bilingual" | "native" | "english";

interface Message {
  role: "user" | "ai";
  content: string;
  engine?: string;
  data?: Record<string, unknown>;
}

const TASK_MODES: { key: TaskType; label: string; placeholder: string }[] = [
  { key: "teach", label: "Teach", placeholder: "Ask me to explain any concept..." },
  { key: "practice", label: "Practice", placeholder: "Request practice questions on a topic..." },
  { key: "hint", label: "Hint", placeholder: "Ask for a hint on your current problem..." },
  { key: "evaluate", label: "Evaluate", placeholder: "Type your answer for evaluation..." },
];

const LANGUAGES = [
  { code: "en", label: "English", speechCode: "en-US" },
  { code: "hi", label: "हिन्दी", speechCode: "hi-IN" },
  { code: "ta", label: "தமிழ்", speechCode: "ta-IN" },
  { code: "te", label: "తెలుగు", speechCode: "te-IN" },
  { code: "kn", label: "ಕನ್ನಡ", speechCode: "kn-IN" },
  { code: "ml", label: "മലയാളം", speechCode: "ml-IN" },
  { code: "bn", label: "বাংলা", speechCode: "bn-IN" },
  { code: "mr", label: "मराठी", speechCode: "mr-IN" },
];

const LANG_MODES: { key: LangMode; label: string }[] = [
  { key: "bilingual", label: "Bilingual" },
  { key: "native", label: "Native Only" },
  { key: "english", label: "English Only" },
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [activeMode, setActiveMode] = useState<TaskType>("teach");
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState("en");
  const [langMode, setLangMode] = useState<LangMode>("bilingual");
  const [isListening, setIsListening] = useState(false);
  const [showLangMenu, setShowLangMenu] = useState(false);
  const [speakingIdx, setSpeakingIdx] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  // Speech Recognition
  const startListening = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech Recognition is not supported in this browser. Try Chrome.");
      return;
    }
    const recognition = new SpeechRecognition();
    const lang = LANGUAGES.find((l) => l.code === language);
    recognition.lang = lang?.speechCode || "en-US";
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = Array.from(event.results).map((r) => r[0].transcript).join("");
      setInput(transcript);
    };
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognition.start();
    recognitionRef.current = recognition;
    setIsListening(true);
  }, [language]);

  const stopListening = () => {
    recognitionRef.current?.stop();
    setIsListening(false);
  };

  // Text-to-Speech
  const speakText = (text: string, idx: number) => {
    if (speakingIdx === idx) {
      window.speechSynthesis.cancel();
      setSpeakingIdx(null);
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const lang = LANGUAGES.find((l) => l.code === language);
    utterance.lang = lang?.speechCode || "en-US";
    utterance.rate = 0.9;
    utterance.onend = () => setSpeakingIdx(null);
    utterance.onerror = () => setSpeakingIdx(null);
    window.speechSynthesis.speak(utterance);
    setSpeakingIdx(idx);
  };

  // Build language preference string for backend
  const getLanguagePref = (): string => {
    const lang = LANGUAGES.find((l) => l.code === language);
    const langName = lang?.label || "English";
    if (language === "en" || langMode === "english") return "English";
    if (langMode === "native") return langName;
    return `Bilingual (${langName} + English) — explain in ${langName} but keep technical terms in English`;
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const taskInput: Record<string, string> = {};
      if (activeMode === "evaluate") {
        taskInput.answer = input;
      } else {
        taskInput.topic = input;
      }

      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_type: activeMode,
          user_profile: {
            user_id: TEST_USER_ID,
            target_exam: "IIT JEE",
            current_class: "12th",
            language_pref: getLanguagePref(),
          },
          learning_state: { mastery_level: "beginner" },
          learning_pattern: { style: "visual" },
          task_input: taskInput,
        }),
      });

      const data = await res.json();
      const output = data.output || {};

      const aiMsg: Message = {
        role: "ai",
        content: formatAIResponse(output, activeMode),
        engine: output.engine || activeMode,
        data: output,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: " Failed to reach the API. Make sure the backend is running on port 8000." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const selectedLang = LANGUAGES.find((l) => l.code === language);

  return (
    <div className="max-w-4xl mx-auto px-4 flex flex-col" style={{ height: "calc(100vh - 5rem)" }}>
      {/* Chat Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto py-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <div className="h-16 w-16 mb-4 text-emerald-600 flex items-center justify-center">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">Start a conversation</h2>
            <p className="text-sm text-gray-500 max-w-sm text-center">
              Choose a mode below, then ask me anything about your studies. I adapt to how you think.
            </p>
            <p className="text-xs text-gray-600 mt-2">
              {selectedLang?.label} • {langMode === "bilingual" ? "Bilingual mode" : langMode === "native" ? "Native only" : "English only"}
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatBubble key={i} message={msg} index={i} speakingIdx={speakingIdx} onSpeak={speakText} />
        ))}

        {loading && (
          <div className="flex items-center gap-3 px-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-green-700 flex items-center justify-center text-gray-900 text-xs font-bold">N</div>
            <div className="glass-card px-4 py-3 rounded-2xl">
              <div className="flex gap-1.5">
                <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Controls Area */}
      <div className="pb-4 space-y-3">
        {/* Mode Tabs + Language Controls */}
        <div className="flex items-center justify-center gap-2 flex-wrap">
          {TASK_MODES.map((mode) => (
            <button key={mode.key} onClick={() => setActiveMode(mode.key)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-smooth ${activeMode === mode.key ? "bg-emerald-600 text-white glow" : "bg-black/5 text-gray-600 hover:bg-black/10 hover:text-gray-900"
                }`}>
              {mode.label}
            </button>
          ))}

          {/* Language Dropdown */}
          <div className="relative">
            <button onClick={() => setShowLangMenu(!showLangMenu)}
              className="px-3 py-2 rounded-full bg-black/5 text-gray-600 hover:bg-black/10 hover:text-gray-900 text-sm font-medium transition-smooth flex items-center gap-1.5">
              {selectedLang?.label}
            </button>
            {showLangMenu && (
              <div className="absolute bottom-12 right-0 glass-card p-3 rounded-xl min-w-[180px] z-50 shadow-xl">
                {/* Languages */}
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 px-2">Language</div>
                {LANGUAGES.map((lang) => (
                  <button key={lang.code}
                    onClick={() => { setLanguage(lang.code); if (lang.code === "en") setLangMode("english"); }}
                    className={`w-full text-left px-3 py-1.5 rounded-lg text-sm transition-smooth ${language === lang.code ? "bg-emerald-600/30 text-emerald-300" : "text-gray-600 hover:bg-black/5 hover:text-gray-900"
                      }`}>
                    {lang.label}
                  </button>
                ))}
                {/* Mode divider */}
                {language !== "en" && (
                  <>
                    <div className="border-t border-black/5 my-2" />
                    <div className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 px-2">Mode</div>
                    {LANG_MODES.map((m) => (
                      <button key={m.key}
                        onClick={() => { setLangMode(m.key); setShowLangMenu(false); }}
                        className={`w-full text-left px-3 py-1.5 rounded-lg text-sm transition-smooth ${langMode === m.key ? "bg-teal-600/30 text-teal-300" : "text-gray-600 hover:bg-black/5 hover:text-gray-900"
                          }`}>
                        {m.label}
                      </button>
                    ))}
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Input Bar */}
        <div className="glass-card flex items-center gap-3 px-4 py-3 glow">
          {/* Mic Button */}
          <button onClick={isListening ? stopListening : startListening}
            className={`w-9 h-9 rounded-full flex items-center justify-center text-sm transition-smooth shrink-0 ${isListening ? "bg-red-500 text-white animate-pulse" : "bg-black/5 text-gray-600 hover:bg-black/10 hover:text-gray-900"
              }`}
            title={isListening ? "Stop listening" : `Voice input (${selectedLang?.label})`}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>
          </button>

          <input type="text" value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder={TASK_MODES.find((m) => m.key === activeMode)?.placeholder}
            className="flex-1 bg-transparent text-gray-900 placeholder-gray-500 outline-none text-sm"
            disabled={loading} />

          <button onClick={sendMessage} disabled={loading || !input.trim()}
            className="px-5 py-2 rounded-full bg-gradient-to-r from-emerald-600 to-green-600 text-gray-900 text-sm font-medium hover:from-emerald-500 hover:to-green-500 transition-smooth disabled:opacity-40 disabled:cursor-not-allowed">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

function ChatBubble({ message, index, speakingIdx, onSpeak }: {
  message: Message; index: number; speakingIdx: number | null;
  onSpeak: (text: string, idx: number) => void;
}) {
  const isUser = message.role === "user";
  const isSpeaking = speakingIdx === index;

  return (
    <div className={`flex items-start gap-3 px-2 ${isUser ? "flex-row-reverse" : ""}`}>
      {isUser ? null : (
        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-emerald-500 to-green-700 text-white text-xs font-bold shrink-0">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
        </div>
      )}
      <div className={`max-w-[75%] rounded-2xl text-sm leading-relaxed ${isUser
        ? "bg-gradient-to-r from-teal-600/10 to-emerald-600/10 border border-teal-500/20 text-gray-900 px-4 py-3"
        : "glass-card text-gray-800 px-4 py-3"
        }`}>
        {!isUser && message.engine && (
          <div className="text-xs text-emerald-400 font-semibold mb-1.5 uppercase tracking-wider">
            {message.engine} Engine
          </div>
        )}
        <div className="whitespace-pre-wrap">{message.content}</div>
        {/* TTS button on AI messages */}
        {!isUser && (
          <button
            onClick={() => onSpeak(message.content, index)}
            className={`mt-2 inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs transition-smooth ${isSpeaking
              ? "bg-emerald-600 text-white"
              : "bg-black/5 text-gray-600 hover:bg-black/10 hover:text-gray-900"
              }`}
            title="Listen to this response"
          >
            {isSpeaking ? " Stop" : "Listen"}
          </button>
        )}
      </div>
    </div>
  );
}

function formatAIResponse(output: Record<string, unknown>, mode: TaskType): string {
  if (output.error_fallback) {
    return `Error: ${output.error_fallback}\n\n${output.feedback || output.explanation || ""}`;
  }

  switch (mode) {
    case "teach": {
      const steps = output.steps as string[] | undefined;
      const example = output.example as string | undefined;
      const quickCheck = output.quick_check as string | undefined;
      let text = "";
      if (steps) text += steps.map((s: string, i: number) => `${i + 1}. ${s}`).join("\n") + "\n\n";
      if (example) text += `💡 Example: ${example}\n\n`;
      if (quickCheck) text += `🧪 Quick Check: ${quickCheck}`;
      return text || JSON.stringify(output, null, 2);
    }
    case "practice": {
      const q = output.question as string | undefined;
      const diff = output.difficulty_assigned as string | undefined;
      let text = "";
      if (q) text += `📝 ${q}\n\n`;
      if (diff) text += `Difficulty: ${diff}`;
      return text || JSON.stringify(output, null, 2);
    }
    case "hint": {
      const hint = output.hint_text as string | undefined;
      const level = output.hint_level as number | undefined;
      const enc = output.next_step_encouragement as string | undefined;
      let text = "";
      if (level) text += `Hint Level ${level}\n`;
      if (hint) text += `💡 ${hint}\n\n`;
      if (enc) text += ` ${enc}`;
      return text || JSON.stringify(output, null, 2);
    }
    case "evaluate": {
      const assessment = output.assessment as string | undefined;
      const feedback = output.feedback as string | undefined;
      const tip = output.improvement_tip as string | undefined;
      let text = "";
      if (assessment) text += `Assessment: ${assessment}\n\n`;
      if (feedback) text += `${feedback}\n\n`;
      if (tip) text += `💡 Tip: ${tip}`;
      return text || JSON.stringify(output, null, 2);
    }
    default:
      return JSON.stringify(output, null, 2);
  }
}
