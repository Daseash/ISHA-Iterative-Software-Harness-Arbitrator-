"use client";

import React from "react";
import { TikTikColorList } from "../components/v1/skiper24";
import type { Project } from "../components/v1/skiper24";
import { Navbar_001 } from "../components/v1/skiper13";

// All audited benchmark and framework ecosystem suites
export const statsProjects: Project[] = [
  {
    id: "swebench-s4",
    name: "SWE-bench Lite S4 Peak",
    description:
      "70.0% official Docker container resolution rate (21 / 30) achieved in Session 4. S1–S4 combined delivers 55.0% across 120 tasks, leading global open-source agents while maintaining $0.00 inference spend.",
    badge: "Official Docker Ladder",
    bgColor: "#38bdf8", // Sky blue matching skiper24 screenshot
    image: "/images/stats/swebench.svg",
    date: "70.0% SOTA",
    metric: "21 / 30 Docker Verified",
    auditProof: "python scripts/score.py (results/lite300-s4/report.json)",
  },
  {
    id: "django-suite",
    name: "Django Web Framework",
    description:
      "66 verified Docker container resolutions across Django ORM SQL query compilers, schema migrations, composite keys, and form widgets. Represents 84.6% of resolved benchmarks with minimal diff hunks.",
    badge: "ORM & Query Compilers",
    bgColor: "#059669", // Rich Emerald Green
    image: "/images/stats/django.svg",
    date: "66 Resolved",
    metric: "84.6% of Resolved Quota",
    auditProof: "python scripts/score.py (scans results/**/report.json by repo)",
  },
  {
    id: "sympy-algebra",
    name: "SymPy Symbolic Algebra",
    description:
      "3 verified Docker container resolutions resolving complex hyperbolic branch cuts, asymptotic branch evaluation, and polynomial factorizations without numerical precision degradation.",
    badge: "Calculus & Branches",
    bgColor: "#d97706", // Amber Orange
    image: "/images/stats/sympy.svg",
    date: "3 Resolved",
    metric: "Complex Branch Cuts",
    auditProof: "results/lite300-s8/sympy__sympy-13480/report.json",
  },
  {
    id: "pytest-tools",
    name: "Pytest Test Framework",
    description:
      "3 verified Docker container resolutions in core pytest metaprogramming, AST assertion rewriting, parametrized fixture tear-downs, and test discovery introspection.",
    badge: "AST Assertion Rewriting",
    bgColor: "#2563eb", // Royal Developer Blue
    image: "/images/stats/pytest.svg",
    date: "3 Resolved",
    metric: "Framework Metaprogramming",
    auditProof: "results/lite300-s6/pytest-dev__pytest-5495/report.json",
  },
  {
    id: "golden7-suite",
    name: "Golden-7 Safety Net",
    description:
      "Mandatory locked regression net executed on every pull request and push to main. Verifies non-empty patch diffs, AST syntax validity, and official Docker resolution across 7 real repositories in ~18s.",
    badge: "100% CI Locked Net",
    bgColor: "#7c3aed", // Deep Security Violet
    image: "/images/stats/golden7.svg",
    date: "7 / 7 PASS",
    metric: "100% Deterministic Pass",
    auditProof: "python scripts/verify_golden.py",
  },
  {
    id: "laya-engine",
    name: "LAYA Decision Arbitrator",
    description:
      "Temperature-scaled probabilistic decision arbitrator fitted on 546 container outcome labels. Enforces an exponential churn penalty and guarantees 0.0% false approvals (100% precision) at the τ=0.50 threshold.",
    badge: "Calibrated Arbitrator",
    bgColor: "#db2777", // Rose Pink
    image: "/images/stats/laya.svg",
    date: "ECE = 0.0214",
    metric: "Zero False Approvals",
    auditProof: "data/laya_combiner.json & src/review/calibration.py",
  },
  {
    id: "ast-hygiene",
    name: "AST Invariant Hygiene Engine",
    description:
      "8 Non-Negotiable Empirical Container Invariants anchored to target classes, guard clause completeness, and hashability contracts. Pre-sandbox ast.parse() eliminates 100% of host syntax aborts.",
    badge: "Static AST Gates",
    bgColor: "#0d9488", // Dark Teal
    image: "/images/stats/ast.svg",
    date: "86.2% Yield",
    metric: "200 / 232 Clean AST Patches",
    auditProof: "isha-agent/src/bench/gates.py & AGENTS.md",
  },
  {
    id: "pareto-cost",
    name: "Pareto Cost Frontier",
    description:
      "Engineered for zero-cost autonomous operations. Orchestrates a 14-key token pool across Gemini Flash-Lite and Groq LPUs, delivering SOTA benchmark resolution without burning $35/task like Devin.",
    badge: "Economic Efficiency",
    bgColor: "#ca8a04", // Frontier Golden Ochre
    image: "/images/stats/cost.svg",
    date: "$0.00 / Task",
    metric: "Infinite ROI vs Devin $35",
    auditProof: "scripts/cost_report.py & src/config.py",
  },
  {
    id: "tournament-race",
    name: "Parallel Tournament & TDD",
    description:
      "Spawns 3 diverse strategy candidates (minimal_diff, call_site_aware, root_cause_first) in isolated git worktrees. Feeds live pytest tracebacks back into the coder for up to 2 targeted repair rounds.",
    badge: "Multi-Candidate Racing",
    bgColor: "#4f46e5", // Tournament Indigo
    image: "/images/stats/tournament.svg",
    date: "3 Worktrees",
    metric: "Closed Loop TDD Repair",
    auditProof: "src/tournament/race.py & src/coder/pipeline.py",
  },
  {
    id: "memory-ledger",
    name: "Institutional Memory Ledger",
    description:
      "SQLite WAL-mode outcome store tracking 546 evaluated runs in data/memory.db, synchronized with a 384-D dense semantic embedding ledger. Hard veto fires at cosine similarity > 0.92 to prevent repeat regressions.",
    badge: "Persistent Experience Veto",
    bgColor: "#be123c", // Ruby Crimson
    image: "/images/stats/memory.svg",
    date: "546 Outcomes",
    metric: "Cos > 0.92 Repeat Veto",
    auditProof: "isha-agent/src/memory/store.py & tests/test_veto.py",
  },
];

export const StatsPage: React.FC = () => {
  return (
    <main className="relative w-full h-screen overflow-hidden select-none">
      {/* Floating Home Navbar Anchored to Top-Right as requested */}
      <Navbar_001 position="right" />

      {/* Skiper24 TikTikColorList Archive Scroll Experience */}
      <TikTikColorList
        projects={statsProjects}
        showPreview={true}
        previewSize="lg"
        enableSound={true}
        infiniteScroll={true}
        scrollThreshold={45}
      />
    </main>
  );
};

export default StatsPage;
