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
  { stroke: string; bg: string; darkBg: string }
> = {
  coral: { stroke: "#FF6B4A", bg: "#FFE8E2", darkBg: "rgba(255, 107, 74, 0.25)" },
  red: { stroke: "#DC2626", bg: "#FEE2E2", darkBg: "rgba(220, 38, 38, 0.25)" },
  sun: { stroke: "#FFD23F", bg: "#FFF4CC", darkBg: "rgba(255, 210, 63, 0.25)" },
  sky: { stroke: "#2F7FD8", bg: "#E2F0FD", darkBg: "rgba(47, 127, 216, 0.3)" },
  mint: { stroke: "#4F9E4A", bg: "#E3F4E2", darkBg: "rgba(79, 158, 74, 0.25)" },
  lilac: { stroke: "#B7A2FF", bg: "#F0EBFF", darkBg: "rgba(183, 162, 255, 0.25)" },
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
        <span className="relative z-0 font-inherit">{children}</span>
      </span>
    );
  }

  // 2. BRUSH: Rounded translucent highlighter marker bar (like "mechanical engineer" in jameschugh)
  if (variant === "brush") {
    return (
      <span
        className={`relative inline-block px-3 py-1 mx-1 rounded-xl z-0 whitespace-nowrap ${className}`}
      >
        <motion.span
          className="absolute inset-0 -z-10 rounded-xl"
          style={{
            backgroundColor: selectedColor.bg,
          }}
          initial={{ clipPath: "inset(0 100% 0 0)" }}
          whileInView={{ clipPath: "inset(0 0% 0 0)" }}
          viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
          transition={{
            duration: 0.85,
            ease: [0.22, 1, 0.36, 1],
            delay,
          }}
        />
        {/* Dark mode overlay */}
        <motion.span
          className="absolute inset-0 -z-10 rounded-xl hidden dark:block"
          style={{
            backgroundColor: selectedColor.darkBg,
          }}
          initial={{ clipPath: "inset(0 100% 0 0)" }}
          whileInView={{ clipPath: "inset(0 0% 0 0)" }}
          viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
          transition={{
            duration: 0.85,
            ease: [0.22, 1, 0.36, 1],
            delay,
          }}
        />
        <span className="relative z-0 font-inherit">{children}</span>
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
        <span className="relative z-0 font-inherit">{children}</span>
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
        <span className="relative z-0 font-inherit">{children}</span>
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
        <span className="relative z-0 font-inherit">{children}</span>
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
      <span className="relative z-0 font-inherit">{children}</span>
    </span>
  );
};

export default ScrollHighlight;
