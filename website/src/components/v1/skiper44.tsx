"use client";

import React, { useRef } from "react";
import { motion, useScroll, useTransform, useMotionTemplate } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

export interface Skiper44Props {
  className?: string;
}

export const Skiper44: React.FC<Skiper44Props> = ({ className = "" }) => {
  const cardRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: cardRef,
    offset: ["start end", "end start"],
  });

  // Authentic Skiper44 transforms
  const textScale = useTransform(scrollYProgress, [0.2, 1], [1, 0.55]);
  const blurAmount = useTransform(scrollYProgress, [0.2, 0.8], [0, 20]);
  const backdropFilter = useMotionTemplate`blur(${blurAmount}px)`;
  const cardScale = useTransform(scrollYProgress, [0, 0.3], [0.95, 1]);

  const engineeringPillars = [
    "the autonomous harness",
    "the reproduction proof first",
    "the 3 isolated worktrees",
    "the pre-sandbox AST gates",
    "the calibrated LAYA score",
    "the verified minimal pull request",
    "zero false approvals",
    "the 8 container invariants",
    "the future of software",
  ];

  const engineSpecs = [
    "5-D AST Relevance Engine (BM25 + Dense Semantic)",
    "Mandatory Failing TDD Reproduction Test Gate",
    "3-Worktree Parallel Tournament in Git Sandboxes",
    "Pre-Sandbox Static AST & Import Compilation Gates",
    "Calibrated LAYA Arbitrator (ECE 0.0010)",
    "Minimal Churn Patch Synthesis & Format Cleaners",
  ];

  const containerInvariants = [
    "Class Scope Anchoring Invariant",
    "Guard Clause Completeness (Zero NoneType)",
    "Immutable Hashability Contracts",
    "Callable Decorator Preservation (__wrapped__)",
    "Dynamic Execution Namespace Isolation",
    "Strict Qualname Serializer Hierarchy",
  ];

  const benchmarkYield = [
    "76 / 300 Official Docker Verified Resolutions",
    "88.8% Clean AST Compilation Pass Yield",
    "0.0% Patch Abort Rate on Benchmark Suites",
    "Verified across Django, SymPy, Pytest, Matplotlib",
    "SQLite Semantic Ground Truth Historical Ledger",
  ];

  return (
    <section
      id="skiper44-section"
      className={`relative flex w-full flex-col items-center overflow-x-clip bg-[#F9F7EF] dark:bg-black pt-[35vh] sm:pt-[45vh] pb-[16vh] text-neutral-900 dark:text-[#F9F7EF] transition-colors select-none ${className}`}
    >
      {/* ================= STICKY TEXT WITH BLUR (SKIPER 44) ================= */}
      <motion.div
        style={{ scale: textScale }}
        className="sticky top-[14%] sm:top-[18%] flex gap-2 sm:gap-4 md:gap-6 pb-10 text-2xl sm:text-4xl md:text-5xl lg:text-6xl font-black tracking-tighter z-10 max-w-6xl px-4"
      >
        {/* Fixed Prefix: "We Engineer" with Top and Bottom Viewport Masks matching website background */}
        <div className="sticky top-[50%] h-fit shrink-0">
          <h1 className="whitespace-nowrap text-red-600 dark:text-red-500 uppercase font-black tracking-tight">
            We Engineer
          </h1>

          {/* Top Mask: Hides items scrolling above the focal window (100% solid matching page background) */}
          <div className="pointer-events-none absolute left-full top-0 z-10 h-[45vh] w-[200vw] -translate-y-full bg-[#F9F7EF] dark:bg-black transition-colors">
            <div className="absolute bottom-0 inset-x-0 h-16 bg-gradient-to-t from-transparent to-[#F9F7EF] dark:to-black" />
          </div>

          {/* Bottom Mask: Hides items scrolling below the focal window (100% solid matching page background) */}
          <div className="pointer-events-none absolute bottom-0 left-full z-10 h-[45vh] w-[200vw] translate-y-full bg-[#F9F7EF] dark:bg-black transition-colors">
            <div className="absolute top-0 inset-x-0 h-16 bg-gradient-to-b from-transparent to-[#F9F7EF] dark:to-black" />
          </div>
        </div>

        {/* Scrollable Items Column (Moves past "We Engineer" as user scrolls page) */}
        <div className="h-fit space-y-3 sm:space-y-4 pl-1">
          {engineeringPillars.map((item, idx) => (
            <h2
              key={idx}
              className="text-neutral-900 dark:text-[#F9F7EF] hover:text-red-600 dark:hover:text-red-400 transition-colors uppercase whitespace-nowrap cursor-default"
            >
              {item}
            </h2>
          ))}
        </div>

        {/* Scroll-Driven Progressive Backdrop Blur Overlay: Fully transparent background, pure optical blur */}
        <motion.div
          style={{
            backdropFilter,
            WebkitBackdropFilter: backdropFilter,
          }}
          className="pointer-events-none absolute inset-0 bg-transparent"
        />
      </motion.div>

      {/* ================= POPPING DETAILS CARD (SKIPER 44 POPOUT) ================= */}
      <motion.div
        ref={cardRef}
        style={{ scale: cardScale }}
        className="rounded-3xl sm:rounded-4xl z-20 mt-[24vh] flex w-full max-w-5xl flex-col items-center space-y-14 sm:space-y-16 bg-[#121212] text-white py-[12vh] sm:py-[18vh] px-6 sm:px-14 font-medium tracking-tight shadow-2xl border border-neutral-800 backdrop-blur-2xl mx-4"
      >
        {/* Header Label */}
        <div className="flex items-center gap-2 font-mono text-[10px] sm:text-xs font-black uppercase tracking-[0.25em] text-red-500">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <span>AUTONOMOUS SOFTWARE ENGINEERING SPECIFICATION</span>
        </div>

        {/* Section 1: Core Engine */}
        <div className="grid w-full max-w-2xl grid-cols-1 sm:grid-cols-12 gap-4 sm:gap-6 text-sm sm:text-base font-bold">
          <p className="sm:col-span-4 text-left sm:text-right font-mono text-xs uppercase tracking-wider text-neutral-500 pt-1">
            Core Engine
          </p>
          <ul className="sm:col-span-8 space-y-2 text-neutral-200">
            {engineSpecs.map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-red-500 font-mono text-xs shrink-0 select-none">▸</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Section 2: Container Invariants */}
        <div className="grid w-full max-w-2xl grid-cols-1 sm:grid-cols-12 gap-4 sm:gap-6 text-sm sm:text-base font-bold pt-4 border-t border-neutral-800/80">
          <p className="sm:col-span-4 text-left sm:text-right font-mono text-xs uppercase tracking-wider text-neutral-500 pt-1">
            8 Invariants
          </p>
          <ul className="sm:col-span-8 space-y-2 text-neutral-200">
            {containerInvariants.map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-red-500 font-mono text-xs shrink-0 select-none">▸</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Section 3: Benchmark Yield */}
        <div className="grid w-full max-w-2xl grid-cols-1 sm:grid-cols-12 gap-4 sm:gap-6 text-sm sm:text-base font-bold pt-4 border-t border-neutral-800/80">
          <p className="sm:col-span-4 text-left sm:text-right font-mono text-xs uppercase tracking-wider text-neutral-500 pt-1">
            Ground Truth
          </p>
          <ul className="sm:col-span-8 space-y-2 text-neutral-200">
            {benchmarkYield.map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-emerald-400 font-mono text-xs shrink-0 select-none">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* CTAs */}
        <div className="pt-6 flex flex-wrap items-center justify-center gap-4">
          <a
            href="/fix"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-red-600 hover:bg-red-700 text-white font-mono text-xs font-black uppercase tracking-wider shadow-lg shadow-red-600/30 hover:scale-105 active:scale-95 transition-all cursor-pointer"
          >
            <span>Launch ISHA Fix</span>
            <ArrowUpRight className="w-4 h-4 stroke-[3]" />
          </a>
          <a
            href="/stats"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full border border-neutral-700 hover:border-neutral-400 text-neutral-300 hover:text-white font-mono text-xs font-black uppercase tracking-wider hover:scale-105 active:scale-95 transition-all cursor-pointer"
          >
            <span>View Verified Stats</span>
          </a>
        </div>
      </motion.div>
    </section>
  );
};

export default Skiper44;
