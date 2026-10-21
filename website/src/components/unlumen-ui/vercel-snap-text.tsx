"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import { motion, useSpring, useMotionValue } from "framer-motion";
import { sounds } from "../../utils/sound";

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
  itemHeight = 88,
  stiffness = 280,
  damping = 30,
  className = "",
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState<number>(0);
  const [containerHeight, setContainerHeight] = useState<number>(560);
  const accumulatedDelta = useRef<number>(0);
  const isTransitioning = useRef<boolean>(false);

  // Motion value for vertical spring translation centering the active item
  const targetY = useMotionValue((560 / 2 - itemHeight / 2) - 0 * itemHeight);
  const springY = useSpring(targetY, {
    stiffness,
    damping,
    mass: 0.8,
  });

  // Track container height via ResizeObserver for optical centering
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const updateHeight = () => {
      const h = el.clientHeight || 560;
      setContainerHeight(h);
      targetY.set((h / 2 - itemHeight / 2) - activeIndex * itemHeight);
    };

    updateHeight();
    const observer = new ResizeObserver(updateHeight);
    observer.observe(el);

    return () => observer.disconnect();
  }, [activeIndex, itemHeight, targetY]);

  // Step to a specific index with sound effect and motion spring
  const goToIndex = useCallback(
    (index: number) => {
      const bounded = Math.max(0, Math.min(items.length - 1, index));
      if (bounded === activeIndex) return;

      setActiveIndex(bounded);
      sounds.playTick();
      const centerY = (containerHeight / 2 - itemHeight / 2) - bounded * itemHeight;
      targetY.set(centerY);
    },
    [activeIndex, containerHeight, itemHeight, items.length, targetY]
  );

  // Smooth wheel navigation: accumulates delta and snaps responsively
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const handleWheel = (e: WheelEvent) => {
      const isScrollingDown = e.deltaY > 0;
      const isAtBottom = activeIndex === items.length - 1 && isScrollingDown;
      const isAtTop = activeIndex === 0 && !isScrollingDown;

      // Trap wheel only while cycling through internal items; release at extremes so page can scroll
      if (!isAtBottom && !isAtTop) {
        e.preventDefault();
      }

      if (isTransitioning.current) return;

      accumulatedDelta.current += e.deltaY;

      if (Math.abs(accumulatedDelta.current) >= 38) {
        const dir = accumulatedDelta.current > 0 ? 1 : -1;
        accumulatedDelta.current = 0;
        isTransitioning.current = true;

        goToIndex(activeIndex + dir);

        setTimeout(() => {
          isTransitioning.current = false;
        }, 160);
      }
    };

    el.addEventListener("wheel", handleWheel, { passive: false });
    return () => el.removeEventListener("wheel", handleWheel);
  }, [activeIndex, goToIndex, items.length]);

  // Touch swipe support for mobile
  const touchStartY = useRef<number>(0);
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartY.current = e.touches[0].clientY;
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    const touchEndY = e.changedTouches[0].clientY;
    const diff = touchStartY.current - touchEndY;
    if (Math.abs(diff) > 35) {
      const dir = diff > 0 ? 1 : -1;
      goToIndex(activeIndex + dir);
    }
  };

  return (
    <div
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      className={`relative w-full overflow-hidden select-none flex items-center justify-center ${className}`}
      style={{ minHeight: "500px" }}
    >
      {/* Background radial glow */}
      <div className="absolute inset-0 bg-radial from-red-600/5 via-transparent to-transparent pointer-events-none" />

      {/* Main Container: Single static prefix on left + spring-animated scrolling list on right */}
      <div className="relative w-full max-w-6xl h-full flex items-center px-4 sm:px-8 md:px-12 z-10">
        <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-5 w-full">
          {/* Static Prefix: Fixed in the vertical center, never repeats on rows */}
          {prefix && (
            <div className="shrink-0 flex items-center">
              <span className="text-3xl sm:text-5xl md:text-6xl lg:text-7xl font-black tracking-tight text-red-600 dark:text-red-500 whitespace-nowrap">
                {prefix}
              </span>
            </div>
          )}

          {/* Spring-animated items track */}
          <div className="relative flex-1 h-full overflow-visible">
            <motion.div
              style={{ y: springY }}
              className="flex flex-col items-start w-full"
            >
              {items.map((item, idx) => {
                const dist = idx - activeIndex;
                const absDist = Math.abs(dist);
                const isActive = idx === activeIndex;

                const opacity = Math.max(0.18, 1 - absDist * 0.44);
                const xOffset = absDist * 20;
                const scale = Math.max(0.9, 1 - absDist * 0.04);

                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => goToIndex(idx)}
                    style={{ height: `${itemHeight}px` }}
                    className="flex items-center text-left focus:outline-none cursor-pointer w-full group py-0"
                  >
                    <motion.div
                      animate={{
                        x: xOffset,
                        scale,
                        opacity,
                      }}
                      transition={{
                        type: "spring",
                        stiffness: stiffness * 1.1,
                        damping: damping * 1.1,
                      }}
                      className="flex items-baseline gap-3"
                    >
                      <span
                        className={`text-3xl sm:text-5xl md:text-6xl lg:text-7xl font-black tracking-tight leading-none whitespace-nowrap transition-colors duration-200 ${
                          isActive
                            ? "text-neutral-950 dark:text-[#F9F7EF] drop-shadow-sm"
                            : "text-neutral-400 dark:text-neutral-600 group-hover:text-neutral-700 dark:group-hover:text-neutral-300"
                        }`}
                      >
                        {item}
                      </span>
                    </motion.div>
                  </button>
                );
              })}
            </motion.div>
          </div>
        </div>
      </div>

      {/* Navigation step dots at bottom */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2">
        {items.map((_, i) => (
          <button
            key={i}
            type="button"
            onClick={() => goToIndex(i)}
            className={`transition-all duration-300 rounded-full cursor-pointer ${
              i === activeIndex
                ? "w-8 h-2 bg-red-600"
                : "w-2 h-2 bg-neutral-300 dark:bg-neutral-700 hover:bg-neutral-500"
            }`}
            aria-label={`Go to item ${i + 1}`}
          />
        ))}
        <span className="ml-3 font-mono text-[11px] font-black text-neutral-400 dark:text-neutral-500">
          0{activeIndex + 1} / 0{items.length}
        </span>
      </div>
    </div>
  );
};

export default VercelSnapText;
