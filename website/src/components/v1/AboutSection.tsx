"use client";

import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import { X, ShieldCheck, Sparkles } from "lucide-react";
import { ScrollHighlight } from "./ScrollHighlight";
import { sounds } from "../../utils/sound";

const tones = {
  coral: {
    card: "bg-[#E9543F] text-white ring-white/25",
    tag: "bg-white/20 text-white",
    sub: "text-white/80",
    num: "text-white/15",
    glow: "hover:shadow-[0_32px_80px_-24px_rgba(233,84,63,0.65)]",
  },
  sun: {
    card: "bg-[#F2B94B] text-neutral-950 ring-black/10",
    tag: "bg-black/10 text-neutral-900",
    sub: "text-neutral-900/75",
    num: "text-black/10",
    glow: "hover:shadow-[0_32px_80px_-24px_rgba(242,185,75,0.6)]",
  },
  sky: {
    card: "bg-[#5B8DEF] text-white ring-white/25",
    tag: "bg-white/20 text-white",
    sub: "text-white/80",
    num: "text-white/15",
    glow: "hover:shadow-[0_32px_80px_-24px_rgba(91,141,239,0.6)]",
  },
  mint: {
    card: "bg-[#59B98A] text-neutral-950 ring-black/10",
    tag: "bg-black/10 text-neutral-900",
    sub: "text-neutral-900/75",
    num: "text-black/10",
    glow: "hover:shadow-[0_32px_80px_-24px_rgba(89,185,138,0.6)]",
  },
  lilac: {
    card: "bg-[#8E7CC3] text-white ring-white/25",
    tag: "bg-white/20 text-white",
    sub: "text-white/80",
    num: "text-white/15",
    glow: "hover:shadow-[0_32px_80px_-24px_rgba(142,124,195,0.6)]",
  },
  peach: {
    card: "bg-[#E8926A] text-neutral-950 ring-black/10",
    tag: "bg-black/10 text-neutral-900",
    sub: "text-neutral-900/75",
    num: "text-black/10",
    glow: "hover:shadow-[0_32px_80px_-24px_rgba(232,146,106,0.6)]",
  },
  cream: {
    card: "bg-[#F0E6CF] text-neutral-950 ring-black/10",
    tag: "bg-black/10 text-neutral-900",
    sub: "text-neutral-900/75",
    num: "text-black/10",
    glow: "hover:shadow-[0_32px_80px_-24px_rgba(240,230,207,0.6)]",
  },
  ink: {
    card: "bg-[#17171A] text-white ring-white/20",
    tag: "bg-white/10 text-white",
    sub: "text-white/70",
    num: "text-white/10",
    glow: "hover:shadow-[0_32px_80px_-24px_rgba(23,23,26,0.85)]",
  },
} as const;

const topTags = [
  { label: "STATE MACHINE", desc: "Deterministic LangGraph + SQLite Checkpointer" },
  { label: "MANDATORY TDD", desc: "Red-to-Green Reproduction Verification" },
  { label: "3 WORKTREES", desc: "Parallel Tournament Isolated Sandboxes" },
  { label: "LAYA ARBITRATION", desc: "Multiplicative Vetoes + Calibrated ECE 0.0010" },
  { label: "INSTITUTIONAL MEMORY", desc: "76 Verified Solutions + NEVER-DO Veto" },
  { label: "8 INVARIANTS", desc: "Zero NoneType Crashes & Hashability Contracts" },
  { label: "$0.00 INFERENCE", desc: "Groq LPU 500+ t/s + Gemini Flash Frontier" },
  { label: "88.8% AST YIELD", desc: "Pre-Sandbox Static Syntax Gates" },
];

const harnessCards = [
  {
    tag: "01",
    meta: "HYBRID RAG LOCALIZATION",
    title: "5D Relevance Scoring",
    body: "Saturated BM25 (k1=1.5), BGE embeddings, AST definition graphs, and caller hierarchies locate the exact failing symbol.",
    tone: "sky" as const,
  },
  {
    tag: "02",
    meta: "MANDATORY TDD PROOF",
    title: "Reproduce Red First",
    body: "A standalone reproduction test MUST fail on unpatched code. If the unpatched repo passes, ISHA halts immediately.",
    tone: "mint" as const,
  },
  {
    tag: "03",
    meta: "PARALLEL TOURNAMENT",
    title: "3 Isolated Worktrees",
    body: "Minimal-diff, call-site-aware, and root-cause strategies race concurrently. Main branch remains 100% untouched.",
    tone: "lilac" as const,
  },
  {
    tag: "04",
    meta: "AST STATIC GATES",
    title: "Pre-Sandbox Validation",
    body: "Pre-sandbox ast.parse() eliminates indentation errors, missing imports, and broken syntax before Docker execution.",
    tone: "peach" as const,
  },
  {
    tag: "05",
    meta: "CLOSED-LOOP REPAIR",
    title: "Verbatim Pytest Feedback",
    body: "Real traceback lines and container stderr feed directly back into the coder for up to 2 targeted self-repair rounds.",
    tone: "sun" as const,
  },
  {
    tag: "06",
    meta: "CALIBRATED ARBITRATION",
    title: "LAYA Composite Gate",
    body: "Multi-factor scoring rewards surgical hunks with exponential churn penalties and hard vetoes on security or logic drift.",
    tone: "cream" as const,
  },
  {
    tag: "07",
    meta: "INSTITUTIONAL MEMORY",
    title: "NEVER-DO Negative Veto",
    body: "SQLite ground truth + 384-d semantic ledger prevents repeating known container-graded failures across identical repos.",
    tone: "coral" as const,
  },
  {
    tag: "08",
    meta: "PRODUCTION SHIPPING",
    title: "Patch or Automated PR",
    body: "Export unified diffs, apply cleanly with atomic safety, or open an audited GitHub Pull Request with `isha fix --pr`.",
    tone: "ink" as const,
  },
];

const comparisonRows = [
  {
    feature: "Operating Architecture",
    chatbots: "Unconstrained ReAct loop (wandering bash)",
    passive: "Passive prompt & response",
    isha: "Deterministic Directed State Machine Graph",
  },
  {
    feature: "Bug Proof Guarantee",
    chatbots: "Manual or hallucinated test claims",
    passive: "❌ None (left to user)",
    isha: "✅ Mandatory TDD Red-to-Green Proof",
  },
  {
    feature: "Branch Hygiene",
    chatbots: "Pollutes user's active branch",
    passive: "Clipboard copy-paste",
    isha: "✅ 3 Isolated Git Worktrees (.worktrees/)",
  },
  {
    feature: "Strategy Exploration",
    chatbots: "Single trial-and-error trajectory",
    passive: "Single code snippet",
    isha: "✅ 3 Parallel Algorithmic Strategies",
  },
  {
    feature: "Arbitration & Decision Gate",
    chatbots: "Model evaluates its own output",
    passive: "❌ None",
    isha: "✅ Calibrated LAYA External Gate (ECE 0.0010)",
  },
  {
    feature: "Context Extraction",
    chatbots: "Entire files dumped into prompt",
    passive: "Whatever user pastes",
    isha: "✅ AST Call Hierarchy & Verbatim Line Clipping",
  },
  {
    feature: "Institutional Memory",
    chatbots: "Stateless (repeats exact same errors)",
    passive: "❌ None",
    isha: "✅ SQLite + 384-d Semantic Vector + NEVER-DO Veto",
  },
  {
    feature: "Inference Cost per Bug",
    chatbots: "$1.50 – $4.00 per attempt",
    passive: "$20/month subscription",
    isha: "✅ $0.00 Free-Tier Frontier (Groq + Gemini)",
  },
];

const cardClass =
  "group relative flex h-[350px] w-[270px] sm:w-[290px] shrink-0 snap-center flex-col justify-between overflow-hidden rounded-[28px] p-6 text-left ring-1 ring-inset shadow-[0_24px_60px_-28px_rgba(19,35,58,0.45)] transition-all duration-500 ease-out hover:-translate-y-4 hover:shadow-2xl";

export const AboutSection: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeTag, setActiveTag] = useState<string | null>(null);

  return (
    <section
      id="about"
      ref={containerRef}
      className="relative w-full py-24 sm:py-32 md:py-40 px-6 sm:px-10 md:px-16 lg:px-20 bg-[#F9F7EF] dark:bg-black text-black dark:text-[#F9F7EF] transition-colors duration-300 border-t border-b border-neutral-200/60 dark:border-neutral-900/60 overflow-hidden"
    >
      <div className="max-w-7xl mx-auto relative z-10">
        {/* ================= TOP SECTION LABEL & INTERACTIVE PILL TAGS ================= */}
        <div className="mb-10 sm:mb-14 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs sm:text-sm font-mono uppercase tracking-[0.3em] text-neutral-500 dark:text-neutral-400 font-extrabold">
              WHAT ISHA IS · ARCHITECTURAL SPECIFICATION
            </span>
            <span className="font-mono text-[11px] font-bold text-red-600 dark:text-red-500 uppercase tracking-widest hidden sm:inline">
              PROD VERSION 0.1.0
            </span>
          </div>

          {/* Interactive Right Tags Bar */}
          <div className="flex flex-wrap items-center gap-2 pt-2">
            {topTags.map((tag) => (
              <button
                key={tag.label}
                type="button"
                onClick={() => {
                  sounds.playClick();
                  setActiveTag(activeTag === tag.label ? null : tag.label);
                }}
                className={`group px-3 py-1.5 rounded-full text-[10px] sm:text-[11px] font-mono font-black uppercase tracking-wider transition-all cursor-pointer border ${
                  activeTag === tag.label
                    ? "bg-red-600 text-white border-red-600 shadow-md shadow-red-600/30 scale-105"
                    : "bg-white/90 dark:bg-neutral-900/90 text-neutral-700 dark:text-neutral-300 border-neutral-300 dark:border-neutral-800 hover:border-red-600 dark:hover:border-red-500 hover:text-red-600"
                }`}
                title={tag.desc}
              >
                <span>{tag.label}</span>
                <span className="ml-1.5 text-[9px] opacity-60 group-hover:opacity-100">
                  {activeTag === tag.label ? "✓" : "•"}
                </span>
              </button>
            ))}
          </div>

          {/* Active Tag Descriptor Drawer */}
          {activeTag && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3.5 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-xs font-mono font-bold text-neutral-700 dark:text-neutral-300 flex items-center justify-between gap-3 shadow-md"
            >
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-red-600 shrink-0" />
                <span className="text-red-600 uppercase font-black">{activeTag}:</span>
                <span>{topTags.find((t) => t.label === activeTag)?.desc}</span>
              </div>
              <button
                type="button"
                onClick={() => setActiveTag(null)}
                className="text-neutral-400 hover:text-neutral-900 dark:hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          )}
        </div>

        {/* ================= MAIN EDITORIAL GRID ================= */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-14 items-start">
          {/* ================= LEFT COLUMN: BIG BOLD EDITORIAL SPEC ================= */}
          <div className="lg:col-span-8 space-y-6">
            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-[52px] font-black tracking-tight text-neutral-950 dark:text-neutral-100 leading-[1.28] sm:leading-[1.24] md:leading-[1.2]">
              ISHA is a deterministic software-engineering state machine that turns an issue into a{" "}
              <ScrollHighlight variant="brush" color="sky" delay={0.1}>
                mathematically verified pull request
              </ScrollHighlight>
              . It localizes code across 5 AST dimensions, proves the bug with a{" "}
              <ScrollHighlight variant="round" color="coral" delay={0.25} strokeWidth={3.5}>
                mandatory failing TDD test
              </ScrollHighlight>
              , races{" "}
              <ScrollHighlight variant="wavy" color="sun" delay={0.35}>
                three parallel strategies
              </ScrollHighlight>{" "}
              in isolated Git worktrees, and merges only the minimal diff that passes pre-sandbox compilation, Docker regression tests, and the{" "}
              <ScrollHighlight variant="double" color="red" delay={0.55} strokeWidth={3}>
                calibrated LAYA arbitration gate
              </ScrollHighlight>
              .
            </h2>

            <p className="max-w-3xl text-base sm:text-lg font-bold leading-relaxed text-neutral-700 dark:text-neutral-300">
              Unlike conversational chatbots that aimlessly edit live files and guess in terminal bash loops, ISHA enforces an empirical scientific process:{" "}
              <span className="text-red-600 dark:text-red-500 font-black">
                Never touch code without proving the bug exists first
              </span>
              ,{" "}
              <span className="text-neutral-900 dark:text-white font-black">
                never mutate the user&apos;s active branch
              </span>
              , and{" "}
              <span className="text-neutral-900 dark:text-white font-black">
                never accept a patch without clean regression proofs
              </span>
              .
            </p>

            {/* Key Verified Performance Callouts */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4">
              <div className="p-4 rounded-2xl bg-white/80 dark:bg-neutral-900/80 border border-neutral-200/80 dark:border-neutral-800 shadow-sm">
                <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-500 font-extrabold block">
                  SWE-bench Lite
                </span>
                <span className="text-2xl sm:text-3xl font-black text-red-600 dark:text-red-500 mt-1 block">
                  76 / 300
                </span>
                <span className="text-[11px] font-bold text-neutral-600 dark:text-neutral-400 mt-1 block">
                  Official Docker Resolved
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-white/80 dark:bg-neutral-900/80 border border-neutral-200/80 dark:border-neutral-800 shadow-sm">
                <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-500 font-extrabold block">
                  AST Patch Yield
                </span>
                <span className="text-2xl sm:text-3xl font-black text-neutral-900 dark:text-white mt-1 block">
                  88.8%
                </span>
                <span className="text-[11px] font-bold text-neutral-600 dark:text-neutral-400 mt-1 block">
                  Zero Syntax Defects
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-white/80 dark:bg-neutral-900/80 border border-neutral-200/80 dark:border-neutral-800 shadow-sm">
                <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-500 font-extrabold block">
                  LAYA Calibration
                </span>
                <span className="text-2xl sm:text-3xl font-black text-neutral-900 dark:text-white mt-1 block">
                  0.0010
                </span>
                <span className="text-[11px] font-bold text-neutral-600 dark:text-neutral-400 mt-1 block">
                  Empirical Calibration Error
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-white/80 dark:bg-neutral-900/80 border border-neutral-200/80 dark:border-neutral-800 shadow-sm">
                <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-500 font-extrabold block">
                  Inference Cost
                </span>
                <span className="text-2xl sm:text-3xl font-black text-emerald-600 dark:text-emerald-400 mt-1 block">
                  $0.00
                </span>
                <span className="text-[11px] font-bold text-neutral-600 dark:text-neutral-400 mt-1 block">
                  Free-Tier Pareto Frontier
                </span>
              </div>
            </div>

            {/* Direct CTA Action Links */}
            <div className="pt-2 flex flex-wrap items-center gap-3">
              <a
                href="/fix"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-red-600 hover:bg-red-700 text-white text-xs font-black uppercase tracking-wider shadow-lg shadow-red-600/25 hover:scale-105 active:scale-95 transition-all"
              >
                <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                TRY ISHA FIX IN BROWSER
              </a>
              <a
                href="/stats"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full border-2 border-neutral-300 dark:border-neutral-700 hover:border-red-600 dark:hover:border-red-500 text-neutral-900 dark:text-neutral-100 hover:text-red-600 dark:hover:text-red-400 text-xs font-black uppercase tracking-wider hover:scale-105 active:scale-95 transition-all"
              >
                AUDITED BENCHMARKS ↗
              </a>
            </div>
          </div>

          {/* ================= RIGHT COLUMN: INTERACTIVE TILTED STICKY NOTES ================= */}
          <div className="lg:col-span-4 relative flex flex-col items-center lg:items-end gap-5 pt-4 lg:pt-0">
            <div className="flex items-center gap-2 text-xs font-mono text-neutral-500 dark:text-neutral-400 font-bold self-center lg:self-end pr-4">
              <span>drag these notes ;)</span>
              <span className="text-sm">↗</span>
            </div>

            {/* Note 1: Yellow Sticky Note - SWE-bench Lite */}
            <motion.div
              drag
              dragConstraints={containerRef}
              dragElastic={0.15}
              whileDrag={{ scale: 1.05, cursor: "grabbing" }}
              whileHover={{ rotate: 0, scale: 1.02 }}
              onDragStart={() => sounds.playClick()}
              initial={{ rotate: -2 }}
              className="relative w-64 sm:w-76 bg-[#FFF4CC] dark:bg-[#FFF4CC] text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-10"
            >
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-white/70 backdrop-blur-xs shadow-xs -rotate-1 border border-white/50" />
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider font-extrabold text-neutral-600">
                  SWE-BENCH LITE GOLDEN
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-400/30 text-amber-900 font-black">
                  76 RESOLVED
                </span>
              </div>
              <p className="text-base font-extrabold leading-snug tracking-tight text-neutral-900">
                76 / 300 official Docker resolved.
                <br />
                88.8% clean AST yield.
                <br />
                0.0% patch abort rate.
              </p>
              <div className="mt-4 pt-3 border-t border-neutral-900/10 text-[10px] font-mono uppercase tracking-widest text-neutral-600 font-black">
                CONTAINER-GRADED VERIFICATION
              </div>
            </motion.div>

            {/* Note 2: Peach Sticky Note - 8 Container Invariants */}
            <motion.div
              drag
              dragConstraints={containerRef}
              dragElastic={0.15}
              whileDrag={{ scale: 1.05, cursor: "grabbing" }}
              whileHover={{ rotate: 0, scale: 1.02 }}
              onDragStart={() => sounds.playClick()}
              initial={{ rotate: 2 }}
              className="relative w-64 sm:w-76 bg-[#FFE8E2] dark:bg-[#FFE8E2] text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-20"
            >
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-white/70 backdrop-blur-xs shadow-xs rotate-2 border border-white/50" />
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider font-extrabold text-neutral-600">
                  AST & CONTAINER HARDENING
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-red-500/20 text-red-800 font-black">
                  8 INVARIANTS
                </span>
              </div>
              <p className="text-base font-extrabold leading-snug tracking-tight text-neutral-900">
                Class anchoring & guard completeness.
                <br />
                Immutable hashability contracts.
                <br />
                Strict qualname hierarchy.
              </p>
              <div className="mt-4 pt-3 border-t border-neutral-900/10 text-[10px] font-mono uppercase tracking-widest text-neutral-600 font-black">
                ZERO NONETYPE CRASHES
              </div>
            </motion.div>

            {/* Note 3: White Sticker Note - Dual Memory & NEVER-DO */}
            <motion.div
              drag
              dragConstraints={containerRef}
              dragElastic={0.15}
              whileDrag={{ scale: 1.05, cursor: "grabbing" }}
              whileHover={{ rotate: 0, scale: 1.02 }}
              onDragStart={() => sounds.playClick()}
              initial={{ rotate: -1.5 }}
              className="relative w-64 sm:w-76 bg-white dark:bg-neutral-100 text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-30"
            >
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-white/80 backdrop-blur-xs shadow-xs -rotate-2 border border-neutral-200/60" />
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider font-extrabold text-neutral-500">
                  INSTITUTIONAL MEMORY
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-800 font-black">
                  NEVER-DO VETO
                </span>
              </div>
              <p className="text-base font-extrabold leading-snug tracking-tight text-neutral-900">
                SQLite ground truth ledger.
                <br />
                384-d semantic vector index.
                <br />
                Cosine similarity &gt;0.92 vetoes prior failed strategies.
              </p>
              <div className="mt-4 pt-3 border-t border-neutral-200 text-[10px] font-mono uppercase tracking-widest text-neutral-500 font-black">
                SENIOR TENURE EFFECT
              </div>
            </motion.div>

            {/* Note 4: Mint Green Note - Free-Tier Pareto Engine */}
            <motion.div
              drag
              dragConstraints={containerRef}
              dragElastic={0.15}
              whileDrag={{ scale: 1.05, cursor: "grabbing" }}
              whileHover={{ rotate: 0, scale: 1.02 }}
              onDragStart={() => sounds.playClick()}
              initial={{ rotate: 1.5 }}
              className="relative w-64 sm:w-76 bg-[#E3F5EC] dark:bg-[#E3F5EC] text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-40"
            >
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-white/70 backdrop-blur-xs shadow-xs rotate-1 border border-white/50" />
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider font-extrabold text-neutral-600">
                  ASYMMETRIC GATEWAY
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-800 font-black">
                  $0.00 INFERENCE
                </span>
              </div>
              <p className="text-base font-extrabold leading-snug tracking-tight text-neutral-900 mb-3">
                500+ tokens/sec Groq LPU.
                <br />
                Gemini Flash reasoning.
                <br />
                LAYA ECE 0.0010.
              </p>
              <div className="flex items-center gap-1.5">
                <span className="px-2 py-0.5 rounded bg-[#F05A28] text-white font-black text-[10px] tracking-tight">
                  Groq
                </span>
                <span className="px-2 py-0.5 rounded bg-[#1A73E8] text-white font-black text-[10px] tracking-tight">
                  Gemini
                </span>
                <span className="px-2 py-0.5 rounded bg-[#2496ED] text-white font-black text-[10px] tracking-tight">
                  Docker
                </span>
              </div>
              <div className="mt-4 pt-3 border-t border-emerald-900/10 text-[10px] font-mono uppercase tracking-widest text-emerald-800 font-black">
                ZERO VENDOR LOCK-IN
              </div>
            </motion.div>
          </div>
        </div>

        {/* ================= ARCHITECTURE COMPARISON TABLE ================= */}
        <div className="mt-24 sm:mt-32 pt-16 border-t border-neutral-300 dark:border-neutral-800">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-600/10 text-red-600 dark:text-red-400 border border-red-600/20 text-xs font-mono font-black tracking-widest uppercase mb-3">
              <ShieldCheck className="w-3.5 h-3.5" />
              INDUSTRY ARCHITECTURAL COMPARISON
            </span>
            <h3 className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight text-neutral-950 dark:text-neutral-100">
              Why ISHA Differs From Conversational Agents
            </h3>
            <p className="mt-3 text-sm sm:text-base font-bold text-neutral-600 dark:text-neutral-400 leading-relaxed">
              Most coding assistants act like humans typing in bash, wandering through files and breaking existing functionality. ISHA is an autonomous, test-driven state machine.
            </p>
          </div>

          <div className="w-full overflow-x-auto rounded-3xl border border-neutral-300 dark:border-neutral-800 bg-white/70 dark:bg-neutral-950/70 shadow-xl backdrop-blur-md">
            <table className="w-full text-left border-collapse text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-neutral-300 dark:border-neutral-800 bg-neutral-100/80 dark:bg-neutral-900/80 font-mono text-[11px] sm:text-xs uppercase tracking-wider text-neutral-600 dark:text-neutral-400">
                  <th className="py-4 px-4 sm:px-6 font-black">Architectural Feature</th>
                  <th className="py-4 px-4 sm:px-6 font-black text-neutral-500">Conversational (Claude Code / OpenHands)</th>
                  <th className="py-4 px-4 sm:px-6 font-black text-neutral-500">Passive (Copilot / ChatGPT)</th>
                  <th className="py-4 px-4 sm:px-6 font-black text-red-600 dark:text-red-400 bg-red-500/5 dark:bg-red-500/10">
                    ISHA Harness
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 dark:divide-neutral-900 font-bold">
                {comparisonRows.map((row, idx) => (
                  <tr
                    key={idx}
                    className="hover:bg-neutral-100/50 dark:hover:bg-neutral-900/40 transition-colors"
                  >
                    <td className="py-3.5 px-4 sm:px-6 font-black text-neutral-900 dark:text-neutral-100">
                      {row.feature}
                    </td>
                    <td className="py-3.5 px-4 sm:px-6 text-neutral-500 dark:text-neutral-400">
                      {row.chatbots}
                    </td>
                    <td className="py-3.5 px-4 sm:px-6 text-neutral-500 dark:text-neutral-400">
                      {row.passive}
                    </td>
                    <td className="py-3.5 px-4 sm:px-6 font-black text-red-600 dark:text-red-400 bg-red-500/5 dark:bg-red-500/10">
                      {row.isha}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ================= TEAR SECTION: 8-STAGE END-TO-END PIPELINE CARDS ================= */}
      <div className="relative mt-20 sm:mt-28 -mx-6 sm:-mx-10 md:-mx-16 lg:-mx-20 bg-[#F3EFE4] dark:bg-[#0A0A0B] px-6 sm:px-10 md:px-16 lg:px-20 pt-[150px] sm:pt-[170px] pb-16 sm:pb-20">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 h-[150px] bg-[#F3EFE4] dark:bg-[#0A0A0B]"
          style={{
            WebkitMaskImage: "url('/tear.png')",
            maskImage: "url('/tear.png')",
            WebkitMaskRepeat: "repeat-x",
            maskRepeat: "repeat-x",
            WebkitMaskSize: "auto 150px",
            maskSize: "auto 150px",
            WebkitMaskPosition: "top left",
            maskPosition: "top left",
            filter: "drop-shadow(0 -8px 14px rgba(19, 35, 58, 0.16))",
          }}
        />

        <div className="relative z-10 max-w-7xl mx-auto">
          <div className="flex flex-col items-center text-center">
            <p className="inline-flex items-center gap-2 font-mono text-[10px] sm:text-xs font-black uppercase tracking-[0.28em] text-red-600 dark:text-red-500">
              <svg className="h-3.5 w-3.5 fill-current" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 1l2.2 7.1L21 5l-3.6 6.5L24 14l-7.1 1.3L19 22l-7-3.9L5 22l2.1-6.7L0 14l6.6-2.5L3 5l6.8 3.1z" />
              </svg>
              THE COMPLETE AUTONOMOUS PIPELINE
            </p>
            <h3 className="mt-5 max-w-4xl text-4xl sm:text-5xl md:text-6xl lg:text-[72px] font-black leading-[0.98] tracking-[-0.055em] text-neutral-950 dark:text-[#F9F7EF]">
              The harness,{" "}
              <ScrollHighlight variant="brush" color="sun" delay={0.1}>
                end to end.
              </ScrollHighlight>
            </h3>
            <p className="mt-5 max-w-2xl text-sm sm:text-lg font-bold leading-relaxed text-neutral-600 dark:text-neutral-400">
              The 8-stage empirical loop behind every verified, minimal-churn pull request.
            </p>
          </div>

          <div className="relative mt-12 sm:mt-16">
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-x-10 bottom-4 h-28 rounded-[50%] bg-[#D9C39A]/40 blur-3xl dark:bg-red-950/20"
            />
            <div
              aria-label="ISHA updates and pipeline"
              className="relative flex gap-4 sm:gap-5 overflow-x-auto overscroll-x-contain snap-x snap-mandatory scroll-smooth px-1 pb-5 pt-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
            >
              {harnessCards.map((card) => {
                const tone = tones[card.tone];
                return (
                  <div
                    key={card.meta}
                    className={`${cardClass} ${tone.card} ${tone.glow}`}
                  >
                    <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-black/10" />
                    <span
                      aria-hidden="true"
                      className={`pointer-events-none absolute -bottom-7 -right-2 font-black leading-none tracking-[-0.08em] ${tone.num} ${
                        card.tag.length > 2 ? "text-[80px]" : "text-[110px]"
                      }`}
                    >
                      {card.tag}
                    </span>
                    <div className="relative z-10">
                      <div className="flex items-start justify-between gap-3">
                        <span
                          className={`rounded-full px-2.5 py-1 font-mono text-[10px] font-black uppercase tracking-[0.2em] ${tone.tag}`}
                        >
                          {card.tag}
                        </span>
                        <span className="font-mono text-[9px] font-black uppercase tracking-[0.16em] opacity-75">
                          {card.meta}
                        </span>
                      </div>
                      <h4 className="mt-6 text-[23px] font-black leading-[1.05] tracking-[-0.04em]">
                        {card.title}
                      </h4>
                    </div>
                    <div className="relative z-10">
                      <p className={`text-[12.5px] font-semibold leading-relaxed ${tone.sub}`}>
                        {card.body}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-4 flex items-center justify-center gap-3">
            <span className="font-hand text-2xl text-neutral-500 dark:text-neutral-400">
              scroll through pipeline
            </span>
            <span className="font-mono text-[10px] font-black uppercase tracking-[0.2em] text-neutral-400 dark:text-neutral-600">
              scroll →
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
