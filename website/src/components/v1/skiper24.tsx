"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { sounds } from "../../utils/sound";

export interface Project {
  id: number | string;
  name: string;
  description: string;
  badge: string;
  bgColor: string;
  image: string;
  date?: string;
  metric?: string;
  auditProof?: string;
}

export interface TikTikColorListProps {
  projects: Project[];
  className?: string;
  showPreview?: boolean;
  previewSize?: "sm" | "md" | "lg";
  enableSound?: boolean;
  infiniteScroll?: boolean;
  scrollThreshold?: number;
}

export const TikTikColorList: React.FC<TikTikColorListProps> = ({
  projects,
  className = "",
  showPreview = true,
  previewSize = "lg",
  enableSound = true,
  infiniteScroll = true,
  scrollThreshold = 45,
}) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const accumulatedDeltaRef = useRef(0);
  const isTransitioningRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const activeProject = projects[activeIndex] || projects[0];

  // Play official skiper24 tick.wav on project change
  const handleIndexChange = useCallback(
    (newIndex: number) => {
      if (newIndex === activeIndex) return;
      setActiveIndex(newIndex);
      if (enableSound) {
        sounds.playTick();
      }
    },
    [activeIndex, enableSound]
  );

  // Wheel listener with smooth threshold accumulation
  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && target.closest(".no-wheel-hijack")) return;

      e.preventDefault();

      if (isTransitioningRef.current) return;

      accumulatedDeltaRef.current += e.deltaY;

      if (Math.abs(accumulatedDeltaRef.current) >= scrollThreshold) {
        const direction = accumulatedDeltaRef.current > 0 ? 1 : -1;
        accumulatedDeltaRef.current = 0;
        isTransitioningRef.current = true;

        let nextIndex: number;
        if (infiniteScroll) {
          nextIndex = (activeIndex + direction + projects.length) % projects.length;
        } else {
          nextIndex = Math.max(0, Math.min(projects.length - 1, activeIndex + direction));
        }

        handleIndexChange(nextIndex);

        setTimeout(() => {
          isTransitioningRef.current = false;
        }, 180);
      }
    };

    const container = containerRef.current;
    if (container) {
      container.addEventListener("wheel", handleWheel, { passive: false });
    }

    return () => {
      if (container) {
        container.removeEventListener("wheel", handleWheel);
      }
    };
  }, [activeIndex, infiniteScroll, projects.length, scrollThreshold, handleIndexChange]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowDown" || e.key === "PageDown") {
        e.preventDefault();
        const next = infiniteScroll
          ? (activeIndex + 1) % projects.length
          : Math.min(projects.length - 1, activeIndex + 1);
        handleIndexChange(next);
      } else if (e.key === "ArrowUp" || e.key === "PageUp") {
        e.preventDefault();
        const prev = infiniteScroll
          ? (activeIndex - 1 + projects.length) % projects.length
          : Math.max(0, activeIndex - 1);
        handleIndexChange(prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeIndex, infiniteScroll, projects.length, handleIndexChange]);

  // Touch swipe support for mobile devices
  const touchStartYRef = useRef(0);
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartYRef.current = e.touches[0].clientY;
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    const touchEndY = e.changedTouches[0].clientY;
    const diff = touchStartYRef.current - touchEndY;
    if (Math.abs(diff) > 40) {
      const direction = diff > 0 ? 1 : -1;
      const next = infiniteScroll
        ? (activeIndex + direction + projects.length) % projects.length
        : Math.max(0, Math.min(projects.length - 1, activeIndex + direction));
      handleIndexChange(next);
    }
  };

  // Preview card sizing: noticeably smaller and more compact
  const previewSizeClasses = {
    sm: "w-[240px] h-[240px]",
    md: "w-[280px] h-[280px]",
    lg: "w-[270px] h-[270px] sm:w-[300px] sm:h-[300px] md:w-[330px] md:h-[330px]",
  }[previewSize];

  return (
    <div
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      style={{
        backgroundColor: activeProject.bgColor,
        transition: "background-color 0.75s cubic-bezier(0.16, 1, 0.3, 1)",
      }}
      className={`relative w-full h-screen overflow-hidden select-none flex items-center transition-colors duration-700 ${className}`}
    >
      {/* ================= MAIN VERTICAL TYPOGRAPHIC SCROLL LIST ================= */}
      <div className="relative w-full h-full flex items-center px-6 sm:px-12 md:px-16 lg:px-20 z-20">
        <div className="w-full max-w-xl sm:max-w-2xl md:max-w-3xl lg:max-w-4xl relative">
          {/* Spring-animated list container kept centered */}
          <motion.div
            animate={{
              y: -activeIndex * 96,
            }}
            transition={{
              type: "spring",
              stiffness: 320,
              damping: 34,
              mass: 0.8,
            }}
            className="flex flex-col gap-4 py-[35vh]"
          >
            {projects.map((project, idx) => {
              const isActive = idx === activeIndex;

              return (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => handleIndexChange(idx)}
                  className={`group text-left transition-all duration-300 focus:outline-none flex flex-wrap items-center gap-4 sm:gap-6 py-2 cursor-pointer ${
                    isActive
                      ? "opacity-100 scale-100"
                      : "opacity-20 hover:opacity-80 scale-[0.98]"
                  }`}
                >
                  {/* Big Typographic Title */}
                  <span className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-none text-black transition-colors duration-300">
                    {project.name}
                  </span>

                  {/* Category Badge Pill */}
                  <span className="inline-flex items-center rounded-full bg-white/20 px-4 py-1.5 text-xs sm:text-sm font-medium backdrop-blur-sm text-black border border-black/5 transition-all duration-300">
                    {project.badge}
                  </span>

                  {/* Date or Key Metric Badge */}
                  {(project.date || project.metric) && (
                    <span className="hidden md:inline-block text-xs sm:text-sm font-normal text-black/50 transition-colors duration-300">
                      [{project.date || project.metric}]
                    </span>
                  )}
                </button>
              );
            })}
          </motion.div>
        </div>
      </div>

      {/* ================= DRAGGABLE PREVIEW CARD ON RIGHT (WEBSITE COLOR BACKGROUND, MINIMAL DATA) ================= */}
      {showPreview && (
        <div className="fixed right-4 sm:right-6 md:right-8 lg:right-12 top-[56%] sm:top-[58%] -translate-y-1/2 z-30 pointer-events-none hidden sm:block">
          <motion.div
            drag
            dragConstraints={{ left: -360, right: 80, top: -200, bottom: 200 }}
            dragElastic={0.16}
            whileDrag={{ scale: 1.03, cursor: "grabbing" }}
            whileHover={{ scale: 1.01 }}
            className={`pointer-events-auto rounded-3xl overflow-hidden shadow-2xl shadow-neutral-950/20 dark:shadow-black/70 cursor-grab select-none p-5 sm:p-6 bg-[#F9F7EF] dark:bg-[#121212] border border-black/10 dark:border-neutral-800 text-neutral-900 dark:text-[#F9F7EF] flex flex-col justify-between transition-colors duration-300 ${previewSizeClasses}`}
          >
            <AnimatePresence mode="wait">
              <motion.div
                key={activeProject.id}
                initial={{ opacity: 0, y: 8, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 1.02 }}
                transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
                className="w-full h-full flex flex-col justify-between select-none pointer-events-none"
              >
                {/* Top: Minimal Badge with Status Accent */}
                <div className="flex items-center justify-between w-full">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-black/5 dark:bg-white/10 font-mono text-[10px] font-black uppercase tracking-wider text-black dark:text-[#F9F7EF] border border-black/5 dark:border-white/10">
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: activeProject.bgColor }}
                    />
                    {activeProject.badge}
                  </span>
                  <span className="font-mono text-[9px] font-black uppercase tracking-widest text-black/40 dark:text-white/40">
                    ISHA VERIFIED
                  </span>
                </div>

                {/* Center: Minimal Data Display - Clean Big Metric & Label (No Clumsy Graphs) */}
                <div className="my-auto py-2 flex flex-col">
                  <div className="text-3xl sm:text-4xl md:text-[42px] font-black tracking-tight leading-none text-black dark:text-[#F9F7EF]">
                    {activeProject.date || activeProject.metric}
                  </div>
                  <div className="mt-2 text-xs sm:text-sm font-black tracking-tight text-red-600 dark:text-red-500 uppercase">
                    {activeProject.metric || activeProject.name}
                  </div>
                  <p className="mt-3 text-[11px] sm:text-xs font-medium leading-relaxed text-neutral-600 dark:text-neutral-400 line-clamp-2">
                    {activeProject.description}
                  </p>
                </div>

                {/* Bottom: Light Accent Line & Minimal Audit */}
                <div className="pt-3 border-t border-black/10 dark:border-neutral-800 flex flex-col gap-1.5">
                  <div className="w-full h-1 rounded-full bg-black/5 dark:bg-neutral-800 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: "100%",
                        backgroundColor: activeProject.bgColor,
                      }}
                    />
                  </div>
                  <div className="flex items-center justify-between font-mono text-[9px] text-black/50 dark:text-neutral-400">
                    <span className="truncate max-w-[180px]">
                      {activeProject.auditProof || "Docker Ground Truth"}
                    </span>
                    <span className="font-black text-black dark:text-white shrink-0">
                      PASS
                    </span>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default TikTikColorList;
