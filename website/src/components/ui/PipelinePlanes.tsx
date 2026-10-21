import React, { useState, useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";

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
  stagger?: number;
  className?: string;
}

export const PipelinePlanes: React.FC<PipelinePlanesProps> = ({
  cards = defaultPipelineCards,
  photoWidth = 230,
  photoHeight = 320,
  spread = 115,
  tilt = 10,
  depth = 14,
  stagger = 0.1,
  className = "",
}) => {
  const [hasLanded, setHasLanded] = useState(false);
  const [isFanned, setIsFanned] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, amount: 0.15 });

  // Trigger falling on view/refresh, followed by smooth fanning
  useEffect(() => {
    if (isInView && !hasLanded) {
      setHasLanded(true);
      const fanTimer = setTimeout(() => {
        setIsFanned(true);
      }, (cards.length * stagger + 0.35) * 1000);

      return () => clearTimeout(fanTimer);
    }
  }, [isInView, hasLanded, cards.length, stagger]);

  const centerIndex = (cards.length - 1) / 2;

  return (
    <div
      ref={containerRef}
      className={`relative w-full flex flex-col items-center justify-center py-12 overflow-x-auto sm:overflow-hidden select-none ${className}`}
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

            // Calculate fanned out X offset
            const baseOffset = (i - centerIndex) * spread;

            // When a card is hovered, neighbours shift outwards smoothly to make room
            let hoverShift = 0;
            if (hoveredIndex !== null) {
              if (i < hoveredIndex) {
                hoverShift = -42;
              } else if (i > hoveredIndex) {
                hoverShift = 42;
              }
            }

            const isHovered = hoveredIndex === i;

            // Slanted plane angles matching useplanes 3D effect
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
                  x: 0,
                  y: -380,
                  scale: 1.25,
                  rotateZ: (i % 2 === 0 ? -1 : 1) * (8 + (i * 3) % 7),
                  rotateY: 0,
                  rotateX: 0,
                  opacity: 0,
                }}
                animate={
                  !hasLanded
                    ? {
                        x: 0,
                        y: -380,
                        scale: 1.25,
                        rotateZ: (i % 2 === 0 ? -1 : 1) * (8 + (i * 3) % 7),
                        rotateY: 0,
                        rotateX: 0,
                        opacity: 0,
                      }
                    : !isFanned
                    ? {
                        // Phase 1: Landing onto pile (falling animation)
                        x: (i % 3 - 1) * 5,
                        y: (i - centerIndex) * -3,
                        scale: 1,
                        rotateZ: (i % 2 === 0 ? -1 : 1) * (4 + i * 2),
                        rotateY: 0,
                        rotateX: 0,
                        opacity: 1,
                        transition: {
                          delay: i * stagger,
                          duration: 0.52,
                          ease: [0.22, 1, 0.36, 1],
                        },
                      }
                    : {
                        // Phase 2: Fanned horizontal 3D row
                        x: baseOffset + hoverShift,
                        y: isHovered ? -28 : (i - centerIndex) * depth,
                        scale: isHovered ? 1.15 : 1,
                        rotateZ: isHovered ? 0 : normalRotateZ,
                        rotateY: isHovered ? 0 : normalRotateY,
                        rotateX: isHovered ? 0 : normalRotateX,
                        opacity: 1,
                        transition: {
                          duration: 0.65,
                          ease: [0.25, 1, 0.5, 1],
                        },
                      }
                }
                whileHover={
                  isFanned
                    ? {
                        scale: 1.16,
                        y: -28,
                        rotateZ: 0,
                        rotateY: 0,
                        rotateX: 0,
                        transition: { duration: 0.28, ease: "easeOut" },
                      }
                    : {}
                }
                onMouseEnter={() => isFanned && setHoveredIndex(i)}
                onMouseLeave={() => isFanned && setHoveredIndex(null)}
                onClick={() => {
                  if (isFanned) {
                    setHoveredIndex(hoveredIndex === i ? null : i);
                  }
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

                {/* Bottom: Verbatim Body Text from Image 2 */}
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
      <div className="mt-6 flex items-center justify-center gap-2 text-xs font-mono font-bold text-neutral-500 dark:text-neutral-400">
        <span>hover or tap any plane to focus stage</span>
        <span>↗</span>
      </div>
    </div>
  );
};

export default PipelinePlanes;
