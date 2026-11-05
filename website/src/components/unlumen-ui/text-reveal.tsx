"use client";

import * as React from "react";
import { motion, useInView } from "framer-motion";
import { cn } from "../../lib/utils";

export interface TextRevealProps {
  /** The text to animate. */
  text: string;
  /**
   * HTML tag for the container element.
   * @default "p"
   */
  as?: keyof React.JSX.IntrinsicElements;
  /**
   * Split mode: word-by-word or character-by-character.
   * @default "words"
   */
  splitBy?: "words" | "characters";
  /**
   * Delay between each word/character animation in seconds.
   * @default 0.05
   */
  staggerDelay?: number;
  /**
   * Duration of each unit's animation in seconds.
   * @default 0.5
   */
  duration?: number;
  /**
   * Trigger the animation only once.
   * @default true
   */
  once?: boolean;
  /**
   * Viewport threshold amount where reveal triggers (0-1).
   * @default 0.85
   */
  threshold?: number;
  className?: string;
}

export function TextReveal({
  text,
  as: Tag = "p",
  splitBy = "words",
  staggerDelay = 0.05,
  duration = 0.5,
  once = true,
  threshold,
  className,
}: TextRevealProps) {
  const ref = React.useRef<HTMLElement>(null);
  const isInView = useInView(ref, {
    once,
    amount: threshold !== undefined ? threshold : 0.2,
    margin: "0px 0px -10% 0px",
  });

  const units =
    splitBy === "words"
      ? text
          .split(/\s+/)
          .map((w, i, arr) => (i < arr.length - 1 ? w + "\u00A0" : w))
      : text.split("");

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const AnyTag = Tag as any;

  return (
    <AnyTag
      ref={ref}
      className={cn("leading-relaxed", className)}
      aria-label={text}
    >
      {units.map((unit, i) => (
        <motion.span
          key={i}
          initial={{ opacity: 0.1, filter: "blur(8px)" }}
          animate={
            isInView
              ? { opacity: 1, filter: "blur(0px)" }
              : { opacity: 0.1, filter: "blur(8px)" }
          }
          transition={{
            duration,
            delay: i * staggerDelay,
            ease: "easeOut",
          }}
          style={{ display: "inline-block" }}
          className="will-change-[opacity,filter]"
        >
          {unit}
        </motion.span>
      ))}
    </AnyTag>
  );
}

export default TextReveal;
