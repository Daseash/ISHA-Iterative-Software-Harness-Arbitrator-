import React, { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "../../lib/utils";

export interface HoverExpandImage {
  src: string;
  alt: string;
  code: string;
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
  expandedWidth = "clamp(14rem, 36vw, 26rem)",
  collapsedWidth = "clamp(1.8rem, 4.5vw, 3.5rem)",
  defaultWidth = "clamp(3rem, 8.5vw, 6.5rem)",
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
                      className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent z-10 pointer-events-none"
                    />
                  )}
                </AnimatePresence>

                {/* Number & description tag */}
                <AnimatePresence>
                  {isActive && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 5 }}
                      transition={{ duration: 0.4, delay: 0.1 }}
                      className="absolute inset-x-0 bottom-0 flex flex-col justify-end p-3 sm:p-4 z-20 pointer-events-none"
                    >
                      <span className="font-mono text-[10px] sm:text-xs font-bold tracking-widest text-red-500">
                        {image.code}
                      </span>
                      <p className="text-white font-black text-[11px] sm:text-xs tracking-wide line-clamp-1 uppercase mt-0.5">
                        {image.alt}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Subtle dimming on inactive cards when another card is active */}
                <div
                  className={cn(
                    "absolute inset-0 transition-opacity duration-300 pointer-events-none z-[5]",
                    isAnyActive && !isActive ? "opacity-40 bg-black" : "opacity-0"
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
  const images = [
    {
      src: "/eyes.jpg",
      alt: "Neural Repo Ingestion",
      code: "# 01",
    },
    {
      src: "/eyes.jpg",
      alt: "AST Structural Mapping",
      code: "# 02",
    },
    {
      src: "/eyes.jpg",
      alt: "TDD Test Synthesis",
      code: "# 03",
    },
    {
      src: "/eyes.jpg",
      alt: "3-Worktree Parallel Tournament",
      code: "# 04",
    },
    {
      src: "/eyes.jpg",
      alt: "State Arbitrator",
      code: "# 05",
    },
    {
      src: "/eyes.jpg",
      alt: "LAYA Calibrated Decision",
      code: "# 06",
    },
    {
      src: "/eyes.jpg",
      alt: "Closed-Loop Self-Healing",
      code: "# 07",
    },
  ];

  return (
    <div className="flex h-full w-full items-center justify-center overflow-hidden bg-[#F9F7EF] dark:bg-black transition-colors duration-300 py-8">
      <HoverExpand_001 images={images} />
    </div>
  );
};

export default Skiper52;
