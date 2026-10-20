"use client";

import React, { useRef } from "react";
import { motion } from "framer-motion";
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

const harnessCards = [
  {
    tag: "NEW",
    meta: "FIX CONSOLE",
    title: "Try a bug in the browser",
    body: "Describe a bug and watch ISHA synthesize a verified patch.",
    href: "/fix",
    tone: "coral" as const,
  },
  {
    tag: "LIVE",
    meta: "BENCHMARKS",
    title: "See the audited numbers",
    body: "Inspect SWE-bench metrics and container-graded results.",
    href: "/stats",
    tone: "sun" as const,
  },
  {
    tag: "01",
    meta: "LOCALIZE",
    title: "Read the repository",
    body: "AST maps, BM25 ranking, and a dependency graph pin the failing symbol.",
    tone: "sky" as const,
  },
  {
    tag: "02",
    meta: "PROVE RED",
    title: "Reproduce first",
    body: "A regression test must fail on the unpatched repo before any patch is written.",
    tone: "mint" as const,
  },
  {
    tag: "03",
    meta: "RACE 3",
    title: "Run the tournament",
    body: "Minimal-diff, call-site-aware, and root-cause candidates race in isolated worktrees.",
    tone: "lilac" as const,
  },
  {
    tag: "04",
    meta: "VERIFY GREEN",
    title: "Prove it in a container",
    body: "AST gates and official SWE-bench Docker tests reject regressions and unrelated churn.",
    tone: "peach" as const,
  },
  {
    tag: "05",
    meta: "ARBITRATE",
    title: "Pick the smallest diff",
    body: "The calibrated LAYA gate scores quality, issue match, and safety before approval.",
    tone: "cream" as const,
  },
  {
    tag: "06",
    meta: "SHIP",
    title: "Patch or pull request",
    body: "Preview the diff, apply it in place, or open a GitHub PR with isha fix --pr.",
    tone: "ink" as const,
  },
];

const cardClass =
  "group relative flex h-[330px] w-[252px] sm:w-[270px] shrink-0 snap-center flex-col justify-between overflow-hidden rounded-[28px] p-6 text-left ring-1 ring-inset shadow-[0_24px_60px_-28px_rgba(19,35,58,0.45)] transition-all duration-500 ease-out hover:-translate-y-4 hover:shadow-2xl";

export const AboutSection: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <section
      id="about"
      ref={containerRef}
      className="relative w-full py-24 sm:py-32 md:py-40 px-6 sm:px-10 md:px-16 lg:px-20 bg-[#F9F7EF] dark:bg-[#121212] text-black dark:text-[#F9F7EF] transition-colors duration-300 border-t border-b border-neutral-200/60 dark:border-neutral-900/60 overflow-hidden"
    >
      <div className="max-w-7xl mx-auto relative z-10">
        {/* Top Label */}
        <div className="mb-10 sm:mb-14">
          <span className="text-xs sm:text-sm font-mono uppercase tracking-[0.3em] text-neutral-500 dark:text-neutral-400 font-extrabold">
            What ISHA is
          </span>
        </div>

        {/* Main Grid: Editorial Prose on Left + Interactive Floating Sticky Notes on Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-14 items-start">
          {/* ================= LEFT COLUMN: BIG BOLD TYPOGRAPHY FLOW WITH SCROLL HIGHLIGHTS ================= */}
          <div className="lg:col-span-8">
            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-[54px] font-black tracking-tight text-neutral-950 dark:text-neutral-100 leading-[1.3] sm:leading-[1.25] md:leading-[1.22]">
              ISHA is an autonomous software-engineering harness that turns a{" "}
              <ScrollHighlight variant="brush" color="sky" delay={0.1}>
                bug report into a verified patch
              </ScrollHighlight>
              . It reads the repository, proves the bug with a{" "}
              <ScrollHighlight variant="round" color="coral" delay={0.25} strokeWidth={3.5}>
                failing regression test
              </ScrollHighlight>
              , races{" "}
              <ScrollHighlight variant="wavy" color="sun" delay={0.35}>
                three candidate fixes
              </ScrollHighlight>{" "}
              in isolated Git worktrees, and ships only the minimal diff that passes AST gates, container tests, and the{" "}
              <ScrollHighlight variant="double" color="red" delay={0.55} strokeWidth={3}>
                LAYA calibrated gate
              </ScrollHighlight>
              .
            </h2>

            <p className="mt-6 max-w-3xl text-base sm:text-lg font-bold leading-relaxed text-neutral-700 dark:text-neutral-300">
              On SWE-bench Lite, ISHA has resolved{" "}
              <span className="text-red-600 dark:text-red-500">76 / 300 instances</span> under the official Docker harness with an{" "}
              <span className="text-red-600 dark:text-red-500">88.8% clean AST patch yield</span> — at{" "}
              <span className="text-red-600 dark:text-red-500">$0.00 inference cost</span> using free-tier Groq and Gemini models.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a
                href="/fix"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-red-600 hover:bg-red-700 text-white text-xs font-black uppercase tracking-wider shadow-lg shadow-red-600/20 hover:scale-105 active:scale-95 transition-all"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                NEW · TRY ISHA FIX
              </a>
              <a
                href="/stats"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full border-2 border-neutral-300 dark:border-neutral-700 hover:border-red-600 dark:hover:border-red-500 text-neutral-800 dark:text-neutral-200 hover:text-red-600 dark:hover:text-red-500 text-xs font-black uppercase tracking-wider hover:scale-105 active:scale-95 transition-all"
              >
                LIVE BENCHMARKS
              </a>
            </div>
          </div>

          {/* ================= RIGHT COLUMN: INTERACTIVE TILTED STICKY NOTES ("these notes move ;)") ================= */}
          <div className="lg:col-span-4 relative flex flex-col items-center lg:items-end gap-6 pt-4 lg:pt-0">
            {/* Playful Arrow indicator - Matching jameschugh "these notes move ;)" */}
            <div className="flex items-center gap-2 text-xs font-mono text-neutral-500 dark:text-neutral-400 font-bold self-center lg:self-end pr-4">
              <span>these notes move ;)</span>
              <span className="text-sm">↗</span>
            </div>

            {/* Note 1: Yellow Sticky Note */}
            <motion.div
              drag
              dragConstraints={containerRef}
              dragElastic={0.15}
              whileDrag={{ scale: 1.05, cursor: "grabbing" }}
              whileHover={{ rotate: 0, scale: 1.02 }}
              onDragStart={() => sounds.playClick()}
              initial={{ rotate: -2 }}
              className="relative w-64 sm:w-72 bg-[#FFF4CC] dark:bg-[#FFF4CC] text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-10"
            >
              {/* Semi-transparent Scotch Tape */}
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-white/70 backdrop-blur-xs shadow-xs -rotate-1 border border-white/50" />

              <p className="text-base font-extrabold leading-snug tracking-tight text-neutral-900">
                76 / 300 official
                <br />
                Docker resolved.
                <br />
                88.8% clean AST yield.
              </p>
              <div className="mt-4 pt-3 border-t border-neutral-900/10 text-[10px] font-mono uppercase tracking-widest text-neutral-600 font-black">
                SWE-BENCH LITE · OFFICIAL DOCKER
              </div>
            </motion.div>

            {/* Note 2: Peach / Rose Sticky Note */}
            <motion.div
              drag
              dragConstraints={containerRef}
              dragElastic={0.15}
              whileDrag={{ scale: 1.05, cursor: "grabbing" }}
              whileHover={{ rotate: 0, scale: 1.02 }}
              onDragStart={() => sounds.playClick()}
              initial={{ rotate: 2 }}
              className="relative w-64 sm:w-72 bg-[#FFE8E2] dark:bg-[#FFE8E2] text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-20"
            >
              {/* Semi-transparent Scotch Tape */}
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-white/70 backdrop-blur-xs shadow-xs rotate-2 border border-white/50" />

              <p className="text-base font-extrabold leading-snug tracking-tight text-neutral-900">
                3 parallel worktrees.
                <br />
                8 container invariants.
                <br />
                0.0% patch abort rate.
              </p>
              <div className="mt-4 pt-3 border-t border-neutral-900/10 text-[10px] font-mono uppercase tracking-widest text-neutral-600 font-black">
                TOURNAMENT + CONTAINER INVARIANTS
              </div>
            </motion.div>

            {/* Note 3: White Sticker Note with Gateway Badges */}
            <motion.div
              drag
              dragConstraints={containerRef}
              dragElastic={0.15}
              whileDrag={{ scale: 1.05, cursor: "grabbing" }}
              whileHover={{ rotate: 0, scale: 1.02 }}
              onDragStart={() => sounds.playClick()}
              initial={{ rotate: -1 }}
              className="relative w-64 sm:w-72 bg-white dark:bg-neutral-100 text-neutral-900 rounded-sm p-6 shadow-xl shadow-neutral-900/10 cursor-grab select-none transition-shadow hover:shadow-2xl z-30"
            >
              {/* Semi-transparent Scotch Tape */}
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-white/80 backdrop-blur-xs shadow-xs -rotate-2 border border-neutral-200/60" />

              <p className="text-xs font-mono uppercase tracking-wider font-extrabold text-neutral-500 mb-2.5">
                Free-tier Pareto Engine
              </p>
              <p className="text-base font-extrabold leading-snug tracking-tight text-neutral-900 mb-3">
                LAYA ECE 0.0010.
                <br />
                Zero inference cost.
              </p>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md bg-[#F05A28] text-white font-black text-xs tracking-tight shadow-xs">
                  Groq
                </span>
                <span className="px-2.5 py-1 rounded-md bg-[#1A73E8] text-white font-black text-xs tracking-tight shadow-xs">
                  Gemini
                </span>
                <span className="px-2.5 py-1 rounded-md bg-[#2496ED] text-white font-black text-xs tracking-tight shadow-xs">
                  Docker
                </span>
              </div>
              <div className="mt-4 pt-3 border-t border-neutral-200 text-[10px] font-mono uppercase tracking-widest text-neutral-500 font-black">
                $0.00 INFERENCE COST
              </div>
            </motion.div>
          </div>
        </div>
      </div>

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
              What&apos;s new
            </p>
            <h3 className="mt-5 max-w-4xl text-4xl sm:text-5xl md:text-6xl lg:text-[76px] font-black leading-[0.95] tracking-[-0.055em] text-neutral-950 dark:text-[#F9F7EF]">
              The harness,{" "}
              <ScrollHighlight variant="brush" color="sun" delay={0.1}>
                end to end.
              </ScrollHighlight>
            </h3>
            <p className="mt-5 max-w-2xl text-sm sm:text-lg font-bold leading-relaxed text-neutral-600 dark:text-neutral-400">
              Two new ways to explore ISHA, plus the six-step loop behind every verified patch.
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
                const content = (
                  <>
                    <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-black/10" />
                    <span
                      aria-hidden="true"
                      className={`pointer-events-none absolute -bottom-7 -right-2 font-black leading-none tracking-[-0.08em] ${tone.num} ${
                        card.tag.length > 2 ? "text-[92px]" : "text-[118px]"
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
                        <span className="font-mono text-[9px] font-black uppercase tracking-[0.18em] opacity-60">
                          {card.meta}
                        </span>
                      </div>
                      <h4 className="mt-8 text-[27px] font-black leading-[1.02] tracking-[-0.045em]">
                        {card.title}
                      </h4>
                    </div>
                    <div className="relative z-10">
                      <p className={`text-[13px] font-semibold leading-relaxed ${tone.sub}`}>{card.body}</p>
                      {card.href && (
                        <span className="mt-5 inline-flex items-center gap-1.5 font-mono text-[10px] font-black uppercase tracking-[0.2em]">
                          Open
                          <span className="transition-transform group-hover:translate-x-0.5">↗</span>
                        </span>
                      )}
                    </div>
                  </>
                );

                return card.href ? (
                  <a
                    key={card.meta}
                    href={card.href}
                    className={`${cardClass} ${tone.card} ${tone.glow} cursor-pointer`}
                  >
                    {content}
                  </a>
                ) : (
                  <div key={card.meta} className={`${cardClass} ${tone.card}`}>
                    {content}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-3 flex items-center justify-center gap-3">
            <span className="font-hand text-2xl text-neutral-500 dark:text-neutral-400">pick a card</span>
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
