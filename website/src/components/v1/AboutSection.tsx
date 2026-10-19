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
      className="relative w-full py-24 sm:py-32 md:py-40 px-6 sm:px-10 md:px-16 lg:px-20 bg-[#F9F7EF] dark:bg-[#121212] text-black dark:text-[#F9F7EF] transition-colors duration-300 border-t border-b border-neutral-200/60 dark:border-neutral-900/60 overflow-hidden"
    >
      <div className="max-w-7xl mx-auto relative z-10">
        {/* Top Label - Matching "How I got here" in jameschugh */}
        <div className="mb-10 sm:mb-14">
          <span className="text-xs sm:text-sm font-mono uppercase tracking-[0.3em] text-neutral-500 dark:text-neutral-400 font-extrabold">
            How we got here
          </span>
        </div>

        {/* Main Grid: Editorial Prose on Left + Interactive Floating Sticky Notes on Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-14 items-start">
          {/* ================= LEFT COLUMN: BIG BOLD TYPOGRAPHY FLOW WITH SCROLL HIGHLIGHTS ================= */}
          <div className="lg:col-span-8">
            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-[54px] font-black tracking-tight text-neutral-950 dark:text-neutral-100 leading-[1.3] sm:leading-[1.25] md:leading-[1.22]">
              Standard AI coders fail on benchmarks because{" "}
              <ScrollHighlight variant="brush" color="sky" delay={0.1}>
                prompt loops cannot
              </ScrollHighlight>{" "}
              replace container invariants. Learning{" "}
              <ScrollHighlight variant="round" color="coral" delay={0.25} strokeWidth={3.5}>
                how real software breaks,
              </ScrollHighlight>{" "}
              we replaced stochastic trial-and-error with{" "}
              <ScrollHighlight variant="wavy" color="sun" delay={0.35}>
                deterministic engineering invariants.
              </ScrollHighlight>{" "}
              We race 3-worktree tournaments across{" "}
              <ScrollHighlight variant="brush" color="lilac" delay={0.45}>
                isolated sandboxes,
              </ScrollHighlight>{" "}
              enforce strict TDD red-to-green test synthesis, and calibrate decisions with LAYA arbitration to fix the{" "}
              <ScrollHighlight variant="double" color="red" delay={0.55} strokeWidth={3}>
                "hallucinated regression" moments
              </ScrollHighlight>{" "}
              for good.
            </h2>
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
                300 / 300 instances
                <br />
                run btw. Verified in
                <br />
                Docker containers too.
              </p>
              <div className="mt-4 pt-3 border-t border-neutral-900/10 text-[10px] font-mono uppercase tracking-widest text-neutral-600 font-black">
                SWE-BENCH LITE · CLASS OF 2026
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
                0.0% patch abort rate.
                <br />
                Every single repair
                <br />
                anchored to AST qualname.
              </p>
              <div className="mt-4 pt-3 border-t border-neutral-900/10 text-[10px] font-mono uppercase tracking-widest text-neutral-600 font-black">
                8 CONTAINER INVARIANTS
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
    </section>
  );
};

export default AboutSection;
