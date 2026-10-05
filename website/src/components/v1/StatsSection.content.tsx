import React, { useState } from "react";
import {
  TrendingUp,
  Zap,
  ShieldCheck,
  BarChart3,
  GitBranch,
  Layers,
  Cpu,
  CheckCircle2,
  Sparkles,
  Terminal,
  Copy,
  Check,
  FileCode,
  Flame,
  ArrowRight,
} from "lucide-react";
import { HoverExpand_001 } from "./skiper52";

export const StatsSection: React.FC = () => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [activeStage, setActiveStage] = useState<number>(0);

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // 6 Real audited metrics from isha-agent/results/REPORT.md & README.md
  const statsMetrics = [
    {
      value: "66.7%",
      delta: "+26.7% ABSOLUTE",
      label: "SWE-BENCH GENERATION YIELD",
      detail: "20/30 patches produced (up from 40.0% baseline)",
      icon: TrendingUp,
    },
    {
      value: "0.0%",
      delta: "-26.7% ELIMINATED",
      label: "HOST PATCH APPLY FAILURES",
      detail: "0/30 failures across worktrees (down from 26.7%)",
      icon: ShieldCheck,
    },
    {
      value: "0.0010",
      delta: "-98.9% ERROR DROP",
      label: "LAYA CALIBRATION ERROR (ECE)",
      detail: "Temperature-scaled T=0.35 over 315 real labels",
      icon: Sparkles,
    },
    {
      value: "100%",
      delta: "ZERO FALSE POSITIVES",
      label: "AUTO-APPROVE PRECISION",
      detail: "At threshold τ=0.50 with 32.0% coverage",
      icon: CheckCircle2,
    },
    {
      value: "$0.00",
      delta: "100% FREE TIER",
      label: "AVERAGE INFERENCE COST",
      detail: "Groq LPU + Gemini 3.8 Flash zero-cost cascade",
      icon: Cpu,
    },
    {
      value: "81/81",
      delta: "100% PASSING",
      label: "VERIFIED GREEN TEST SUITE",
      detail: "All unit, AST, and arbitration tests passing in ~18s",
      icon: Zap,
    },
  ];

  // 1. Benchmark Evaluation (7 Slices of isha_vs_baselines.png)
  const benchmarkGallery = [
    {
      src: "/isha_vs_baselines.png",
      alt: "Panel A: SWE-bench Lite Yield (+26.7% Gain)",
      code: "# 01",
    },
    {
      src: "/isha_vs_baselines.png",
      alt: "Panel B: $0.00 Inference Cost Frontier",
      code: "# 02",
    },
    {
      src: "/isha_vs_baselines.png",
      alt: "Panel C: LAYA ECE Probability Calibration",
      code: "# 03",
    },
    {
      src: "/isha_vs_baselines.png",
      alt: "Panel D: Component Ablation Lifts",
      code: "# 04",
    },
    {
      src: "/isha_vs_baselines.png",
      alt: "Host Diff Apply Failures: 0.0% Eliminated",
      code: "# 05",
    },
    {
      src: "/isha_vs_baselines.png",
      alt: "Verified 25/25 Release Criteria Matrix",
      code: "# 06",
    },
    {
      src: "/isha_vs_baselines.png",
      alt: "Reconciled Mutually Exclusive Stage Table",
      code: "# 07",
    },
  ];

  // 2. Multi-Agent Arbitration Tournament (7 Slices of demo-desktop.png)
  const arbitrationGallery = [
    {
      src: "/demo-desktop.png",
      alt: "Candidate 1: Direct Surgical AST Fix",
      code: "# 01",
    },
    {
      src: "/demo-desktop.png",
      alt: "Candidate 2: Defensive Boundary Checks",
      code: "# 02",
    },
    {
      src: "/demo-desktop.png",
      alt: "Candidate 3: Alternative Caller Fix",
      code: "# 03",
    },
    {
      src: "/demo-desktop.png",
      alt: "3 Isolated Git Worktree Sandboxes",
      code: "# 04",
    },
    {
      src: "/demo-desktop.png",
      alt: "Minimal Churn State Arbitrator",
      code: "# 05",
    },
    {
      src: "/demo-desktop.png",
      alt: "LAYA Calibrated Approval Gate (T=0.35)",
      code: "# 06",
    },
    {
      src: "/demo-desktop.png",
      alt: "Verified Senior-Dev 8-Section PR Output",
      code: "# 07",
    },
  ];

  // 6-Stage Autonomous Architecture Pipeline from README.md & user_prompt_spec.md
  const architectureStages = [
    {
      id: "stage-1",
      number: "01",
      title: "Ingestion & AST Map",
      badge: "BM25 + Tree-Sitter",
      desc: "Localizes candidate files using hybrid lexical retrieval and ranks target functions via symbol_target AST parsing instead of whole-repo hallucination.",
      metric: "Hit@8 Recall: 66.7% (MRR 0.535)",
      icon: Layers,
    },
    {
      id: "stage-2",
      number: "02",
      title: "TDD Test Synthesis",
      badge: "Red-to-Green Verification",
      desc: "Synthesizes an isolated reproduction test that MUST fail on existing unfixed code before any repair begins. If the test cannot fail, it is rejected.",
      metric: "Guaranteed Red State Reproduction",
      icon: Flame,
    },
    {
      id: "stage-3",
      number: "03",
      title: "Parallel Tournament",
      badge: "3 Git Worktrees",
      desc: "Spawns 3 parallel candidate agents across isolated .worktrees/. Candidate 1 pursues direct surgical fix, Candidate 2 defensive boundary checks, Candidate 3 alternative caller fixes.",
      metric: "Zero Working Tree Branch Pollution",
      icon: GitBranch,
    },
    {
      id: "stage-4",
      number: "04",
      title: "Minimal Churn Arbitrator",
      badge: "AST + Assertion Gate",
      desc: "Runs reproduction tests inside sandboxes. Compares candidate AST diffs, selects the minimal syntax-validated patch that turns tests green with zero regressions.",
      metric: "0.0% Static Syntax / AST Errors",
      icon: ShieldCheck,
    },
    {
      id: "stage-5",
      number: "05",
      title: "LAYA Calibrated Gate",
      badge: "ECE = 0.0010 (T=0.35)",
      desc: "Temperature-scaled logistic combiner over 315 real developer labels. Evaluates repro status, blast radius, and AST safety to decide Auto-Approve vs Senior Human Review.",
      metric: "100.0% Auto-Approve Precision",
      icon: Sparkles,
    },
    {
      id: "stage-6",
      number: "06",
      title: "Security & Atomic Apply",
      badge: "CRLF Safe + Secret Scan",
      desc: "Enforces secret-leak scanning, cross-platform LF line ending normalization, and atomic git patch application with automatic fuzz-context recovery.",
      metric: "0/30 Host Diff Apply Failures",
      icon: FileCode,
    },
  ];

  // Audited comparison records from results/before_after.json
  const benchmarkRows = [
    {
      metric: "Patch Apply Failures",
      baseline: "8/30 (26.7%)",
      isha: "0/30 (0.0%)",
      change: "-26.7%",
      status: "100% Eliminated",
    },
    {
      metric: "Patch Generation Yield",
      baseline: "12/30 (40.0%)",
      isha: "20/30 (66.7%)",
      change: "+26.7%",
      status: "Statistically Significant",
    },
    {
      metric: "Static Syntax/AST Errors",
      baseline: "1/30 (3.3%)",
      isha: "0/30 (0.0%)",
      change: "-3.3%",
      status: "100% Clean AST",
    },
    {
      metric: "Harness Container Aborts",
      baseline: "2/30 (6.7%)",
      isha: "0/30 (0.0%)",
      change: "-6.7%",
      status: "Fixed via LF-Writes",
    },
    {
      metric: "Host Environment Health",
      baseline: "28/30 (93.3%)",
      isha: "30/30 (100.0%)",
      change: "+6.7%",
      status: "Worktree Isolation",
    },
    {
      metric: "Localizer File Recall (Hit@8)",
      baseline: "13/30 (43.3%)",
      isha: "20/30 (66.7%)",
      change: "+23.4%",
      status: "+54% Relative Gain",
    },
  ];

  // Quick CLI Commands from project quickstart
  const cliCommands = [
    {
      title: "Zero-Clone Install",
      cmd: "pip install git+https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-.git",
    },
    {
      title: "Run Autonomous Fix",
      cmd: "isha solve --repo ./target-repo --issue ./problem_statement.md",
    },
    {
      title: "Run System Doctor",
      cmd: "isha doctor --check-all",
    },
    {
      title: "Run Full Test Suite",
      cmd: "pytest tests/ -v  # 81 passed in ~18s (100% green)",
    },
  ];

  return (
    <section
      id="stats"
      className="relative py-24 px-4 sm:px-8 md:px-12 bg-[#F9F7EF] dark:bg-black transition-colors font-black"
    >
      <div className="max-w-6xl mx-auto space-y-20">
        {/* Header */}
        <div className="text-center space-y-3">
          <span className="text-xs sm:text-sm font-mono uppercase tracking-widest text-red-600 dark:text-red-500">
            Empirical Evaluation & System Architecture
          </span>
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tight text-black dark:text-[#F9F7EF]">
            STATS
          </h2>
          <p className="max-w-2xl mx-auto text-sm sm:text-base text-neutral-600 dark:text-neutral-400 font-bold">
            Audited results from SWE-bench Lite benchmarks ($N=30$), LAYA calibration curves, and 3-worktree isolated execution.
          </p>
        </div>

        {/* 6 High-Impact Stat Metrics with 3D Shadows */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
          {statsMetrics.map((stat, i) => {
            const Icon = stat.icon;
            return (
              <div
                key={i}
                className="flex flex-col justify-between p-6 sm:p-8 rounded-3xl bg-[#F9F7EF] dark:bg-black border border-neutral-300 dark:border-neutral-800 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 space-y-4 transition-transform hover:-translate-y-1 duration-300"
              >
                <div className="flex items-center justify-between">
                  <div className="p-3 rounded-2xl bg-neutral-200/80 dark:bg-neutral-900 text-red-600 shadow-sm">
                    <Icon className="w-6 h-6 stroke-[3]" />
                  </div>
                  <span className="text-xs font-mono font-bold tracking-wider text-red-600 dark:text-red-500 px-2.5 py-1 rounded-full bg-red-600/10 dark:bg-red-500/15">
                    {stat.delta}
                  </span>
                </div>

                <div className="space-y-1">
                  <span className="text-4xl sm:text-5xl font-black text-red-600 tracking-tight block">
                    {stat.value}
                  </span>
                  <span className="text-sm sm:text-base font-black uppercase tracking-wide text-black dark:text-[#F9F7EF] block">
                    {stat.label}
                  </span>
                  <p className="text-xs text-neutral-600 dark:text-neutral-400 font-bold pt-1">
                    {stat.detail}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* EXACTLY 2 VISUAL SHOWCASE CARDS (LIKE THE FIRST VERSION) WITH 7-PANEL SLICED MOSAIC */}
        <div className="space-y-6">
          <div className="flex items-center justify-between pb-2 border-b border-neutral-300 dark:border-neutral-800">
            <span className="text-sm sm:text-base font-mono uppercase tracking-wider text-red-600 dark:text-red-500">
              Interactive Visual Deep-Dive
            </span>
            <span className="text-xs font-mono text-neutral-500 uppercase tracking-widest hidden sm:inline">
              Hover over cards to expand details
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Card 1: Benchmark Comparison Frame */}
            <div className="rounded-3xl bg-[#F9F7EF] dark:bg-black border border-neutral-300 dark:border-neutral-800 p-6 sm:p-8 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-neutral-300 dark:border-neutral-800">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-red-600 stroke-[3]" />
                  <span className="text-base sm:text-lg font-black uppercase tracking-tight text-black dark:text-[#F9F7EF]">
                    BENCHMARK EVALUATION
                  </span>
                </div>
                <span className="text-xs font-mono text-red-600 dark:text-red-500 font-bold">
                  SWE-BENCH LITE (N=30)
                </span>
              </div>

              <div className="h-72 sm:h-80 w-full rounded-2xl overflow-hidden shadow-inner bg-neutral-200/50 dark:bg-neutral-900/60 flex items-center justify-center relative p-2">
                <HoverExpand_001
                  images={benchmarkGallery}
                  height="17rem"
                  expandedWidth="clamp(12rem, 26vw, 18rem)"
                  collapsedWidth="clamp(1.5rem, 3.2vw, 2.6rem)"
                  defaultWidth="clamp(2.4rem, 5vw, 3.8rem)"
                />
              </div>

              <p className="text-xs font-mono text-neutral-600 dark:text-neutral-400">
                7-panel empirical lift breakdown: patch yield (+26.7%), zero cost frontier ($0.00), and LAYA ECE calibration curve.
              </p>
            </div>

            {/* Card 2: Autonomous Multi-Agent Execution Frame */}
            <div className="rounded-3xl bg-[#F9F7EF] dark:bg-black border border-neutral-300 dark:border-neutral-800 p-6 sm:p-8 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-neutral-300 dark:border-neutral-800">
                <div className="flex items-center gap-2">
                  <GitBranch className="w-5 h-5 text-red-600 stroke-[3]" />
                  <span className="text-base sm:text-lg font-black uppercase tracking-tight text-black dark:text-[#F9F7EF]">
                    MULTI-AGENT ARBITRATION
                  </span>
                </div>
                <span className="text-xs font-mono text-red-600 dark:text-red-500 font-bold">
                  3-WORKTREE TOURNAMENT
                </span>
              </div>

              <div className="h-72 sm:h-80 w-full rounded-2xl overflow-hidden shadow-inner bg-neutral-200/50 dark:bg-neutral-900/60 flex items-center justify-center relative p-2">
                <HoverExpand_001
                  images={arbitrationGallery}
                  height="17rem"
                  expandedWidth="clamp(12rem, 26vw, 18rem)"
                  collapsedWidth="clamp(1.5rem, 3.2vw, 2.6rem)"
                  defaultWidth="clamp(2.4rem, 5vw, 3.8rem)"
                />
              </div>

              <p className="text-xs font-mono text-neutral-600 dark:text-neutral-400">
                Parallel tournament racing direct, defensive, and alternative candidate fixes across isolated worktrees.
              </p>
            </div>
          </div>
        </div>

        {/* 6-STAGE AUTONOMOUS PIPELINE (PROJECT ARCHITECTURE DEEP-DIVE) */}
        <div className="rounded-3xl bg-[#F9F7EF] dark:bg-black border border-neutral-300 dark:border-neutral-800 p-6 sm:p-10 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 space-y-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-neutral-300 dark:border-neutral-800">
            <div>
              <span className="text-xs font-mono uppercase tracking-widest text-red-600 dark:text-red-500">
                TDD Red-to-Green Execution Engine
              </span>
              <h3 className="text-2xl sm:text-3xl font-black uppercase tracking-tight text-black dark:text-[#F9F7EF] mt-1">
                Autonomous SWE Architecture
              </h3>
            </div>
            <span className="px-3 py-1 rounded-full bg-red-600/10 dark:bg-red-500/15 text-red-600 dark:text-red-500 font-mono text-xs font-bold self-start sm:self-auto">
              6 STAGES · ZERO HOST POLLUTION
            </span>
          </div>

          {/* Stage selection badges */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {architectureStages.map((stage, idx) => {
              const Icon = stage.icon;
              const isSelected = activeStage === idx;
              return (
                <button
                  key={stage.id}
                  onClick={() => setActiveStage(idx)}
                  className={`flex flex-col items-start p-3 sm:p-4 rounded-2xl border text-left transition-all ${
                    isSelected
                      ? "bg-red-600 text-white border-red-600 shadow-lg shadow-red-600/20"
                      : "bg-neutral-200/50 dark:bg-neutral-900/50 text-neutral-700 dark:text-neutral-300 border-neutral-300 dark:border-neutral-800 hover:border-neutral-400 dark:hover:border-neutral-700"
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-2">
                    <span className="text-[10px] font-mono font-bold">{stage.number}</span>
                    <Icon className="w-4 h-4 stroke-[2.5]" />
                  </div>
                  <span className="text-xs font-black line-clamp-1 uppercase">
                    {stage.title}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Active Stage Detail Showcase */}
          <div className="p-6 sm:p-8 rounded-2xl bg-neutral-200/40 dark:bg-neutral-900/40 border border-neutral-300 dark:border-neutral-800 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono font-black text-red-600 dark:text-red-500 bg-red-600/10 dark:bg-red-500/15 px-2.5 py-1 rounded-full">
                  STAGE {architectureStages[activeStage].number}
                </span>
                <h4 className="text-lg sm:text-xl font-black text-black dark:text-[#F9F7EF] uppercase">
                  {architectureStages[activeStage].title}
                </h4>
              </div>
              <span className="text-xs font-mono font-bold text-neutral-600 dark:text-neutral-400">
                {architectureStages[activeStage].badge}
              </span>
            </div>

            <p className="text-sm sm:text-base text-neutral-700 dark:text-neutral-300 font-medium leading-relaxed">
              {architectureStages[activeStage].desc}
            </p>

            <div className="flex items-center gap-2 pt-2 border-t border-neutral-300 dark:border-neutral-800 text-xs font-mono font-bold text-red-600 dark:text-red-500">
              <ArrowRight className="w-4 h-4" />
              <span>Audited Result: {architectureStages[activeStage].metric}</span>
            </div>
          </div>
        </div>

        {/* Audited Before-vs-After Comparison Table */}
        <div className="rounded-3xl bg-[#F9F7EF] dark:bg-black border border-neutral-300 dark:border-neutral-800 p-6 sm:p-10 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-neutral-300 dark:border-neutral-800">
            <div>
              <h3 className="text-xl sm:text-2xl font-black uppercase tracking-tight text-black dark:text-[#F9F7EF]">
                SWE-bench Lite Audited Results (N = 30)
              </h3>
              <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 font-bold mt-1">
                Source: results/before_after.json · Fixed random seed 42 · Reconciled stage breakdown
              </p>
            </div>
            <span className="px-3 py-1 rounded-full bg-red-600/10 dark:bg-red-500/15 text-red-600 dark:text-red-500 font-mono text-xs font-bold self-start sm:self-auto">
              25/25 VERIFIED
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-neutral-300 dark:border-neutral-800 text-neutral-500 uppercase tracking-wider">
                  <th className="py-3 px-2 sm:px-4 font-bold">Metric Dimension</th>
                  <th className="py-3 px-2 sm:px-4 font-bold">Baseline</th>
                  <th className="py-3 px-2 sm:px-4 font-bold text-red-600 dark:text-red-500">Upgraded ISHA</th>
                  <th className="py-3 px-2 sm:px-4 font-bold">Measured Δ</th>
                  <th className="py-3 px-2 sm:px-4 font-bold text-right">Verification Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 dark:divide-neutral-900 font-bold">
                {benchmarkRows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-neutral-200/40 dark:hover:bg-neutral-900/40 transition-colors">
                    <td className="py-3.5 px-2 sm:px-4 text-black dark:text-[#F9F7EF] font-black font-sans">
                      {row.metric}
                    </td>
                    <td className="py-3.5 px-2 sm:px-4 text-neutral-500 line-through">
                      {row.baseline}
                    </td>
                    <td className="py-3.5 px-2 sm:px-4 text-red-600 dark:text-red-500 font-black">
                      {row.isha}
                    </td>
                    <td className="py-3.5 px-2 sm:px-4 text-black dark:text-[#F9F7EF]">
                      {row.change}
                    </td>
                    <td className="py-3.5 px-2 sm:px-4 text-right">
                      <span className="inline-flex items-center gap-1.5 text-xs text-neutral-800 dark:text-neutral-200 font-black">
                        <CheckCircle2 className="w-3.5 h-3.5 text-red-600 inline" />
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* QUICK CLI / DEVELOPER QUICKSTART TERMINAL */}
        <div className="rounded-3xl bg-[#F9F7EF] dark:bg-black border border-neutral-300 dark:border-neutral-800 p-6 sm:p-10 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-neutral-300 dark:border-neutral-800">
            <div className="flex items-center gap-2.5">
              <Terminal className="w-6 h-6 text-red-600 stroke-[2.5]" />
              <h3 className="text-xl sm:text-2xl font-black uppercase tracking-tight text-black dark:text-[#F9F7EF]">
                Developer Quickstart & CLI
              </h3>
            </div>
            <span className="text-xs font-mono text-neutral-500 font-bold">
              PYTHON 3.10+ · LINUX / MACOS / WINDOWS
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {cliCommands.map((item, idx) => (
              <div
                key={idx}
                className="p-4 sm:p-5 rounded-2xl bg-neutral-200/50 dark:bg-neutral-900/60 border border-neutral-300 dark:border-neutral-800 flex flex-col justify-between space-y-3 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono uppercase tracking-wider text-black dark:text-[#F9F7EF] font-black">
                    {item.title}
                  </span>
                  <button
                    onClick={() => copyToClipboard(item.cmd, idx)}
                    className="p-1.5 rounded-lg bg-neutral-300/60 dark:bg-neutral-800 hover:bg-neutral-300 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 transition-colors"
                    title="Copy command"
                  >
                    {copiedIndex === idx ? (
                      <Check className="w-3.5 h-3.5 text-green-500" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
                <div className="font-mono text-xs text-red-600 dark:text-red-400 bg-neutral-100 dark:bg-black p-3 rounded-xl overflow-x-auto border border-neutral-300/50 dark:border-neutral-800/80">
                  <code>{item.cmd}</code>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default StatsSection;
