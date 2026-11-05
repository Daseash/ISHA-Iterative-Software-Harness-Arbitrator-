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
  prefix = "WE ENGINEER",
  itemHeight = 72,
  stiffness = 280,
  damping = 30,
  className = "",
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState<number>(0);
  const [sectionHeight, setSectionHeight] = useState<number>(640);
  const [scrollProgress, setScrollProgress] = useState<number>(0);
  const activeIndexRef = useRef<number>(0);

  // Motion value for vertical spring translation centering the active item
  const targetY = useMotionValue((640 / 2 - itemHeight / 2) - 0 * itemHeight);
  const springY = useSpring(targetY, {
    stiffness,
    damping,
    mass: 0.8,
  });

  // Track container height via ResizeObserver for responsive snap boundaries
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const updateHeight = () => {
      const h = el.clientHeight || window.innerHeight || 640;
      setSectionHeight(h);
      const currentProg = scrollRef.current
        ? (scrollRef.current.scrollTop / (h || 640))
        : activeIndexRef.current;
      targetY.set((h / 2 - itemHeight / 2) - currentProg * itemHeight);
    };

    updateHeight();
    const observer = new ResizeObserver(updateHeight);
    observer.observe(el);

    return () => observer.disconnect();
  }, [itemHeight, targetY]);

  // Handle scroll events from the invisible scroll-snap driver
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const top = target.scrollTop;
    const progress = sectionHeight > 0 ? top / sectionHeight : 0;
    setScrollProgress(progress);

    const newIndex = Math.max(0, Math.min(items.length - 1, Math.round(progress)));
    if (newIndex !== activeIndexRef.current) {
      activeIndexRef.current = newIndex;
      setActiveIndex(newIndex);
      sounds.playTick();
    }

    targetY.set((sectionHeight / 2 - itemHeight / 2) - progress * itemHeight);
  };

  // Programmatically jump to a specific index with smooth glide
  const goToIndex = useCallback(
    (index: number) => {
      const bounded = Math.max(0, Math.min(items.length - 1, index));
      if (scrollRef.current) {
        scrollRef.current.scrollTo({
          top: bounded * sectionHeight,
          behavior: "smooth",
        });
      } else {
        setActiveIndex(bounded);
        activeIndexRef.current = bounded;
        setScrollProgress(bounded);
        sounds.playTick();
        targetY.set((sectionHeight / 2 - itemHeight / 2) - bounded * itemHeight);
      }
    },
    [itemHeight, items.length, sectionHeight, targetY]
  );

  return (
    <div
      ref={containerRef}
      className={`relative w-full overflow-hidden select-none flex items-center justify-center bg-[#F9F7EF] dark:bg-black transition-colors ${className}`}
      style={{ minHeight: "560px" }}
    >
      {/* Top and Bottom Viewport Fade Masks: Seamlessly blend into page background */}
      <div className="pointer-events-none absolute top-0 inset-x-0 h-36 bg-gradient-to-b from-[#F9F7EF] dark:from-black via-[#F9F7EF]/80 dark:via-black/80 to-transparent z-30" />
      <div className="pointer-events-none absolute bottom-0 inset-x-0 h-36 bg-gradient-to-t from-[#F9F7EF] dark:from-black via-[#F9F7EF]/80 dark:via-black/80 to-transparent z-30" />

      {/* ================= LAYER 1: INVISIBLE SCROLL DRIVER OVERLAY ================= */}
      {/* Captures scroll/wheel/touch cleanly, overscrolls naturally to page when at ends */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        data-lenis-prevent="true"
        className="absolute inset-0 overflow-y-scroll z-20 pointer-events-auto [scroll-snap-type:y_mandatory] [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden"
      >
        {items.map((_, idx) => (
          <div
            key={idx}
            className="w-full shrink-0 snap-start"
            style={{ height: `${sectionHeight}px` }}
          />
        ))}
      </div>

      {/* ================= LAYER 2: SPRING-ANIMATED VISUAL TRACK ================= */}
      <div className="relative w-full max-w-7xl h-full flex items-center px-4 sm:px-6 md:px-10 lg:px-12 z-10 pointer-events-none">
        <div className="flex flex-col md:flex-row md:items-center gap-2 sm:gap-4 md:gap-6 w-full">
          {/* Static Prefix: Fixed in the vertical center, never repeats on rows */}
          {prefix && (
            <div className="shrink-0 flex items-center">
              <span className="text-xl sm:text-2xl md:text-3xl lg:text-[40px] xl:text-[44px] font-black tracking-tight text-neutral-950 dark:text-neutral-100 uppercase whitespace-nowrap">
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
                const dist = idx - scrollProgress;
                const absDist = Math.abs(dist);
                const isActive = Math.abs(idx - activeIndex) < 0.5;

                // Authentic Unlumen math: distance-based opacity, horizontal indent, and scale
                const opacity = Math.max(0.18, 1 - absDist * 0.44);
                const xOffset = absDist * 10;
                const scale = Math.max(0.92, 1 - absDist * 0.03);

                return (
                  <div
                    key={idx}
                    style={{ height: `${itemHeight}px` }}
                    className="flex items-center text-left w-full py-0 select-none"
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
                      className="flex items-baseline"
                    >
                      <span
                        className={`text-xl sm:text-2xl md:text-3xl lg:text-[40px] xl:text-[44px] font-black tracking-tight leading-none whitespace-nowrap transition-colors duration-200 uppercase ${
                          isActive
                            ? "text-red-600 dark:text-red-500 drop-shadow-sm"
                            : "text-neutral-300 dark:text-neutral-700"
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
      </div>

      {/* Navigation step dots at bottom */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 pointer-events-auto">
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
