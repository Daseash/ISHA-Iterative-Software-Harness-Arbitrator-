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
  defaultActive?: number;
}

export const HoverExpand_001: React.FC<HoverExpandProps> = ({
  images,
  className,
  defaultActive = 2,
}) => {
  const [activeImage, setActiveImage] = useState<number | null>(defaultActive);

  return (
    <motion.div
      initial={{ opacity: 0, translateY: 20 }}
      animate={{ opacity: 1, translateY: 0 }}
      transition={{
        duration: 0.5,
        delay: 0.2,
      }}
      className={cn("relative w-full max-w-6xl mx-auto px-4 sm:px-6 flex justify-center items-center", className)}
    >
      <div className="w-full flex items-center justify-center">
        <div className="flex w-full items-center justify-center gap-1.5 sm:gap-2.5 md:gap-3.5">
          {images.map((image, index) => {
            const isActive = activeImage === index;
            return (
              <motion.div
                key={index}
                className="relative cursor-pointer overflow-hidden rounded-2xl sm:rounded-3xl shadow-2xl shadow-neutral-900/15 dark:shadow-black/80 bg-neutral-200 dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-800/80 group shrink-0 transition-colors"
                initial={false}
                animate={{
                  width: isActive
                    ? "clamp(14rem, 42vw, 32rem)"
                    : "clamp(3rem, 10vw, 6.5rem)",
                  height: isActive
                    ? "clamp(18rem, 55vh, 32rem)"
                    : "clamp(18rem, 55vh, 32rem)",
                }}
                transition={{ duration: 0.35, ease: [0.25, 1, 0.5, 1] }}
                onClick={() => setActiveImage(index)}
                onHoverStart={() => setActiveImage(index)}
              >
                {/* Gradient vignette on active & hover */}
                <AnimatePresence>
                  {isActive && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent z-10 pointer-events-none"
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
                      transition={{ duration: 0.25 }}
                      className="absolute inset-x-0 bottom-0 flex flex-col justify-end p-4 sm:p-6 z-20 pointer-events-none"
                    >
                      <span className="font-mono text-xs sm:text-sm font-bold tracking-widest text-red-500">
                        {image.code}
                      </span>
                      <p className="text-white font-black text-xs sm:text-sm tracking-wide line-clamp-1 uppercase mt-0.5">
                        {image.alt}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Subtle inactive overlay so active pops out */}
                <div
                  className={cn(
                    "absolute inset-0 transition-opacity duration-300 pointer-events-none z-[5]",
                    isActive ? "opacity-0" : "opacity-35 bg-black"
                  )}
                />

                <img
                  src={image.src}
                  className="w-full h-full object-cover object-center filter brightness-95 contrast-110 select-none pointer-events-none transition-transform duration-500 group-hover:scale-105"
                  alt={image.alt}
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
      alt: "Autonomous Ingestion",
      code: "# 01",
    },
    {
      src: "/eyes.jpg",
      alt: "AST Structural Mapping",
      code: "# 02",
    },
    {
      src: "/eyes.jpg",
      alt: "Git Worktree Tournament",
      code: "# 03",
    },
    {
      src: "/eyes.jpg",
      alt: "LAYA Calibrated Decision",
      code: "# 04",
    },
    {
      src: "/eyes.jpg",
      alt: "Closed-Loop Self-Healing",
      code: "# 05",
    },
  ];

  return (
    <div className="flex h-full w-full items-center justify-center overflow-hidden bg-[#F9F7EF] dark:bg-black transition-colors duration-300 py-8">
      <HoverExpand_001 images={images} />
    </div>
  );
};

export default Skiper52;
