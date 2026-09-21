"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowRight, BookOpen, Brain, Check, ChevronRight, CircleHelp, Compass, GitBranch, Moon, RotateCcw, ShieldCheck, Sparkles, Target } from "lucide-react";

type View = "goal" | "mission" | "diagnostic" | "home" | "lesson" | "feedback" | "report";
type Mission = { id: string; objective: string; outcome: string; depth: number; depth_label: string; estimated_hours: string; prerequisites: string[]; target_capabilities: string[]; course_version: string };

const fallbackMission: Mission = {
  id: "offline-demo", objective: "I want to learn LLM fine-tuning.", outcome: "Independent implementation and design competency", depth: 3,
  depth_label: "Professional", estimated_hours: "24–30 focused hours", course_version: "2026.09",
  prerequisites: ["Transformer fundamentals", "PyTorch basics", "LLM inference concepts"],
  target_capabilities: ["Decide whether fine-tuning is appropriate", "Choose SFT, LoRA, QLoRA, RAG, or prompting", "Prepare and validate datasets", "Configure and debug training", "Evaluate results and trade-offs", "Serve adapters"],
};

const skillRows = [
  ["Decisions", 5, "Stable"], ["Dataset design", 4, "Developing"], ["LoRA", 4, "Developing"], ["QLoRA", 3, "Developing"], ["Evaluation", 2, "Needs attention"], ["Production", 1, "Needs attention"],
] as const;

const api = async <T,>(path: string, options?: RequestInit): Promise<T> => {
  const response = await fetch(`/backend/v1${path}`, { ...options, headers: { "Content-Type": "application/json", "X-User-ID": "demo-user", ...(options?.headers ?? {}) } });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
};

function Header({ onHome }: { onHome: () => void }) {
  return <header className="topbar shell">
    <button onClick={onHome} className="brand" style={{ border: 0, background: "transparent", color: "inherit" }} aria-label="Arc home">
      <span className="brand-mark"><GitBranch size={17} aria-hidden /></span> Arc
    </button>
    <div className="top-actions"><span className="muted" style={{ fontSize: ".82rem" }}>Evidence, not completion</span><button className="icon-btn" aria-label="Theme follows system"><Moon size={17} /></button></div>
  </header>;
}

function Rail({ active }: { active: View }) {
  const items = [["home", Compass, "Today"], ["mission", Target, "Mission"], ["lesson", BookOpen, "Learn"], ["report", Brain, "Skill report"]] as const;
  return <nav className="rail" aria-label="Learning navigation">{items.map(([id, Icon, label]) => <div key={id} className={`rail-item ${active === id ? "active" : ""}`}><Icon size={17} />{label}</div>)}</nav>;
}

export function LearningApp() {
  const [view, setView] = useState<View>("goal");
  const [goal, setGoal] = useState("I want to learn LLM fine-tuning well enough to make good training decisions and implement it professionally.");
  const [mission, setMission] = useState<Mission>(fallbackMission);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [answer, setAnswer] = useState("");
  const [confidence, setConfidence] = useState(0);
  const [hint, setHint] = useState(0);
  const [result, setResult] = useState<{ misconception?: string; next_action?: string; updated?: number } | null>(null);
  const answeredCorrectly = answer === "B";

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [view]);

  const createMission = async () => {
    if (goal.trim().length < 8) return;
    setBusy(true); setError("");
    try {
      const created = await api<Mission>("/missions", { method: "POST", body: JSON.stringify({ objective: goal, hours_per_week: 5, prior_experience: "some", intensity: "focused", depth: "auto" }) });
      setMission(created);
    } catch {
      setMission({ ...fallbackMission, objective: goal });
      setError("The API is offline, so this preview is using the deterministic demo mission.");
    } finally { setBusy(false); setView("mission"); }
  };

  const submitLesson = async () => {
    if (!answer || !confidence) return;
    const correctness = answeredCorrectly ? 1 : 0.2;
    const body = { skill_id: "qlora", dimension: "debugging", assessment_type: "scenario", mode: "learning", difficulty: .72, correctness, hint_level: hint, learner_confidence: confidence, independent: hint === 0, answer: { selected: answer } };
    try {
      const update = await api<{ misconception_detected?: string; next_action: string; updated: number }>("/evidence", { method: "POST", body: JSON.stringify(body) });
      setResult({ misconception: update.misconception_detected, next_action: update.next_action, updated: update.updated });
    } catch {
      setResult({ misconception: !answeredCorrectly && confidence >= .75 ? "Quantized storage vs trainable parameters" : undefined, next_action: answeredCorrectly ? "interleaved_application" : "targeted_remediation", updated: answeredCorrectly ? .58 : .37 });
    }
    setView("feedback");
  };

  const content = useMemo(() => {
    if (view === "goal") return <main className="shell hero">
      <span className="eyebrow">Adaptive learning · V1</span>
      <h1 className="display">What do you want to be able to do?</h1>
      <p className="lede">Arc builds the shortest defensible path from an objective to independent capability. It will ask you to retrieve, reason, debug, and transfer—not just read.</p>
      <div className="goal-card">
        <textarea aria-label="Learning goal" value={goal} onChange={(event) => setGoal(event.target.value)} placeholder="I want to learn…" />
        <div className="goal-actions"><span className="muted" style={{ fontSize: ".84rem" }}>Depth, prerequisites, and pace adapt after diagnosis.</span><button className="btn btn-primary" onClick={createMission} disabled={busy}>{busy ? "Building mission…" : "Shape my mission"}<ArrowRight size={17} /></button></div>
      </div>
      {error && <p className="notice">{error}</p>}
      <section className="steps" aria-label="How Arc works">
        <div className="step"><Target size={19} /><strong>Define capability</strong><span className="muted">A concrete outcome, not a topic list.</span></div>
        <div className="step"><GitBranch size={19} /><strong>Find the shortest path</strong><span className="muted">Diagnose prerequisites and skip proven skills.</span></div>
        <div className="step"><ShieldCheck size={19} /><strong>Prove independence</strong><span className="muted">Novel problems, a project, and a viva.</span></div>
      </section>
    </main>;

    if (view === "mission") return <AppFrame active={view}><section className="panel">
      <span className="eyebrow">Learning mission · Ready to review</span><h1>{mission.objective.replace(/^I want to learn /i, "").replace(/\.$/, "")}</h1>
      <p className="lede">The system interpreted your goal as <strong style={{ color: "var(--ink)" }}>{mission.depth_label.toLowerCase()} capability</strong>: you should be able to make and defend training decisions, implement them, and debug failures.</p>
      <div className="grid-2" style={{ marginTop: 26 }}><div className="metric"><small>Selected depth</small><strong>{mission.depth} · {mission.depth_label}</strong></div><div className="metric"><small>Estimated effort</small><strong>{mission.estimated_hours}</strong></div><div className="metric"><small>Course version</small><strong>{mission.course_version}</strong></div><div className="metric"><small>Research status</small><strong>Verified 21 Sep 2026</strong></div></div>
      <div className="chip-row">{mission.prerequisites.map((item) => <span className="chip" key={item}>{item}</span>)}</div>
      <h2>Target capabilities</h2><ul className="capabilities">{mission.target_capabilities.map((item) => <li key={item}><Check size={17} color="var(--accent)" />{item}</li>)}</ul>
      <div className="panel-footer"><button className="btn btn-ghost" onClick={() => setView("goal")}>Edit mission</button><button className="btn btn-primary" onClick={() => setView("diagnostic")}>Begin diagnostic <ArrowRight size={17} /></button></div>
    </section></AppFrame>;

    if (view === "diagnostic") return <AppFrame active={view}><section className="panel">
      <span className="eyebrow">Diagnostic · 1 of 3</span><div className="progress" style={{ marginTop: 14 }}><span style={{ width: "33%" }} /></div>
      <p className="question">A team wants a model to answer from fresh private documents updated every hour. What would you try first—and what evidence might change your mind?</p>
      <div className="scenario">There is no single keyword answer. We are looking for your assumptions, trade-offs, and whether you request missing information.</div>
      <textarea aria-label="Diagnostic answer" style={{ width: "100%", minHeight: 130, marginTop: 22, border: "1px solid var(--line)", borderRadius: 12, padding: 15, background: "transparent", color: "var(--ink)" }} placeholder="Explain your reasoning briefly…" />
      <div className="panel-footer"><span className="muted">It is useful to say “I don’t know.”</span><button className="btn btn-primary" onClick={() => setView("home")}>Submit diagnostic <ArrowRight size={17} /></button></div>
    </section></AppFrame>;

    if (view === "home") return <AppFrame active={view}><section className="panel">
      <span className="eyebrow">Monday · Recommended session</span><h1>Good morning.</h1><p className="lede">Twenty-two focused minutes will reinforce one older skill, test a prior misconception, and move QLoRA forward.</p>
      <div className="grid-2" style={{ margin: "28px 0" }}><div className="metric"><small>Memory queue</small><strong>4 concepts due</strong></div><div className="metric"><small>Previous misconception</small><strong>1 novel recheck</strong></div></div>
      <div className="capabilities">{[["Retrieval", "Prompting vs RAG vs fine-tuning · 3 min"], ["Current lesson", "QLoRA memory model · 9 min"], ["Misconception check", "Storage vs trainable weights · 3 min"], ["Transfer", "14B model on 16 GB · 7 min"]].map(([label, detail]) => <div className="metric" key={label}><small>{label}</small><strong>{detail}</strong></div>)}</div>
      <div className="panel-footer"><span className="muted">The queue adapts after every attempt.</span><button className="btn btn-primary" onClick={() => setView("lesson")}>Start 22-minute session <ArrowRight size={17} /></button></div>
    </section></AppFrame>;

    if (view === "lesson") return <AppFrame active={view}><section className="panel">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}><span className="eyebrow">QLoRA · Debugging 3/6</span><span className="muted" style={{ fontSize: ".78rem" }}>Learning mode</span></div>
      <p className="question">A 14B model OOMs during full fine-tuning on one 16 GB GPU. Which change most directly reduces memory while preserving trainable adaptation?</p>
      <div className="scenario"><strong>Constraints:</strong> 20,000 instruction examples · one 16 GB GPU · behavior adaptation · no latency requirement yet.</div>
      <div className="options">{[["A", "Reduce the learning rate"], ["B", "Load the base model in 4-bit and train low-rank adapters"], ["C", "Increase sequence length to reduce padding"], ["D", "Move the validation set to CPU"]].map(([key, label]) => <button key={key} className={`option ${answer === key ? "selected" : ""}`} onClick={() => setAnswer(key)}><strong>{key}</strong> · {label}</button>)}</div>
      <p style={{ fontWeight: 750 }}>How confident are you?</p><div className="confidence">{[[.2, "Guessing"], [.5, "Somewhat sure"], [.8, "Confident"], [1, "Very confident"]].map(([value, label]) => <button key={label} className={confidence === value ? "selected" : ""} onClick={() => setConfidence(value as number)}>{label}</button>)}</div>
      {hint > 0 && <div className="feedback"><strong>Hint {hint}</strong><br />{hint === 1 ? "Which option changes the states that must remain in high precision during training?" : hint === 2 ? "QLoRA separates quantized base-model storage from trainable adapter parameters." : "Focus on which weights receive gradients, not only how the checkpoint is stored."}</div>}
      <div className="panel-footer"><button className="btn btn-ghost" onClick={() => setHint((value) => Math.min(3, value + 1))}><CircleHelp size={17} /> Hint {hint ? `${hint}/5` : ""}</button><button className="btn btn-primary" disabled={!answer || !confidence} onClick={submitLesson}>Commit answer <ArrowRight size={17} /></button></div>
    </section></AppFrame>;

    if (view === "feedback") return <AppFrame active={view}><section className="panel">
      <span className="eyebrow">Diagnostic feedback</span><h1>{answeredCorrectly ? "Correct—with a caveat." : "This reveals a useful gap."}</h1>
      <p className="lede">{answeredCorrectly ? "QLoRA quantizes the frozen base model for storage and compute while keeping small adapter parameters trainable. The mechanism—not the label—is the important part." : "The selected intervention does not materially reduce the memory held by trainable model states. Because your confidence was high, Arc records this as a probable misconception rather than a simple miss."}</p>
      <div className="feedback"><strong>{result?.misconception ? "Probable misconception" : "Evidence recorded"}</strong><br />{result?.misconception ?? "Independent debugging evidence strengthened."}<br /><span className="muted">Related prerequisite: mixed-precision training · Next: {result?.next_action?.replaceAll("_", " ")}</span></div>
      <h2 style={{ marginTop: 28 }}>Micro-teach</h2><p className="lede">Quantizing a frozen base model reduces its memory footprint. LoRA then adds small trainable matrices. Optimizer states and gradients are maintained for those adapters—not every base-model weight. These are separate ideas: <em>how weights are stored</em> and <em>which parameters are trained</em>.</p>
      <div className="grid-2" style={{ marginTop: 20 }}><div className="metric"><small>Base model</small><strong>4-bit · frozen</strong></div><div className="metric"><small>Adapters</small><strong>Higher precision · trainable</strong></div></div>
      <div className="panel-footer"><button className="btn btn-ghost" onClick={() => { setView("lesson"); setAnswer(""); setConfidence(0); setHint(0); }}>Try a novel recheck <RotateCcw size={17} /></button><button className="btn btn-primary" onClick={() => setView("report")}>View skill evidence <ArrowRight size={17} /></button></div>
    </section></AppFrame>;

    return <AppFrame active={view}><section className="panel">
      <span className="eyebrow">Skill report · Evidence based</span><h1>What you can do now.</h1><p className="lede">Reading is not counted as mastery. These estimates come from explanation, implementation, debugging, design, transfer, confidence, and assistance evidence.</p>
      <div style={{ marginTop: 30 }}>{skillRows.map(([name, score, status]) => <div className="skill-row" key={name}><strong>{name}</strong><div className="bars" aria-label={`${score} of 5 evidence strength`}>{[1,2,3,4,5].map((item) => <span key={item} className={`bar-dot ${item <= score ? "on" : ""}`} />)}</div><span className="status">{status}</span></div>)}</div>
      <div className="grid-2" style={{ marginTop: 26 }}><div className="metric"><small>Independent solving</small><strong>Developing · 52%</strong></div><div className="metric"><small>Hint dependency</small><strong>Moderate, trending down</strong></div><div className="metric"><small>Retention confidence</small><strong>Needs another spaced check</strong></div><div className="metric"><small>Next review</small><strong>24 Sep · novel scenario</strong></div></div>
      <div className="panel-footer"><span className="muted">Internal scores are estimates, not scientific probabilities.</span><button className="btn btn-primary" onClick={() => setView("home")}>Return to today <ChevronRight size={17} /></button></div>
    </section></AppFrame>;
  }, [view, goal, mission, busy, error, answer, confidence, hint, result, answeredCorrectly]);

  return <><Header onHome={() => setView(view === "goal" ? "goal" : "home")} />{content}</>;
}

function AppFrame({ active, children }: { active: View; children: React.ReactNode }) {
  return <main className="shell workspace"><Rail active={active} /><div>{children}</div></main>;
}
