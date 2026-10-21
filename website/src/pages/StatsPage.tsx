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
    description: "21 / 30 official Docker resolutions leading global open-source.",
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
    description: "66 verified Docker resolutions across Django ORM & migrations.",
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
    description: "3 complex hyperbolic branch cuts and factorizations verified.",
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
    description: "3 AST assertion rewriting and fixture introspection verified.",
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
    description: "Mandatory locked 7-repo regression net passing in ~18s.",
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
    description: "Probabilistic calibrated arbitrator with 0% false approvals.",
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
    description: "8 empirical container invariants eliminating host syntax aborts.",
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
    description: "Zero-cost 14-key token pool with infinite ROI vs Devin $35.",
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
    description: "3 strategy worktrees with closed-loop pytest repair rounds.",
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
    description: "SQLite WAL store with dense semantic cosine similarity veto.",
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
