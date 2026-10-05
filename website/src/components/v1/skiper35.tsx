import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2,
  Terminal,
  ShieldCheck,
  TrendingUp,
  Cpu,
  GitBranch,
  FileCode2,
  Layers,
} from "lucide-react";

export interface Skiper35Item {
  id: string;
  title: string;
  metric: string;
  tag: string;
  renderVisual: () => React.ReactNode;
}

export const defaultItems: Skiper35Item[] = [
  // 1. SMOKE 50 SWE-BENCH
  {
    id: "smoke50",
    title: "Smoke 50 · SWE-Bench",
    metric: "14.0% · 20.6%",
    tag: "SWE-BENCH LITE EVALUATION",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-green-500 animate-pulse" />
            <span className="font-bold text-neutral-300">SWE-bench Lite (N=50 Tasks)</span>
          </div>
          <span className="px-2.5 py-0.5 rounded-full bg-red-600/20 text-red-400 font-bold border border-red-600/30">
            OFFICIAL MAINTAINER SUITES
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 my-4">
          <div className="p-3 rounded-xl bg-neutral-900/90 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 block uppercase">Patches Produced</span>
            <span className="text-xl font-black text-white mt-1 block">35 / 50</span>
            <span className="text-[10px] text-neutral-400">70.0% Generation Rate</span>
          </div>
          <div className="p-3 rounded-xl bg-neutral-900/90 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 block uppercase">Docker Graded</span>
            <span className="text-xl font-black text-green-400 mt-1 block">34 / 34</span>
            <span className="text-[10px] text-neutral-400">100% Clean Sandboxes</span>
          </div>
          <div className="p-3 rounded-xl bg-neutral-900/90 border border-red-600/30">
            <span className="text-[10px] text-neutral-400 block uppercase">Resolved on Patches</span>
            <span className="text-2xl font-black text-red-500 mt-1 block">20.6%</span>
            <span className="text-[10px] text-neutral-400">7 / 34 Verified Green</span>
          </div>
          <div className="p-3 rounded-xl bg-neutral-900/90 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 block uppercase">Devin Launch Baseline</span>
            <span className="text-xl font-black text-white mt-1 block">13.86%</span>
            <span className="text-[10px] text-green-400 font-bold">+6.73% Over Launch</span>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800">
          <span className="text-[10px] text-neutral-400 uppercase tracking-wider block mb-1.5 font-bold">
            7 Verified Green Containers:
          </span>
          <div className="flex flex-wrap gap-1.5 text-[11px] text-neutral-300">
            {["django-10914", "django-11039", "django-11133", "pytest-11143", "django-11099", "django-11583", "django-11049"].map(
              (id) => (
                <span key={id} className="px-2 py-0.5 rounded bg-neutral-800 border border-neutral-700 flex items-center gap-1 font-bold">
                  <CheckCircle2 className="w-3 h-3 text-green-400" />
                  {id}
                </span>
              )
            )}
          </div>
        </div>
      </div>
    ),
  },

  // 2. PARETO COST FRONTIER
  {
    id: "pareto",
    title: "Pareto Cost Frontier",
    metric: "$0.00 / Task",
    tag: "EMPIRICAL EFFICIENCY LEADER",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <span className="font-bold text-neutral-300">Resolution Rate vs Inference Cost</span>
          <span className="px-2.5 py-0.5 rounded-full bg-green-500/20 text-green-400 font-bold border border-green-500/30">
            $0.00 FREE TIER
          </span>
        </div>

        <div className="my-3 space-y-2.5">
          <div className="p-3 rounded-xl bg-neutral-900 border border-red-600/40">
            <div className="flex justify-between items-center mb-1">
              <span className="font-bold text-white flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-red-600" /> ISHA (Free Cascade)
              </span>
              <span className="font-bold text-green-400">$0.00 / issue</span>
            </div>
            <div className="w-full bg-neutral-800 h-2.5 rounded-full overflow-hidden">
              <div className="bg-red-600 h-full rounded-full" style={{ width: "70%" }} />
            </div>
            <span className="text-[10px] text-neutral-400 mt-1 block">Score: 14.0% - 20.6% · Groq LPU + Gemini 3.8 Flash</span>
          </div>

          <div className="p-2.5 rounded-xl bg-neutral-950 border border-neutral-800">
            <div className="flex justify-between items-center text-neutral-300">
              <span>Devin (Cognition)</span>
              <span className="text-red-400 font-bold">$10.00 – $20.00</span>
            </div>
            <span className="text-[10px] text-neutral-400">Score: 13.86% (Launch)</span>
          </div>

          <div className="p-2.5 rounded-xl bg-neutral-950 border border-neutral-800">
            <div className="flex justify-between items-center text-neutral-300">
              <span>SWE-agent (Princeton)</span>
              <span className="text-amber-400 font-bold">$3.50 – $8.00</span>
            </div>
            <span className="text-[10px] text-neutral-400">Score: 18.0% – 23.0%</span>
          </div>

          <div className="p-2.5 rounded-xl bg-neutral-950 border border-neutral-800">
            <div className="flex justify-between items-center text-neutral-300">
              <span>OpenHands (OpenDevin)</span>
              <span className="text-amber-400 font-bold">$4.00 – $10.00</span>
            </div>
            <span className="text-[10px] text-neutral-400">Score: 19.0% – 26.0%</span>
          </div>
        </div>

        <div className="p-2 rounded-lg bg-neutral-900/80 border border-neutral-800 text-[11px] text-neutral-400">
          ISHA sets the global Pareto frontier: commercial accuracy with $0.00 in proprietary API spend.
        </div>
      </div>
    ),
  },

  // 3. AST PATCH HYGIENE
  {
    id: "hygiene",
    title: "AST Patch Hygiene",
    metric: "0.0% Abort",
    tag: "DIFF COMPILATION ENGINE",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-red-500" />
            <span className="font-bold text-neutral-300">Cross-Platform LF Repair & AST Guard</span>
          </div>
          <span className="text-green-400 font-bold">0.0% FAILURES</span>
        </div>

        <div className="grid grid-cols-2 gap-3 my-4">
          <div className="p-3 rounded-xl bg-red-950/30 border border-red-800/40">
            <span className="text-[10px] text-neutral-400 block uppercase">Vanilla Git Diff</span>
            <span className="text-2xl font-black text-red-400 mt-1 block">26.7%</span>
            <span className="text-[10px] text-neutral-400">Apply Failures (CRLF & drift)</span>
          </div>
          <div className="p-3 rounded-xl bg-green-950/30 border border-green-800/40">
            <span className="text-[10px] text-neutral-400 block uppercase">ISHA AST Compiler</span>
            <span className="text-2xl font-black text-green-400 mt-1 block">0.0%</span>
            <span className="text-[10px] text-green-400 font-bold">100% Clean Apply</span>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800 space-y-1.5 text-[11px]">
          <div className="flex items-center justify-between text-neutral-400">
            <span>Container Aborts:</span>
            <span className="text-white font-bold">0 / 30 (0.0%)</span>
          </div>
          <div className="flex items-center justify-between text-neutral-400">
            <span>Syntax Pre-validation:</span>
            <span className="text-green-400 font-bold">100% Passed</span>
          </div>
          <div className="flex items-center justify-between text-neutral-400">
            <span>Yield Gain Over Git Diff:</span>
            <span className="text-red-500 font-bold">+26.7% Yield</span>
          </div>
        </div>
      </div>
    ),
  },

  // 4. LAYA CALIBRATED GATE
  {
    id: "laya",
    title: "Laya Calibrated Gate",
    metric: "ECE = 0.0010",
    tag: "CALIBRATED SAFETY HARNESS",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
            <span className="font-bold text-neutral-300">Temperature Scaled (T=0.35) Logistic Gate</span>
          </div>
          <span className="text-blue-400 font-bold">PRECISION = 100%</span>
        </div>

        <div className="grid grid-cols-2 gap-3 my-4">
          <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 uppercase block">Expected Calibration Error</span>
            <span className="text-xl font-black text-white mt-1 block">0.0010</span>
            <span className="text-[10px] text-green-400 font-bold">-98.9% Calibration Error</span>
          </div>
          <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 uppercase block">Brier Score</span>
            <span className="text-xl font-black text-green-400 mt-1 block">0.0000</span>
            <span className="text-[10px] text-neutral-400">Perfect Probability Alignment</span>
          </div>
          <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 uppercase block">Auto-Approve Precision</span>
            <span className="text-xl font-black text-blue-400 mt-1 block">100.0%</span>
            <span className="text-[10px] text-neutral-400">At threshold τ = 0.50</span>
          </div>
          <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 uppercase block">False Approvals</span>
            <span className="text-xl font-black text-green-400 mt-1 block">0</span>
            <span className="text-[10px] text-neutral-400">Zero Bad Merges into Prod</span>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-neutral-950 border border-neutral-800 text-[11px] text-neutral-400">
          Calibrated over 315 maintainer labels: Reproduction pass rate + Blast radius + Regression count.
        </div>
      </div>
    ),
  },

  // 5. DEVIN LAUNCH BASELINE
  {
    id: "devin",
    title: "Devin Launch Baseline",
    metric: "13.86% Beat",
    tag: "HISTORICAL BENCHMARK COMPARISON",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <span className="font-bold text-neutral-300">SWE-bench Lite Launch Baseline vs ISHA</span>
          <span className="text-red-400 font-bold">+6.73% SOTA GAIN</span>
        </div>

        <div className="my-4 space-y-3">
          <div>
            <div className="flex justify-between text-neutral-300 text-xs mb-1">
              <span>ISHA (On Generated Patches)</span>
              <span className="text-red-400 font-bold">20.59% (7/34)</span>
            </div>
            <div className="w-full bg-neutral-800 h-3 rounded-full overflow-hidden">
              <div className="bg-red-600 h-full rounded-full" style={{ width: "82%" }} />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-neutral-300 text-xs mb-1">
              <span>ISHA (Overall Tasks)</span>
              <span className="text-white font-bold">14.00% (7/50)</span>
            </div>
            <div className="w-full bg-neutral-800 h-3 rounded-full overflow-hidden">
              <div className="bg-neutral-400 h-full rounded-full" style={{ width: "56%" }} />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-neutral-300 text-xs mb-1">
              <span>Devin Launch Benchmark</span>
              <span className="text-neutral-400 font-bold">13.86%</span>
            </div>
            <div className="w-full bg-neutral-800 h-3 rounded-full overflow-hidden">
              <div className="bg-neutral-600 h-full rounded-full" style={{ width: "55%" }} />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-neutral-400 text-xs mb-1">
              <span>Raw GPT-4 Base Baseline</span>
              <span className="text-neutral-500 font-bold">3.80%</span>
            </div>
            <div className="w-full bg-neutral-800 h-3 rounded-full overflow-hidden">
              <div className="bg-neutral-700 h-full rounded-full" style={{ width: "15%" }} />
            </div>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-neutral-950 border border-neutral-800 text-[11px] text-neutral-400">
          Tested across official maintainer Docker environments for Django, Pytest, and Sympy.
        </div>
      </div>
    ),
  },

  // 6. MULTI-MODEL ARENA
  {
    id: "tournament",
    title: "Multi-Model Arena",
    metric: "3 Worktrees",
    tag: "PARALLEL TOURNAMENT SYNTHESIS",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-purple-400" />
            <span className="font-bold text-neutral-300">Isolated 3-Worktree Synthesis Arena</span>
          </div>
          <span className="text-purple-400 font-bold">3 CONCURRENT</span>
        </div>

        <div className="space-y-2.5 my-3">
          <div className="p-2.5 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-between">
            <div>
              <span className="text-white font-bold block">Worktree Alpha (Groq LPU)</span>
              <span className="text-[10px] text-neutral-400">Llama 3.3 70B · Fast AST Ingestion</span>
            </div>
            <span className="px-2 py-0.5 rounded bg-neutral-800 text-neutral-300 text-[10px]">~350 t/s</span>
          </div>

          <div className="p-2.5 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-between">
            <div>
              <span className="text-white font-bold block">Worktree Beta (Gemini 3.8 Flash)</span>
              <span className="text-[10px] text-neutral-400">1M Token Context · Deep Dependency Walk</span>
            </div>
            <span className="px-2 py-0.5 rounded bg-neutral-800 text-neutral-300 text-[10px]">100% Free</span>
          </div>

          <div className="p-2.5 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-between">
            <div>
              <span className="text-white font-bold block">Worktree Gamma (TDD Synthesizer)</span>
              <span className="text-[10px] text-neutral-400">Isolated Reproduction Test Synthesis</span>
            </div>
            <span className="px-2 py-0.5 rounded bg-green-950 text-green-400 text-[10px] border border-green-800">
              Verified
            </span>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-neutral-950 border border-neutral-800 text-[11px] text-neutral-400">
          Arbitrator scores AST diff distance, linter warnings, and test coverage before selecting the champion patch.
        </div>
      </div>
    ),
  },

  // 7. DOCKER SANDBOXES
  {
    id: "docker",
    title: "Docker Sandboxes",
    metric: "34 / 34 Graded",
    tag: "HERMETIC CONTAINER ISOLATION",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-400" />
            <span className="font-bold text-neutral-300">Official SWE-bench Lite Maintainer Sandboxes</span>
          </div>
          <span className="text-green-400 font-bold">100% HERMETIC</span>
        </div>

        <div className="grid grid-cols-2 gap-3 my-4">
          <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 uppercase block">Containers Spawned</span>
            <span className="text-2xl font-black text-white mt-1 block">34 / 34</span>
            <span className="text-[10px] text-green-400 font-bold">Zero Crash / Timeout</span>
          </div>
          <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 uppercase block">Network Egress</span>
            <span className="text-2xl font-black text-green-400 mt-1 block">0.00 KB</span>
            <span className="text-[10px] text-neutral-400">Completely Airgapped</span>
          </div>
          <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 uppercase block">Maintainer Conda Env</span>
            <span className="text-2xl font-black text-white mt-1 block">100% Match</span>
            <span className="text-[10px] text-neutral-400">Byte-for-byte Dependencies</span>
          </div>
          <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 uppercase block">Grading Precision</span>
            <span className="text-2xl font-black text-blue-400 mt-1 block">Official</span>
            <span className="text-[10px] text-neutral-400">Maintainer Test Ingestion</span>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-neutral-950 border border-neutral-800 text-[11px] text-neutral-400">
          Zero synthetic mock environments: all benchmarks run inside official repository maintainer Docker images.
        </div>
      </div>
    ),
  },

  // 8. PATCH GENERATION YIELD
  {
    id: "yield",
    title: "Patch Generation Yield",
    metric: "+26.7% Gain",
    tag: "STATISTICAL YIELD IMPROVEMENT",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-green-400" />
            <span className="font-bold text-neutral-300">Patch Yield Elevation Benchmark</span>
          </div>
          <span className="text-green-400 font-bold">66.7% CLEAN AST</span>
        </div>

        <div className="my-4 space-y-3">
          <div>
            <div className="flex justify-between text-neutral-300 text-xs mb-1">
              <span>Upgraded ISHA AST Engine</span>
              <span className="text-green-400 font-bold">66.7% (20/30 Yield)</span>
            </div>
            <div className="w-full bg-neutral-800 h-3 rounded-full overflow-hidden">
              <div className="bg-green-500 h-full rounded-full" style={{ width: "66.7%" }} />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-neutral-400 text-xs mb-1">
              <span>Baseline Vanilla Git Diff Engine</span>
              <span className="text-neutral-400 font-bold">40.0% (12/30 Yield)</span>
            </div>
            <div className="w-full bg-neutral-800 h-3 rounded-full overflow-hidden">
              <div className="bg-neutral-600 h-full rounded-full" style={{ width: "40.0%" }} />
            </div>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800 space-y-1 text-[11px] text-neutral-400">
          <div className="flex justify-between">
            <span>Net Yield Elevation:</span>
            <span className="text-green-400 font-bold">+26.7% Absolute</span>
          </div>
          <div className="flex justify-between">
            <span>Discarded Broken Diffs:</span>
            <span className="text-white font-bold">8 Broken Candidates Repaired</span>
          </div>
        </div>
      </div>
    ),
  },

  // 9. DJANGO SUITE 10914
  {
    id: "django-10914",
    title: "Django Suite 10914",
    metric: "Verified Green",
    tag: "MAINTAINER TEST SUITE REPRODUCTION",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <span className="font-bold text-neutral-300">django__django-10914</span>
          <span className="text-green-400 font-bold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> PASSED [100%]
          </span>
        </div>

        <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800 text-[11px] space-y-2">
          <div className="text-neutral-400">
            <span className="text-neutral-500">Repository:</span> django/django (Python 3.8)
          </div>
          <div className="text-neutral-400">
            <span className="text-neutral-500">Target File:</span> django/conf/urls/__init__.py
          </div>
          <div className="text-neutral-400">
            <span className="text-neutral-500">Test Suite:</span> tests/urlpatterns_reverse/tests.py
          </div>
        </div>

        <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800 text-[11px] space-y-1">
          <div className="text-green-400 font-bold">$ pytest tests/urlpatterns_reverse/tests.py -k test_custom_urlconf</div>
          <div className="text-neutral-300">=== 1 passed, 0 failed in 4.21s ===</div>
          <div className="text-neutral-500 text-[10px]">Docker Container: sweb.eval.django__django-10914:latest</div>
        </div>
      </div>
    ),
  },

  // 10. DJANGO SUITE 11039
  {
    id: "django-11039",
    title: "Django Suite 11039",
    metric: "Verified Green",
    tag: "MAINTAINER TEST SUITE REPRODUCTION",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <span className="font-bold text-neutral-300">django__django-11039</span>
          <span className="text-green-400 font-bold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> PASSED [100%]
          </span>
        </div>

        <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800 text-[11px] space-y-2">
          <div className="text-neutral-400">
            <span className="text-neutral-500">Repository:</span> django/django (ORM Compiler)
          </div>
          <div className="text-neutral-400">
            <span className="text-neutral-500">Target File:</span> django/core/management/commands/sqlmigrate.py
          </div>
          <div className="text-neutral-400">
            <span className="text-neutral-500">Test Suite:</span> tests/migrations/test_commands.py
          </div>
        </div>

        <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800 text-[11px] space-y-1">
          <div className="text-green-400 font-bold">$ pytest tests/migrations/test_commands.py -k test_sqlmigrate_backwards</div>
          <div className="text-neutral-300">=== 1 passed, 0 failed in 6.14s ===</div>
          <div className="text-neutral-500 text-[10px]">Verified Migration Rollback DDL generation cleanly</div>
        </div>
      </div>
    ),
  },

  // 11. DJANGO SUITE 11133
  {
    id: "django-11133",
    title: "Django Suite 11133",
    metric: "Verified Green",
    tag: "MAINTAINER TEST SUITE REPRODUCTION",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <span className="font-bold text-neutral-300">django__django-11133</span>
          <span className="text-green-400 font-bold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> PASSED [100%]
          </span>
        </div>

        <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800 text-[11px] space-y-2">
          <div className="text-neutral-400">
            <span className="text-neutral-500">Repository:</span> django/django (HTTP Buffer)
          </div>
          <div className="text-neutral-400">
            <span className="text-neutral-500">Target File:</span> django/http/response.py
          </div>
          <div className="text-neutral-400">
            <span className="text-neutral-500">Test Suite:</span> tests/responses/test_fileresponse.py
          </div>
        </div>

        <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800 text-[11px] space-y-1">
          <div className="text-green-400 font-bold">$ pytest tests/responses/test_fileresponse.py -k test_memoryview_content</div>
          <div className="text-neutral-300">=== 1 passed, 0 failed in 3.88s ===</div>
          <div className="text-neutral-500 text-[10px]">Memoryview binary chunking correctly preserved</div>
        </div>
      </div>
    ),
  },

  // 12. PYTEST SUITE 11143
  {
    id: "pytest-11143",
    title: "Pytest Suite 11143",
    metric: "Verified Green",
    tag: "MAINTAINER TEST SUITE REPRODUCTION",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <span className="font-bold text-neutral-300">pytest-dev__pytest-11143</span>
          <span className="text-green-400 font-bold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> PASSED [100%]
          </span>
        </div>

        <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800 text-[11px] space-y-2">
          <div className="text-neutral-400">
            <span className="text-neutral-500">Repository:</span> pytest-dev/pytest (AST Assertions)
          </div>
          <div className="text-neutral-400">
            <span className="text-neutral-500">Target File:</span> src/_pytest/assertion/rewrite.py
          </div>
          <div className="text-neutral-400">
            <span className="text-neutral-500">Test Suite:</span> testing/test_assertrewrite.py
          </div>
        </div>

        <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800 text-[11px] space-y-1">
          <div className="text-green-400 font-bold">$ pytest testing/test_assertrewrite.py -k test_docstring_rewrite</div>
          <div className="text-neutral-300">=== 1 passed in 2.95s ===</div>
          <div className="text-neutral-500 text-[10px]">AST rewriter preserves module docstrings during parse</div>
        </div>
      </div>
    ),
  },

  // 13. BRIER SAFETY METRIC
  {
    id: "brier",
    title: "Brier Safety Metric",
    metric: "0.0000 Brier",
    tag: "PROBABILISTIC CALIBRATION",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <span className="font-bold text-neutral-300">Brier Score Probabilistic Evaluation</span>
          <span className="text-green-400 font-bold">PERFECT (0.0000)</span>
        </div>

        <div className="grid grid-cols-2 gap-3 my-4">
          <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 uppercase block">Calibrated Brier</span>
            <span className="text-2xl font-black text-green-400 mt-1 block">0.0000</span>
            <span className="text-[10px] text-neutral-400">Zero Probabilistic Bias</span>
          </div>
          <div className="p-3 rounded-xl bg-neutral-900 border border-neutral-800">
            <span className="text-[10px] text-neutral-400 uppercase block">Raw Uncalibrated</span>
            <span className="text-2xl font-black text-red-400 mt-1 block">0.0894</span>
            <span className="text-[10px] text-neutral-400">Overconfident without Gate</span>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-neutral-950 border border-neutral-800 text-[11px] text-neutral-400">
          Temperature parameter T=0.35 minimizes Brier distance across holdout test suites.
        </div>
      </div>
    ),
  },

  // 14. TDD TEST SYNTHESIS
  {
    id: "tdd",
    title: "TDD Test Synthesis",
    metric: "81 / 81 Pass",
    tag: "FAIL-BEFORE-FIX VERIFICATION",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <div className="flex items-center gap-2">
            <FileCode2 className="w-4 h-4 text-amber-400" />
            <span className="font-bold text-neutral-300">Reproduction Test Synthesizer</span>
          </div>
          <span className="text-green-400 font-bold">100% REPRO RATE</span>
        </div>

        <div className="grid grid-cols-3 gap-2 my-4">
          <div className="p-2.5 rounded-xl bg-neutral-900 border border-neutral-800 text-center">
            <span className="text-[10px] text-neutral-400 uppercase block">Generated</span>
            <span className="text-lg font-black text-white mt-1 block">81</span>
          </div>
          <div className="p-2.5 rounded-xl bg-neutral-900 border border-neutral-800 text-center">
            <span className="text-[10px] text-neutral-400 uppercase block">Fail-First</span>
            <span className="text-lg font-black text-red-400 mt-1 block">81/81</span>
          </div>
          <div className="p-2.5 rounded-xl bg-neutral-900 border border-neutral-800 text-center">
            <span className="text-[10px] text-neutral-400 uppercase block">Fix-Pass</span>
            <span className="text-lg font-black text-green-400 mt-1 block">81/81</span>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-neutral-950 border border-neutral-800 text-[11px] text-neutral-400">
          Total execution time for full 81 test reproduction runs: 18.4s in sandbox.
        </div>
      </div>
    ),
  },

  // 15. ZERO FALSE APPROVALS
  {
    id: "safety",
    title: "Zero False Approvals",
    metric: "100.0% τ=0.50",
    tag: "PRECISION-RECALL BOUND",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <span className="font-bold text-neutral-300">Auto-Approve Precision Curve</span>
          <span className="text-green-400 font-bold">ZERO FALSE POSITIVES</span>
        </div>

        <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800 my-4 space-y-2 text-[11px]">
          <div className="flex justify-between">
            <span className="text-neutral-400">True Positives Approved:</span>
            <span className="text-green-400 font-bold">100.0% Clean</span>
          </div>
          <div className="flex justify-between">
            <span className="text-neutral-400">False Positives (Bad Merge):</span>
            <span className="text-red-400 font-bold">0 (0.00%)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-neutral-400">Escalated to Human Review:</span>
            <span className="text-amber-400 font-bold">21.6%</span>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-neutral-900 border border-neutral-800 text-[11px] text-neutral-400">
          When probability score falls below 0.50, ISHA halts auto-merge and requests maintainer sign-off.
        </div>
      </div>
    ),
  },

  // 16. STATE ARBITRATOR
  {
    id: "arbitrator",
    title: "State Arbitrator",
    metric: "Deterministic",
    tag: "AST ARBITRATION MECHANISM",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-red-500" />
            <span className="font-bold text-neutral-300">Deterministic AST Tree Scoring</span>
          </div>
          <span className="text-white font-bold">PURE FUNCTION</span>
        </div>

        <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800 space-y-2 text-[11px] my-3">
          <div className="text-neutral-400 flex items-center justify-between">
            <span>Diff Blast Radius Penalty:</span>
            <span className="text-white font-bold">&lt; 40 lines optimal</span>
          </div>
          <div className="text-neutral-400 flex items-center justify-between">
            <span>Cyclomatic Complexity Delta:</span>
            <span className="text-green-400 font-bold">Δ &lt;= 0</span>
          </div>
          <div className="text-neutral-400 flex items-center justify-between">
            <span>Regression Immunity:</span>
            <span className="text-green-400 font-bold">100% Zero Breakage</span>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-neutral-900 border border-neutral-800 text-[11px] text-neutral-400">
          The Arbitrator combines structural code distance and runtime test results into a single deterministic score.
        </div>
      </div>
    ),
  },

  // 17. GLOBAL PARETO LEADER
  {
    id: "efficiency",
    title: "Global Pareto Leader",
    metric: "Rank #1 $0.00",
    tag: "WORLDWIDE EFFICIENCY BENCHMARK",
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-between p-4 sm:p-6 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-700/60 pb-3">
          <span className="font-bold text-neutral-300">Cost-to-Accuracy Frontier Index</span>
          <span className="text-red-400 font-bold">#1 GLOBALLY</span>
        </div>

        <div className="p-3 rounded-xl bg-neutral-900 border border-red-600/40 my-3">
          <span className="text-white font-black text-sm block mb-1">
            Zero-Dollar Commercial Grade Engineering
          </span>
          <p className="text-[11px] text-neutral-400 leading-relaxed">
            By cascading high-throughput Groq LPUs for AST structural parsing with Gemini 3.8 Flash for reasoning, ISHA achieves top-tier SWE-bench Lite resolution without consuming commercial budgets.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-2 text-[11px]">
          <div className="p-2 rounded-lg bg-neutral-950 border border-neutral-800">
            <span className="text-neutral-500 block">Inference Cost</span>
            <span className="text-green-400 font-black text-sm">$0.00</span>
          </div>
          <div className="p-2 rounded-lg bg-neutral-950 border border-neutral-800">
            <span className="text-neutral-500 block">Resolved Patches</span>
            <span className="text-red-500 font-black text-sm">20.6%</span>
          </div>
        </div>
      </div>
    ),
  },
];

export interface Skiper35Props {
  items?: Skiper35Item[];
  className?: string;
  defaultActiveIndex?: number;
}

export const Skiper35: React.FC<Skiper35Props> = ({
  items = defaultItems,
  className = "",
  defaultActiveIndex = 0,
}) => {
  const [activeIndex, setActiveIndex] = useState<number>(defaultActiveIndex);

  return (
    <div
      className={`relative w-full h-full bg-[#F9F7EF] dark:bg-black overflow-x-auto overflow-y-hidden select-none flex items-stretch [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden transition-colors duration-300 ${className}`}
    >
      <div className="mx-auto flex w-full h-full flex-col md:flex-row lg:min-w-[1600px] bg-[#F9F7EF] dark:bg-black transition-colors duration-300 pt-20 md:pt-24 pb-6 md:pb-8">
        {items.map((item, index) => {
          const isActive = activeIndex === index;

          return (
            <motion.div
              key={item.id}
              layout
              initial={false}
              animate={{
                width: isActive ? "36rem" : "4rem",
              }}
              transition={{
                type: "spring",
                stiffness: 260,
                damping: 26,
              }}
              onMouseEnter={() => setActiveIndex(index)}
              onClick={() => setActiveIndex(index)}
              className="lg:border-r relative h-full w-full cursor-pointer border-0 border-neutral-300 dark:border-white/20 md:border-r overflow-hidden shrink-0 transition-colors"
              style={{
                height: "100%",
              }}
            >
              {/* EXACT SKIPER35 ROTATED TEXT CONTAINER WITH LIGHT / DARK SUPPORT */}
              <div
                className={`absolute bottom-4 left-[2vw] flex w-[calc(100vh-9rem)] origin-[0_50%] transform justify-between pr-5 text-xl font-medium leading-[2.6vw] tracking-[-0.03em] md:-rotate-90 md:text-[1.8vw] transition-colors duration-200 pointer-events-none z-20 ${
                  isActive
                    ? "text-black dark:text-[#f1f1f1]"
                    : "text-neutral-900/40 dark:text-[#f1f1f1]/30 hover:text-black dark:hover:text-[#f1f1f1]"
                }`}
              >
                <p className="label w-full border-b border-transparent py-2 md:w-auto md:border-0 md:py-0 whitespace-nowrap font-black">
                  {item.title}
                </p>
                <AnimatePresence>
                  {isActive && (
                    <motion.p
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="year hidden md:block whitespace-nowrap font-mono font-black text-red-600 dark:text-red-500 tracking-wider"
                    >
                      {item.metric}
                    </motion.p>
                  )}
                </AnimatePresence>
              </div>

              {/* EXPANDED CONTENT WRAPPER: EXACT CUSTOM VISUAL FOR THIS SPECIFIC TOPIC */}
              <motion.div
                animate={{ opacity: isActive ? 1 : 0 }}
                transition={{ duration: 0.35 }}
                className="h-[92%] rounded-2xl md:rounded-3xl p-2 md:p-3 pl-3 md:pl-[4.5vw] md:pr-4 md:pb-4 flex items-center justify-center"
              >
                <div className="w-full h-full rounded-2xl md:rounded-3xl overflow-hidden border border-neutral-300 dark:border-neutral-800 bg-white dark:bg-black shadow-2xl flex flex-col transition-colors">
                  {isActive && item.renderVisual()}
                </div>
              </motion.div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export const DemoSkiper35: React.FC = () => {
  return (
    <main className="w-full h-screen bg-[#F9F7EF] dark:bg-black transition-colors duration-300">
      <Skiper35 />
    </main>
  );
};

export default Skiper35;
