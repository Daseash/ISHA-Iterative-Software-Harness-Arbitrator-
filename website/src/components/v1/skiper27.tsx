import React, { useRef } from "react";
import { motion, useInView } from "framer-motion";

interface RollingTextProps {
  text: string;
  speed?: number;
  duration?: number;
  className?: string;
  repeatDelay?: number;
}

export const RollingText: React.FC<RollingTextProps> = ({
  text,
  speed = 0.05,
  duration = 3.5,
  className = "",
  repeatDelay = 1.5,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: false, amount: 0.2 });

  const characters = Array.from(text);
  const centerIndex = (characters.length - 1) / 2;

  return (
    <div
      ref={containerRef}
      className={`inline-flex flex-wrap items-center justify-center select-none leading-none ${className}`}
    >
      {characters.map((char, index) => {
        // Calculate staggered timing and delay from center outward to edges
        const distanceFromCenter = Math.abs(index - centerIndex);
        const staggerDelay = distanceFromCenter * speed;

        if (char === " ") {
          return (
            <span key={index} className="inline-block w-[0.3em]">
              &nbsp;
            </span>
          );
        }

        return (
          <span
            key={index}
            className="relative inline-flex h-[1.15em] items-center justify-center overflow-hidden leading-none align-middle font-black"
          >
            {/* Primary letter: sits at 0%, rolls up to -140%, then returns */}
            <motion.span
              animate={
                isInView
                  ? {
                      y: ["0%", "-140%", "-140%", "0%"],
                    }
                  : { y: "0%" }
              }
              transition={{
                duration,
                times: [0, 0.35, 0.65, 1],
                repeat: Infinity,
                repeatDelay,
                delay: staggerDelay,
                ease: [0.76, 0, 0.24, 1] as const,
              }}
              className="inline-block font-black"
            >
              {char}
            </motion.span>

            {/* Secondary clone letter: rolls in from 140% to 0%, rests, then rolls back */}
            <motion.span
              aria-hidden="true"
              animate={
                isInView
                  ? {
                      y: ["140%", "0%", "0%", "140%"],
                    }
                  : { y: "140%" }
              }
              transition={{
                duration,
                times: [0, 0.35, 0.65, 1],
                repeat: Infinity,
                repeatDelay,
                delay: staggerDelay,
                ease: [0.76, 0, 0.24, 1] as const,
              }}
              className="absolute inline-block font-black"
            >
              {char}
            </motion.span>
          </span>
        );
      })}
    </div>
  );
};

export default RollingText;
