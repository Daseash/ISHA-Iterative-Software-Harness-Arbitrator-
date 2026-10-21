"use client";

import React, { useRef } from "react";
import { motion } from "framer-motion";
import { ScrollHighlight } from "./ScrollHighlight";
import { sounds } from "../../utils/sound";

export const AboutSection: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <section
      id="about"
      ref={containerRef}
      className="relative w-full py-24 sm:py-32 md:py-40 px-6 sm:px-10 md:px-16 lg:px-20 bg-[#F9F7EF] dark:bg-black text-black dark:text-[#F9F7EF] transition-colors duration-300 border-t border-b border-neutral-200/60 dark:border-neutral-900/60 overflow-hidden"
    >
      <div className="max-w-7xl mx-auto relative z-10">
        {/* Top Header Label */}
        <div className="mb-10 sm:mb-14">
          <div className="flex items-center justify-between">
            <span className="text-xs sm:text-sm font-mono uppercase tracking-[0.3em] text-neutral-500 dark:text-neutral-400 font-extrabold">
              WHAT ISHA IS · ARCHITECTURAL SPECIFICATION
            </span>
            <span className="font-mono text-[11px] font-bold text-red-600 dark:text-red-500 uppercase tracking-widest hidden sm:inline">
              PROD VERSION 0.1.0
            </span>
          </div>
        </div>

        {/* Main Editorial Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-14 items-start">
          {/* Left Column: Flowing Bold Editorial Matter */}
          <div className="lg:col-span-8 space-y-7">
            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-[50px] font-black tracking-tight text-neutral-950 dark:text-neutral-100 leading-[1.28] sm:leading-[1.24] md:leading-[1.2]">
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

            <p className="max-w-3xl text-lg sm:text-xl font-bold leading-relaxed text-neutral-800 dark:text-neutral-200">
              Unlike conversational chatbots that aimlessly edit live files and guess in terminal bash loops, ISHA enforces an empirical scientific process:{" "}
              <span className="text-red-600 dark:text-red-500 font-black">
                Never touch code without proving the bug exists first
              </span>
              ,{" "}
              <span className="text-neutral-950 dark:text-white font-black">
                never mutate the user&apos;s active branch
              </span>
              , and{" "}
              <span className="text-neutral-950 dark:text-white font-black">
                never accept a patch without clean regression proofs
              </span>
              .
            </p>

            <p className="max-w-3xl text-base sm:text-lg font-bold leading-relaxed text-neutral-700 dark:text-neutral-300">
              When an issue arrives, ISHA executes a{" "}
              <ScrollHighlight variant="brush" color="mint" delay={0.2}>
                5-dimensional relevance engine
              </ScrollHighlight>{" "}
              combining saturated BM25 lexical search (k1=1.5), dense 384-dimensional semantic embeddings, AST definition graphs, caller hierarchies, and enclosing class scopes to pinpoint the exact failing symbols without dumping entire files into context.
            </p>

            <p className="max-w-3xl text-base sm:text-lg font-bold leading-relaxed text-neutral-700 dark:text-neutral-300">
              Once localized, ISHA synthesizes a standalone reproduction script and executes it in an isolated sandbox. If the unpatched repository does not fail, execution halts immediately—no code is ever written for an unverified bug. Once red, three diverse candidates (
              <span className="text-neutral-950 dark:text-white font-black">minimal diff</span>,{" "}
              <span className="text-neutral-950 dark:text-white font-black">call-site aware</span>, and{" "}
              <span className="text-neutral-950 dark:text-white font-black">root-cause first</span>
              ) race concurrently in dedicated Git worktrees. Every candidate must pass{" "}
              <ScrollHighlight variant="round" color="coral" delay={0.3}>
                pre-sandbox AST compilation gates
              </ScrollHighlight>{" "}
              to eliminate syntax errors, indentation defects, and broken imports before ever entering Docker.
            </p>

            <p className="max-w-3xl text-base sm:text-lg font-bold leading-relaxed text-neutral-700 dark:text-neutral-300">
              If a container test fails, verbatim pytest tracebacks and container stderr feed directly back into the coder for up to two closed-loop repair rounds. The final candidate is scored by the{" "}
              <ScrollHighlight variant="double" color="red" delay={0.4}>
                calibrated LAYA arbitrator
              </ScrollHighlight>
              , which penalizes code churn exponentially, enforces 8 container negative invariants (class anchoring, guard completeness, immutable hashability, and qualname hierarchy), verifies against historical failures in the SQLite semantic ledger, and exports an audited, minimal pull request.
            </p>

            {/* Direct CTA Action Links */}
            <div className="pt-3 flex flex-wrap items-center gap-3">
              <a
                href="/fix"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-red-600 hover:bg-red-700 text-white text-xs font-black uppercase tracking-wider shadow-lg shadow-red-600/25 hover:scale-105 active:scale-95 transition-all cursor-pointer"
              >
                <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                TRY ISHA FIX IN BROWSER
              </a>
              <a
                href="/stats"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full border-2 border-neutral-300 dark:border-neutral-700 hover:border-red-600 dark:hover:border-red-500 text-neutral-900 dark:text-neutral-100 hover:text-red-600 dark:hover:text-red-400 text-xs font-black uppercase tracking-wider hover:scale-105 active:scale-95 transition-all cursor-pointer"
              >
                AUDITED BENCHMARKS ↗
              </a>
            </div>
          </div>

          {/* Right Column: Draggable Scotch-Taped Sticky Notes */}
          <div className="lg:col-span-4 relative flex flex-col items-center lg:items-end gap-5 pt-4 lg:pt-0">
            <div className="flex items-center gap-2 text-xs font-mono text-neutral-500 dark:text-neutral-400 font-bold self-center lg:self-end pr-4">
              <span>drag these notes ;)</span>
              <span className="text-sm">↗</span>
            </div>

            {/* Note 1: Yellow Sticky Note - Golden Suite Validation */}
            <motion.div
              drag
              dragConstraints={containerRef}
              dragElastic={0.15}
              whileDrag={{ scale: 1.05, cursor: "grabbing" }}
              whileHover={{ rotate: 0, scale: 1.02 }}
              onDragStart={() => sounds.playClick()}
              initial={{ rotate: -2 }}
              className="relative w-64 sm:w-76 bg-[#FFF4CC] text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-10"
            >
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-white/70 backdrop-blur-xs shadow-xs -rotate-1 border border-white/50" />
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider font-extrabold text-neutral-600">
                  GOLDEN SUITE VERIFIED
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
                CONTAINER-GRADED HARNESS
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
              className="relative w-64 sm:w-76 bg-[#FFE8E2] text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-20"
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
                Cosine similarity &gt;0.92 vetoes repeats.
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
              className="relative w-64 sm:w-76 bg-[#E3F5EC] text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-40"
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

            {/* Note 5: Sky Blue Note - 3 Worktree Isolated Sandboxes */}
            <motion.div
              drag
              dragConstraints={containerRef}
              dragElastic={0.15}
              whileDrag={{ scale: 1.05, cursor: "grabbing" }}
              whileHover={{ rotate: 0, scale: 1.02 }}
              onDragStart={() => sounds.playClick()}
              initial={{ rotate: -2 }}
              className="relative w-64 sm:w-76 bg-[#E2F0FD] text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-50"
            >
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-white/70 backdrop-blur-xs shadow-xs -rotate-1 border border-white/50" />
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider font-extrabold text-neutral-600">
                  ISOLATED SANDBOXES
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-800 font-black">
                  3 WORKTREES
                </span>
              </div>
              <p className="text-base font-extrabold leading-snug tracking-tight text-neutral-900">
                Minimal diff vs call-site vs root-cause.
                <br />
                Parallel competitive tournament.
                <br />
                Active branch remains 100% untouched.
              </p>
              <div className="mt-4 pt-3 border-t border-blue-900/10 text-[10px] font-mono uppercase tracking-widest text-blue-700 font-black">
                PARALLEL TOURNAMENT
              </div>
            </motion.div>

            {/* Note 6: Lilac Note - Mandatory TDD Red-to-Green */}
            <motion.div
              drag
              dragConstraints={containerRef}
              dragElastic={0.15}
              whileDrag={{ scale: 1.05, cursor: "grabbing" }}
              whileHover={{ rotate: 0, scale: 1.02 }}
              onDragStart={() => sounds.playClick()}
              initial={{ rotate: 2 }}
              className="relative w-64 sm:w-76 bg-[#F0EBFF] text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-50"
            >
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-white/70 backdrop-blur-xs shadow-xs rotate-2 border border-white/50" />
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider font-extrabold text-neutral-600">
                  EMPIRICAL METHODOLOGY
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-800 font-black">
                  MANDATORY TDD
                </span>
              </div>
              <p className="text-base font-extrabold leading-snug tracking-tight text-neutral-900">
                Red-to-Green reproduction test first.
                <br />
                Zero code edits if unpatched passes.
                <br />
                Pre-sandbox AST compilation gates.
              </p>
              <div className="mt-4 pt-3 border-t border-purple-900/10 text-[10px] font-mono uppercase tracking-widest text-purple-700 font-black">
                MATHEMATICAL VERIFICATION
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
