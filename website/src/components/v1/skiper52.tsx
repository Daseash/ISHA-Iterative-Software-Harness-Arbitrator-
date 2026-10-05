import React, { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "../../lib/utils";

export interface HoverExpandImage {
  src: string;
  alt: string;
  code: string;
  stat?: string;
  detail?: string;
}

export interface HoverExpandProps {
  images: HoverExpandImage[];
  className?: string;
  defaultActive?: number | null;
  height?: string;
  expandedWidth?: string;
  collapsedWidth?: string;
  defaultWidth?: string;
}

export const HoverExpand_001: React.FC<HoverExpandProps> = ({
  images,
  className,
  defaultActive = null,
  height = "clamp(18rem, 55vh, 32rem)",
  expandedWidth = "clamp(15rem, 36vw, 24rem)",
  collapsedWidth = "clamp(1.6rem, 4vw, 3rem)",
  defaultWidth = "clamp(2.8rem, 8vw, 6.2rem)",
}) => {
  const [activeImage, setActiveImage] = useState<number | null>(defaultActive);
  const totalCards = images.length;

  return (
    <motion.div
      initial={{ opacity: 0, translateY: 15 }}
      animate={{ opacity: 1, translateY: 0 }}
      transition={{
        duration: 0.5,
        delay: 0.2,
      }}
      className={cn("relative w-full mx-auto px-1 sm:px-2 flex justify-center items-center overflow-hidden", className)}
      onMouseLeave={() => setActiveImage(null)}
    >
      <div className="w-full flex items-center justify-center">
        <div className="flex w-full items-center justify-center gap-1 sm:gap-1.5 md:gap-2">
          {images.map((image, index) => {
            const isActive = activeImage === index;
            const isAnyActive = activeImage !== null;

            return (
              <motion.div
                key={index}
                className="relative cursor-pointer overflow-hidden rounded-xl sm:rounded-2xl shadow-xl shadow-neutral-900/15 dark:shadow-black/80 bg-neutral-200 dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-800/80 group shrink-0 transition-colors"
                initial={false}
                animate={{
                  width: !isAnyActive
                    ? defaultWidth
                    : isActive
                    ? expandedWidth
                    : collapsedWidth,
                  height: height,
                }}
                transition={{ duration: 0.75, ease: [0.16, 1, 0.3, 1] }}
                onClick={() => setActiveImage(isActive ? null : index)}
                onHoverStart={() => setActiveImage(index)}
              >
                {/* Gradient vignette on active card */}
                <AnimatePresence>
                  {isActive && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.35 }}
                      className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/45 to-transparent z-10 pointer-events-none"
                    />
                  )}
                </AnimatePresence>

                {/* Number, Stat Badge, & description tag */}
                <AnimatePresence>
                  {isActive && (
                    <motion.div
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 8 }}
                      transition={{ duration: 0.4, delay: 0.08 }}
                      className="absolute inset-x-0 bottom-0 flex flex-col justify-end p-3.5 sm:p-5 z-20 pointer-events-none space-y-1.5"
                    >
                      <div className="flex items-center justify-between gap-1">
                        <span className="font-mono text-[10px] sm:text-xs font-black tracking-widest text-red-500 uppercase">
                          {image.code}
                        </span>
                        {image.stat && (
                          <span className="px-2 py-0.5 rounded-full bg-red-600 text-white font-mono text-[9px] sm:text-[10px] font-black uppercase tracking-wider shadow-sm">
                            {image.stat}
                          </span>
                        )}
                      </div>

                      <p className="text-white font-black text-xs sm:text-sm tracking-wide uppercase leading-tight [text-shadow:_0_2px_8px_rgba(0,0,0,0.8)]">
                        {image.alt}
                      </p>

                      {image.detail && (
                        <p className="text-neutral-300 font-mono text-[10px] sm:text-[11px] leading-tight font-bold line-clamp-2 pt-0.5">
                          {image.detail}
                        </p>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Subtle dimming on inactive cards when another card is active */}
                <div
                  className={cn(
                    "absolute inset-0 transition-opacity duration-300 pointer-events-none z-[5]",
                    isAnyActive && !isActive ? "opacity-45 bg-black" : "opacity-0"
                  )}
                />

                {/* Sliced mosaic image: each card displays its 1/Nth horizontal slice */}
                <motion.img
                  src={image.src}
                  alt={image.alt}
                  initial={false}
                  animate={{
                    width: isActive ? "100%" : `${totalCards * 100}%`,
                    left: isActive ? "0%" : `-${index * 100}%`,
                  }}
                  transition={{ duration: 0.75, ease: [0.16, 1, 0.3, 1] }}
                  className="absolute inset-y-0 h-full max-w-none object-cover object-center filter brightness-95 contrast-110 select-none pointer-events-none"
                />
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
};

export const Skiper52: React.FC = () => {
  const images: HoverExpandImage[] = [
    {
      src: "/eyes.jpg",
      code: "# 01 · LOCALIZATION",
      alt: "BM25 + AST Symbol Targeting",
      stat: "66.7% HIT@8",
      detail: "MRR 0.535 lexical retrieval & AST function ranking without repo bloat",
    },
    {
      src: "/eyes.jpg",
      code: "# 02 · TDD SYNTHESIS",
      alt: "Red-to-Green Repro Test",
      stat: "100% REPRO",
      detail: "Synthesizes isolated test that must fail on unfixed code first",
    },
    {
      src: "/eyes.jpg",
      code: "# 03 · TOURNAMENT",
      alt: "3-Worktree Parallel Race",
      stat: "0 POLLUTION",
      detail: "Races Direct, Defensive, and Alternative fixes in isolated sandboxes",
    },
    {
      src: "/eyes.jpg",
      code: "# 04 · ARBITRATION",
      alt: "Minimal Churn Arbitrator",
      stat: "0.0% AST ERRORS",
      detail: "Selects cleanest syntax-validated patch turning reproduction green",
    },
    {
      src: "/eyes.jpg",
      code: "# 05 · PATCH ENGINE",
      alt: "Atomic Git Patch Apply",
      stat: "0/30 FAILURES",
      detail: "Cross-platform LF normalization & fuzzy context recovery",
    },
    {
      src: "/eyes.jpg",
      code: "# 06 · LAYA CALIBRATION",
      alt: "Calibrated Decision Gate",
      stat: "ECE = 0.0010",
      detail: "Temperature-scaled T=0.35 gate with 100% auto-approve precision",
    },
    {
      src: "/eyes.jpg",
      code: "# 07 · INFERENCE",
      alt: "Zero-Cost Model Cascade",
      stat: "$0.00 BUDGET",
      detail: "Groq LPU + Gemini 3.8 Flash sub-second reasoning chain",
    },
  ];

  return (
    <div className="flex h-full w-full items-center justify-center overflow-hidden bg-[#F9F7EF] dark:bg-black transition-colors duration-300 py-8">
      <HoverExpand_001 images={images} />
    </div>
  );
};

export default Skiper52;
