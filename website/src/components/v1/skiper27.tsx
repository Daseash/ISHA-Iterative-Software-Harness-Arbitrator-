"use client";

import React from "react";
import { motion } from "framer-motion";

export interface RollingTextProps {
  text: string;
  speed?: number;
  duration?: number;
  className?: string;
  repeat?: boolean;
  repeatDelay?: number;
}

/**
 * Authentic Skiper27 Rolling Text (Slot-machine character reel)
 * Inspiring from skiper-ui.com/v1/skiper27
 */
export const RollingText: React.FC<RollingTextProps> = ({
  text = "ROLLING",
  speed = 0.05,
  duration = 4,
  className = "text-5xl sm:text-7xl lg:text-8xl font-bold",
  repeat = true,
  repeatDelay = 2.2,
}) => {
  const l = Math.floor(text.length / 2);

  return (
    <div className={`flex flex-wrap items-center justify-center select-none ${className}`}>
      {text.split("").map((char, index) => {
        if (char === " ") {
          return (
            <span key={index} className="inline-block w-[0.28em]">
              &nbsp;
            </span>
          );
        }

        // Authentic skiper27 math: distance from center drives delay & reel iterations
        const i = Math.abs(index - l);
        const o = Math.max(3, Math.floor(duration / (0.2 + 0.15 * i)));

        return (
          <div
            key={index}
            className="relative inline-block overflow-hidden"
            style={{ height: "1em" }}
          >
            <motion.h1
              className="flex flex-col m-0 p-0 leading-none"
              whileInView={{ y: `-${1.2 * o}em` }}
              viewport={{ once: false, amount: 0.1 }}
              transition={{
                duration,
                ease: [0.15, 1, 0.1, 1],
                delay: i * speed,
                repeat: repeat ? Infinity : 0,
                repeatDelay,
              }}
            >
              {Array(o + 2)
                .fill(null)
                .map((_, r) => (
                  <span
                    key={r}
                    className="flex shrink-0 items-center justify-center leading-none"
                    style={{ height: "1.2em" }}
                  >
                    {char}
                  </span>
                ))}
            </motion.h1>
          </div>
        );
      })}
    </div>
  );
};

export default RollingText;
