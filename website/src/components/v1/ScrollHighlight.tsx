"use client";

import React from "react";
import { motion } from "framer-motion";

export type HighlightVariant =
  | "round"
  | "circle"
  | "brush"
  | "underline"
  | "wavy"
  | "double"
  | "box";
export type HighlightColor =
  | "coral"
  | "sun"
  | "sky"
  | "mint"
  | "lilac"
  | "red";

interface ScrollHighlightProps {
  children: React.ReactNode;
  variant?: HighlightVariant;
  color?: HighlightColor;
  className?: string;
  delay?: number;
  strokeWidth?: number;
}

const COLOR_MAP: Record<
  HighlightColor,
  {
    stroke: string;
    bgClass: string;
    textClass: string;
  }
> = {
  coral: {
    stroke: "#FF6B4A",
    bgClass: "bg-rose-100 border-rose-300 dark:bg-rose-950/80 dark:border-rose-500/50",
    textClass: "text-rose-950 dark:text-rose-200",
  },
  red: {
    stroke: "#EF4444",
    bgClass: "bg-red-100 border-red-300 dark:bg-red-950/80 dark:border-red-500/50",
    textClass: "text-red-950 dark:text-red-200",
  },
  sun: {
    stroke: "#FBBF24",
    bgClass: "bg-amber-100 border-amber-300 dark:bg-amber-950/80 dark:border-amber-500/50",
    textClass: "text-amber-950 dark:text-amber-200",
  },
  sky: {
    stroke: "#38BDF8",
    bgClass: "bg-sky-100 border-sky-300 dark:bg-sky-950/80 dark:border-sky-500/50",
    textClass: "text-sky-950 dark:text-sky-200",
  },
  mint: {
    stroke: "#34D399",
    bgClass: "bg-emerald-100 border-emerald-300 dark:bg-emerald-950/80 dark:border-emerald-500/50",
    textClass: "text-emerald-950 dark:text-emerald-200",
  },
  lilac: {
    stroke: "#C084FC",
    bgClass: "bg-purple-100 border-purple-300 dark:bg-purple-950/80 dark:border-purple-500/50",
    textClass: "text-purple-950 dark:text-purple-200",
  },
};

export const ScrollHighlight: React.FC<ScrollHighlightProps> = ({
  children,
  variant = "round",
  color = "coral",
  className = "",
  delay = 0.15,
  strokeWidth = 3,
}) => {
  const selectedColor = COLOR_MAP[color] || COLOR_MAP.coral;

  // 1. ROUND / CIRCLE: Hand-drawn loop oval circling around the text (like "how things work." in jameschugh)
  if (variant === "round" || variant === "circle") {
    return (
      <span
        className={`relative inline-block px-2.5 py-0.5 mx-1 whitespace-nowrap ${className}`}
      >
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="absolute -inset-x-3 -inset-y-2.5 w-[calc(100%+24px)] h-[calc(100%+20px)] pointer-events-none overflow-visible z-10"
        >
          {/* Hand-drawn organic looping oval path */}
          <motion.path
            d="M 12,50 C 12,16 26,5 56,5 C 86,5 98,18 98,48 C 98,78 82,95 48,95 C 16,95 2,78 4,46 C 6,22 24,7 54,6"
            fill="none"
            stroke={selectedColor.stroke}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0, opacity: 0 }}
            whileInView={{ pathLength: 1, opacity: 1 }}
            viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
            transition={{
              duration: 1.15,
              ease: [0.22, 1, 0.36, 1],
              delay,
            }}
          />
        </svg>
        <span className="relative z-0 font-inherit text-neutral-950 dark:text-white font-black">{children}</span>
      </span>
    );
  }

  // 2. BRUSH: Rounded translucent highlighter marker bar
  if (variant === "brush") {
    return (
      <span
        className={`relative inline-block px-3 py-0.5 mx-1 rounded-lg z-0 whitespace-nowrap align-baseline ${className}`}
      >
        <motion.span
          className={`absolute inset-0 -z-10 rounded-lg border shadow-xs ${selectedColor.bgClass}`}
          initial={{ clipPath: "inset(0 100% 0 0)" }}
          whileInView={{ clipPath: "inset(0 0% 0 0)" }}
          viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
          transition={{
            duration: 0.85,
            ease: [0.22, 1, 0.36, 1],
            delay,
          }}
        />
        <span
          className={`relative z-10 font-black tracking-tight transition-colors ${selectedColor.textClass}`}
        >
          {children}
        </span>
      </span>
    );
  }

  // 3. WAVY: Playful wavy underline (like "why people use them." in jameschugh)
  if (variant === "wavy") {
    return (
      <span
        className={`relative inline-block px-1 mx-0.5 whitespace-nowrap ${className}`}
      >
        <svg
          viewBox="0 0 100 20"
          preserveAspectRatio="none"
          className="absolute left-0 -bottom-3 w-full h-4 pointer-events-none overflow-visible z-10"
        >
          <motion.path
            d="M 2,8 Q 14,2 26,8 T 50,8 T 74,8 T 98,8"
            fill="none"
            stroke={selectedColor.stroke}
            strokeWidth={strokeWidth + 0.5}
            strokeLinecap="round"
            initial={{ pathLength: 0, opacity: 0 }}
            whileInView={{ pathLength: 1, opacity: 1 }}
            viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
            transition={{
              duration: 1.0,
              ease: [0.22, 1, 0.36, 1],
              delay,
            }}
          />
        </svg>
        <span className="relative z-0 font-inherit text-neutral-950 dark:text-white font-extrabold">{children}</span>
      </span>
    );
  }

  // 4. DOUBLE: Double hand-drawn underline (like under "ugh" moments in jameschugh)
  if (variant === "double") {
    return (
      <span
        className={`relative inline-block px-1 mx-0.5 whitespace-nowrap ${className}`}
      >
        <svg
          viewBox="0 0 100 24"
          preserveAspectRatio="none"
          className="absolute left-0 -bottom-3.5 w-full h-4 pointer-events-none overflow-visible z-10"
        >
          <motion.path
            d="M 2,6 C 30,3 70,8 98,5"
            fill="none"
            stroke={selectedColor.stroke}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            initial={{ pathLength: 0, opacity: 0 }}
            whileInView={{ pathLength: 1, opacity: 1 }}
            viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
            transition={{
              duration: 0.8,
              ease: [0.22, 1, 0.36, 1],
              delay,
            }}
          />
          <motion.path
            d="M 6,15 C 34,12 68,17 94,14"
            fill="none"
            stroke={selectedColor.stroke}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            initial={{ pathLength: 0, opacity: 0 }}
            whileInView={{ pathLength: 1, opacity: 1 }}
            viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
            transition={{
              duration: 0.85,
              ease: [0.22, 1, 0.36, 1],
              delay: delay + 0.12,
            }}
          />
        </svg>
        <span className="relative z-0 font-inherit text-neutral-950 dark:text-white font-extrabold">{children}</span>
      </span>
    );
  }

  // 5. UNDERLINE: Single organic underline
  if (variant === "underline") {
    return (
      <span
        className={`relative inline-block px-0.5 whitespace-nowrap ${className}`}
      >
        <svg
          viewBox="0 0 100 20"
          preserveAspectRatio="none"
          className="absolute left-0 -bottom-2 w-full h-3 pointer-events-none overflow-visible z-10"
        >
          <motion.path
            d="M 2,10 C 25,16 65,4 98,11"
            fill="none"
            stroke={selectedColor.stroke}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            initial={{ pathLength: 0, opacity: 0 }}
            whileInView={{ pathLength: 1, opacity: 1 }}
            viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
            transition={{
              duration: 0.85,
              ease: [0.22, 1, 0.36, 1],
              delay,
            }}
          />
        </svg>
        <span className="relative z-0 font-inherit text-neutral-950 dark:text-white font-extrabold">{children}</span>
      </span>
    );
  }

  // 6. BOX: Hand-drawn sketched rough rectangle
  return (
    <span
      className={`relative inline-block px-2 py-0.5 mx-0.5 whitespace-nowrap ${className}`}
    >
      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        className="absolute -inset-1 w-[calc(100%+8px)] h-[calc(100%+8px)] pointer-events-none overflow-visible z-10"
      >
        <motion.path
          d="M 6,8 L 94,6 L 96,92 L 4,94 Z"
          fill="none"
          stroke={selectedColor.stroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0, opacity: 0 }}
          whileInView={{ pathLength: 1, opacity: 1 }}
          viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
          transition={{
            duration: 1.0,
            ease: [0.22, 1, 0.36, 1],
            delay,
          }}
        />
      </svg>
      <span className="relative z-0 font-inherit text-neutral-950 dark:text-white font-extrabold">{children}</span>
    </span>
  );
};

export default ScrollHighlight;
