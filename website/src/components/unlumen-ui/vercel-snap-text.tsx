"use client";

import React, { useRef, useState, useEffect } from "react";
import { motion, useSpring, useMotionValue } from "framer-motion";

export interface VercelSnapTextProps {
  items: string[];
  prefix?: string;
  itemHeight?: number;
  stiffness?: number;
  damping?: number;
  className?: string;
}

export const VercelSnapText: React.FC<VercelSnapTextProps> = ({
  items,
  prefix = "",
  itemHeight = 96,
  stiffness = 200,
  damping = 28,
  className = "",
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [sectionHeight, setSectionHeight] = useState<number>(600);
  const [scrollProgress, setScrollProgress] = useState<number>(0);

  // Motion value for vertical spring translation
  const targetY = useMotionValue(0);
  const springY = useSpring(targetY, {
    stiffness,
    damping,
    mass: 0.8,
  });

  // Track container height via ResizeObserver for responsive section snap boundaries
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const updateHeight = () => {
      const h = el.clientHeight || window.innerHeight;
      setSectionHeight(h);
    };

    updateHeight();
    const observer = new ResizeObserver(updateHeight);
    observer.observe(el);

    return () => observer.disconnect();
  }, []);

  // Handle scroll events from the invisible scroll-snap overlay
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const top = target.scrollTop;
    const progress = sectionHeight > 0 ? top / sectionHeight : 0;
    setScrollProgress(progress);
    targetY.set(-progress * itemHeight);
  };

  const activeIndex = Math.round(scrollProgress);

  return (
    <div
      ref={containerRef}
      className={`relative w-full overflow-hidden select-none ${className}`}
      style={{ minHeight: "500px" }}
    >
      {/* ================= LAYER 1: INVISIBLE SCROLL DRIVER OVERLAY ================= */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="absolute inset-0 overflow-y-scroll z-20 pointer-events-auto [scroll-snap-type:y_mandatory] [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden"
      >
        {items.map((_, idx) => (
          <div
            key={idx}
            className="w-full shrink-0 snap-start"
            style={{ height: sectionHeight }}
          />
        ))}
      </div>

      {/* ================= LAYER 2: SPRING-ANIMATED VISUAL TRACK ================= */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10 px-4 sm:px-8">
        <div className="relative w-full max-w-5xl flex items-center justify-start overflow-visible">
          {/* Spring-animated column of items */}
          <motion.div
            style={{ y: springY }}
            className="flex flex-col items-start justify-center w-full"
          >
            {items.map((item, idx) => {
              const dist = idx - scrollProgress;
              const absDist = Math.abs(dist);
              const isActive = Math.abs(idx - activeIndex) < 0.5;

              // Calculate distance-based opacity, horizontal indent, and scale
              const opacity = Math.max(0.16, 1 - absDist * 0.52);
              const xOffset = absDist * 28;
              const scale = Math.max(0.88, 1 - absDist * 0.05);

              return (
                <div
                  key={idx}
                  style={{
                    height: `${itemHeight}px`,
                  }}
                  className="w-full flex items-center"
                >
                  <motion.div
                    animate={{
                      x: xOffset,
                      scale: scale,
                      opacity: opacity,
                    }}
                    transition={{
                      type: "spring",
                      stiffness: stiffness * 1.2,
                      damping: damping * 1.1,
                    }}
                    className="flex flex-wrap items-baseline gap-x-3 sm:gap-x-4 text-left transition-colors"
                  >
                    {/* Prefix only displayed on the active or closest item */}
                    {prefix && (
                      <span
                        className={`text-3xl sm:text-5xl md:text-6xl lg:text-7xl font-black tracking-tight transition-all duration-200 ${
                          isActive
                            ? "text-red-600 dark:text-red-500 opacity-100"
                            : "text-neutral-400/40 dark:text-neutral-600/40"
                        }`}
                      >
                        {prefix}
                      </span>
                    )}

                    {/* The snapping text item */}
                    <span
                      className={`text-3xl sm:text-5xl md:text-6xl lg:text-7xl font-black tracking-tight transition-all duration-200 ${
                        isActive
                          ? "text-neutral-950 dark:text-[#F9F7EF] opacity-100"
                          : "text-neutral-400/50 dark:text-neutral-500/50"
                      }`}
                    >
                      {item}
                    </span>
                  </motion.div>
                </div>
              );
            })}
          </motion.div>
        </div>
      </div>

      {/* Subtle Scroll Hint Indicator at bottom */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10 pointer-events-none flex items-center gap-2 font-mono text-[11px] font-bold tracking-widest uppercase text-neutral-400 dark:text-neutral-500">
        <span>scroll to explore</span>
        <span className="animate-bounce">↓</span>
      </div>
    </div>
  );
};

export default VercelSnapText;
