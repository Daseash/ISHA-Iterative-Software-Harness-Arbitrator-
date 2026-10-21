import React, { useState, useEffect, useRef } from "react";
import { motion, useInView, AnimatePresence } from "framer-motion";
import { X, ArrowUpRight } from "lucide-react";
import { sounds } from "../../utils/sound";

export interface PipelineCard {
  tag: string;
  meta: string;
  title: string;
  body: string;
  tone: "sky" | "mint" | "lilac" | "peach" | "sun" | "cream" | "coral" | "ink";
}

const tones = {
  sky: {
    bg: "bg-[#5B8DEF]",
    text: "text-white",
    tag: "bg-white/20 text-white",
    sub: "text-white/90",
    num: "text-white/15",
    border: "border-white/25",
    shadow: "shadow-[0_24px_50px_-12px_rgba(91,141,239,0.55)]",
  },
  mint: {
    bg: "bg-[#59B98A]",
    text: "text-neutral-950",
    tag: "bg-black/15 text-neutral-950",
    sub: "text-neutral-900/85",
    num: "text-black/10",
    border: "border-black/10",
    shadow: "shadow-[0_24px_50px_-12px_rgba(89,185,138,0.55)]",
  },
  lilac: {
    bg: "bg-[#8E7CC3]",
    text: "text-white",
    tag: "bg-white/20 text-white",
    sub: "text-white/90",
    num: "text-white/15",
    border: "border-white/25",
    shadow: "shadow-[0_24px_50px_-12px_rgba(142,124,195,0.55)]",
  },
  peach: {
    bg: "bg-[#E8926A]",
    text: "text-neutral-950",
    tag: "bg-black/15 text-neutral-950",
    sub: "text-neutral-900/85",
    num: "text-black/10",
    border: "border-black/10",
    shadow: "shadow-[0_24px_50px_-12px_rgba(232,146,106,0.55)]",
  },
  sun: {
    bg: "bg-[#F2B94B]",
    text: "text-neutral-950",
    tag: "bg-black/15 text-neutral-950",
    sub: "text-neutral-900/85",
    num: "text-black/10",
    border: "border-black/10",
    shadow: "shadow-[0_24px_50px_-12px_rgba(242,185,75,0.55)]",
  },
  cream: {
    bg: "bg-[#F0E6CF]",
    text: "text-neutral-950",
    tag: "bg-black/15 text-neutral-950",
    sub: "text-neutral-900/85",
    num: "text-black/10",
    border: "border-black/10",
    shadow: "shadow-[0_24px_50px_-12px_rgba(240,230,207,0.55)]",
  },
  coral: {
    bg: "bg-[#E9543F]",
    text: "text-white",
    tag: "bg-white/20 text-white",
    sub: "text-white/90",
    num: "text-white/15",
    border: "border-white/25",
    shadow: "shadow-[0_24px_50px_-12px_rgba(233,84,63,0.55)]",
  },
  ink: {
    bg: "bg-[#17171A]",
    text: "text-white",
    tag: "bg-white/15 text-white",
    sub: "text-white/80",
    num: "text-white/10",
    border: "border-white/20",
    shadow: "shadow-[0_24px_50px_-12px_rgba(23,23,26,0.85)]",
  },
} as const;

export const defaultPipelineCards: PipelineCard[] = [
  {
    tag: "01",
    meta: "HYBRID RAG LOCALIZATION",
    title: "5D Relevance Scoring",
    body: "Saturated BM25 (k1=1.5), BGE embeddings, AST definition graphs, and caller hierarchies locate the exact failing symbol.",
    tone: "sky",
  },
  {
    tag: "02",
    meta: "MANDATORY TDD PROOF",
    title: "Reproduce Red First",
    body: "A standalone reproduction test MUST fail on unpatched code. If the unpatched repo passes, ISHA halts immediately.",
    tone: "mint",
  },
  {
    tag: "03",
    meta: "PARALLEL TOURNAMENT",
    title: "3 Isolated Worktrees",
    body: "Minimal-diff, call-site-aware, and root-cause strategies race concurrently. Main branch remains 100% untouched.",
    tone: "lilac",
  },
  {
    tag: "04",
    meta: "AST STATIC GATES",
    title: "Pre-Sandbox Validation",
    body: "Pre-sandbox ast.parse() eliminates indentation errors, missing imports, and broken syntax before Docker execution.",
    tone: "peach",
  },
  {
    tag: "05",
    meta: "CLOSED-LOOP REPAIR",
    title: "Verbatim Pytest Feedback",
    body: "Real traceback lines and container stderr feed directly back into the coder for up to 2 targeted self-repair rounds.",
    tone: "sun",
  },
  {
    tag: "06",
    meta: "CALIBRATED ARBITRATION",
    title: "LAYA Composite Gate",
    body: "Multi-factor scoring rewards surgical hunks with exponential churn penalties and hard vetoes on security or logic drift.",
    tone: "cream",
  },
  {
    tag: "07",
    meta: "INSTITUTIONAL MEMORY",
    title: "NEVER-DO Negative Veto",
    body: "SQLite ground truth + 384-d semantic ledger prevents repeating known container-graded failures across identical repos.",
    tone: "coral",
  },
  {
    tag: "08",
    meta: "PRODUCTION SHIPPING",
    title: "Patch or Automated PR",
    body: "Export unified diffs, apply cleanly with atomic safety, or open an audited GitHub Pull Request with isha fix --pr.",
    tone: "ink",
  },
];

export interface PipelinePlanesProps {
  cards?: PipelineCard[];
  photoWidth?: number;
  photoHeight?: number;
  spread?: number;
  tilt?: number;
  depth?: number;
  className?: string;
}

export const PipelinePlanes: React.FC<PipelinePlanesProps> = ({
  cards = defaultPipelineCards,
  photoWidth = 240,
  photoHeight = 330,
  spread = 120,
  tilt = 10,
  depth = 14,
  className = "",
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: false, amount: 0.1 });

  // Escape key closes focused modal and removes blur
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && selectedIndex !== null) {
        sounds.playClick();
        setSelectedIndex(null);
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [selectedIndex]);

  const centerIndex = (cards.length - 1) / 2;

  // Selected card details for spotlight modal
  const selectedCard = selectedIndex !== null ? cards[selectedIndex] : null;
  const selectedTone = selectedCard ? tones[selectedCard.tone] : null;

  return (
    <>
      <div
        ref={containerRef}
        className={`relative w-full flex flex-col items-center justify-center py-12 select-none transition-all duration-300 ${
          selectedIndex !== null ? "filter blur-[6px] opacity-40 pointer-events-none" : ""
        } ${className}`}
        style={{ minHeight: `${photoHeight + 140}px` }}
      >
        {/* 3D Perspective Stage */}
        <div
          className="relative flex items-center justify-center w-full"
          style={{
            perspective: 1400,
            perspectiveOrigin: "center center",
            height: `${photoHeight + 40}px`,
          }}
        >
          <div className="relative flex items-center justify-center w-full h-full">
            {cards.map((card, i) => {
              const tone = tones[card.tone];

              // Base offset when spread out
              const baseOffset = (i - centerIndex) * spread;

              // Neighbours shift outwards smoothly when one card is hovered
              let hoverShift = 0;
              if (hoveredIndex !== null) {
                if (i < hoveredIndex) {
                  hoverShift = -45;
                } else if (i > hoveredIndex) {
                  hoverShift = 45;
                }
              }

              const isHovered = hoveredIndex === i;

              // Slanted 3D plane angles
              const normalRotateZ = -tilt * 0.72;
              const normalRotateY = 15;
              const normalRotateX = 4;

              return (
                <motion.div
                  key={card.tag}
                  className={`absolute cursor-pointer rounded-[26px] p-5 sm:p-6 overflow-hidden flex flex-col justify-between ${tone.bg} ${tone.text} ${tone.shadow} border ${tone.border} transition-colors duration-200`}
                  style={{
                    width: `${photoWidth}px`,
                    height: `${photoHeight}px`,
                    transformStyle: "preserve-3d",
                    zIndex: isHovered ? 80 : i + 10,
                  }}
                  initial={{
                    x: (i % 3 - 1) * 6,
                    y: (i - centerIndex) * -4,
                    scale: 0.95,
                    rotateZ: (i % 2 === 0 ? -1 : 1) * (4 + i * 2),
                    rotateY: 0,
                    rotateX: 0,
                    opacity: 0.85,
                  }}
                  animate={
                    isInView
                      ? {
                          // Spreads out when coming to this section
                          x: baseOffset + hoverShift,
                          y: isHovered ? -35 : (i - centerIndex) * depth,
                          scale: isHovered ? 1.15 : 1,
                          rotateZ: isHovered ? 0 : normalRotateZ,
                          rotateY: isHovered ? 0 : normalRotateY,
                          rotateX: isHovered ? 0 : normalRotateX,
                          opacity: 1,
                        }
                      : {
                          // Stacked together initially
                          x: (i % 3 - 1) * 6,
                          y: (i - centerIndex) * -4,
                          scale: 0.95,
                          rotateZ: (i % 2 === 0 ? -1 : 1) * (4 + i * 2),
                          rotateY: 0,
                          rotateX: 0,
                          opacity: 0.85,
                        }
                  }
                  transition={{
                    type: "spring",
                    stiffness: 190,
                    damping: 24,
                    delay: isInView ? i * 0.05 : 0,
                  }}
                  whileHover={{
                    scale: 1.16,
                    y: -35,
                    rotateZ: 0,
                    rotateY: 0,
                    rotateX: 0,
                    transition: { duration: 0.22, ease: "easeOut" },
                  }}
                  onMouseEnter={() => setHoveredIndex(i)}
                  onMouseLeave={() => setHoveredIndex(null)}
                  onClick={() => {
                    sounds.playClick();
                    setSelectedIndex(i);
                  }}
                >
                  {/* Giant Stylized Watermark Number in background */}
                  <span
                    aria-hidden="true"
                    className={`pointer-events-none absolute -bottom-7 -right-2 font-black leading-none tracking-[-0.08em] select-none text-[115px] ${tone.num}`}
                  >
                    {card.tag}
                  </span>

                  {/* Top: Stage Pill Badge + Subsystem Category */}
                  <div className="relative z-10">
                    <div className="flex items-start justify-between gap-2">
                      <span
                        className={`rounded-full px-2.5 py-0.5 font-mono text-[10px] font-black uppercase tracking-wider ${tone.tag}`}
                      >
                        {card.tag}
                      </span>
                      <span className="font-mono text-[9px] font-black uppercase tracking-wider opacity-75 truncate text-right">
                        {card.meta}
                      </span>
                    </div>
                    <h3 className="mt-4 text-xl sm:text-[22px] font-black leading-tight tracking-tight">
                      {card.title}
                    </h3>
                  </div>

                  {/* Bottom: Verbatim Body Text */}
                  <div className="relative z-10 pt-2">
                    <p className={`text-[12px] font-semibold leading-relaxed ${tone.sub}`}>
                      {card.body}
                    </p>
                  </div>

                  {/* Subtle glass reflection highlight */}
                  <div className="absolute inset-0 bg-gradient-to-tr from-black/15 via-transparent to-white/20 pointer-events-none" />
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Interactive Micro-Hint */}
        <div className="mt-8 flex items-center justify-center gap-2 text-xs font-mono font-bold text-neutral-500 dark:text-neutral-400">
          <span>click any card to focus with blur &amp; sound</span>
          <span>↗</span>
        </div>
      </div>

      {/* ================= MODAL SPOTLIGHT OVERLAY WITH BACKGROUND BLUR ================= */}
      <AnimatePresence>
        {selectedIndex !== null && selectedCard && selectedTone && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
            {/* Background Blur Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              onClick={() => {
                sounds.playClick();
                setSelectedIndex(null);
              }}
              className="absolute inset-0 bg-black/60 dark:bg-black/80 backdrop-blur-md cursor-pointer"
            />

            {/* Elevated Focused Card */}
            <motion.div
              initial={{ scale: 0.88, opacity: 0, y: 30 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              transition={{ type: "spring", stiffness: 380, damping: 28 }}
              onClick={(e) => e.stopPropagation()}
              className={`relative z-10 w-full max-w-md sm:max-w-lg rounded-[32px] p-7 sm:p-9 shadow-2xl overflow-hidden flex flex-col justify-between border ${selectedTone.bg} ${selectedTone.text} ${selectedTone.border} ${selectedTone.shadow}`}
              style={{ minHeight: "440px" }}
            >
              {/* Giant Watermark Number */}
              <span
                aria-hidden="true"
                className={`pointer-events-none absolute -bottom-10 -right-4 font-black leading-none tracking-[-0.08em] select-none text-[180px] ${selectedTone.num}`}
              >
                {selectedCard.tag}
              </span>

              {/* Header row */}
              <div className="relative z-10 flex items-center justify-between w-full mb-6">
                <span className={`rounded-full px-3.5 py-1 font-mono text-xs font-black uppercase tracking-wider ${selectedTone.tag}`}>
                  STAGE {selectedCard.tag} OF 08
                </span>

                <button
                  type="button"
                  onClick={() => {
                    sounds.playClick();
                    setSelectedIndex(null);
                  }}
                  className="flex items-center justify-center w-9 h-9 rounded-full bg-black/20 hover:bg-black/35 text-white transition-all cursor-pointer shadow-md"
                  aria-label="Close card focus"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Main Content */}
              <div className="relative z-10 flex-1 flex flex-col justify-center my-4">
                <span className="font-mono text-xs font-black uppercase tracking-widest opacity-80 mb-2">
                  {selectedCard.meta}
                </span>
                <h3 className="text-3xl sm:text-4xl font-black tracking-tight leading-tight mb-4">
                  {selectedCard.title}
                </h3>
                <p className={`text-base sm:text-lg font-medium leading-relaxed ${selectedTone.sub}`}>
                  {selectedCard.body}
                </p>
              </div>

              {/* Footer row with Action CTA */}
              <div className="relative z-10 mt-6 pt-5 border-t border-white/20 flex items-center justify-between">
                <span className="font-mono text-xs font-black tracking-wider opacity-75">
                  ISHA PIPELINE ENGINE
                </span>
                <a
                  href="/fix"
                  onClick={() => sounds.playClick()}
                  className="inline-flex items-center gap-1.5 font-mono text-xs font-black uppercase px-5 py-2.5 rounded-full bg-white text-black hover:bg-neutral-100 transition-all shadow-lg hover:scale-105 active:scale-95"
                >
                  <span>TRY ISHA FIX</span>
                  <ArrowUpRight className="w-4 h-4 stroke-[2.5]" />
                </a>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};

export default PipelinePlanes;
