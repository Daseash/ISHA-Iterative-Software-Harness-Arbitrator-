"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Volume2, VolumeX } from "lucide-react";
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
  details?: {
    category?: string;
    highlights?: string[];
    stat1?: { label: string; value: string; detail?: string };
    stat2?: { label: string; value: string; detail?: string };
    stat3?: { label: string; value: string; detail?: string };
  };
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
  enableSound: initialEnableSound = true,
  infiniteScroll = true,
  scrollThreshold = 45,
}) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [soundEnabled, setSoundEnabled] = useState(initialEnableSound);
  const accumulatedDeltaRef = useRef(0);
  const isTransitioningRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const activeProject = projects[activeIndex] || projects[0];

  // Play "tik" sound effect on index change
  const handleIndexChange = useCallback(
    (newIndex: number) => {
      if (newIndex === activeIndex) return;
      setActiveIndex(newIndex);
      if (soundEnabled) {
        sounds.playTick();
      }
    },
    [activeIndex, soundEnabled]
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

  // Preview card sizing matching skiper24 reference
  const previewSizeClasses = {
    sm: "w-[260px] h-[280px]",
    md: "w-[300px] sm:w-[340px] h-[320px] sm:h-[360px]",
    lg: "w-[310px] sm:w-[360px] md:w-[410px] h-[330px] sm:h-[380px] md:h-[430px]",
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
      {/* ================= TOP-LEFT AUDIO CONTROLS (MATCHING SKIPER24) ================= */}
      <div className="fixed top-5 sm:top-6 left-4 sm:left-6 md:left-10 z-40">
        <button
          type="button"
          onClick={() => {
            setSoundEnabled(!soundEnabled);
            sounds.playClick();
          }}
          className="flex items-center justify-center w-11 h-11 rounded-2xl bg-black text-white hover:bg-neutral-900 transition-all cursor-pointer shadow-xl border border-white/10"
          title={soundEnabled ? "Mute tick sound" : "Enable tick sound"}
          aria-label={soundEnabled ? "Mute tick sound" : "Enable tick sound"}
        >
          {soundEnabled ? (
            <Volume2 className="w-5 h-5 text-white" />
          ) : (
            <VolumeX className="w-5 h-5 text-neutral-400" />
          )}
        </button>
      </div>

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
                  className={`group text-left transition-all duration-300 focus:outline-none flex flex-wrap items-baseline gap-3 sm:gap-4 py-2 cursor-pointer ${
                    isActive
                      ? "opacity-100 scale-100"
                      : "opacity-30 hover:opacity-75 scale-[0.97]"
                  }`}
                >
                  {/* Big Typographic Title */}
                  <span
                    className={`text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold tracking-tight leading-none transition-colors duration-300 ${
                      isActive
                        ? "text-black dark:text-neutral-950 font-black drop-shadow-xs"
                        : "text-black/35 dark:text-neutral-950/35 group-hover:text-black/70 font-bold"
                    }`}
                  >
                    {project.name}
                  </span>

                  {/* Category Badge Pill */}
                  <span
                    className={`inline-flex items-center px-3.5 py-1 rounded-full text-xs font-medium tracking-wide transition-all duration-300 ${
                      isActive
                        ? "bg-black/15 text-black font-semibold"
                        : "bg-black/8 text-black/40 group-hover:bg-black/12"
                    }`}
                  >
                    {project.badge}
                  </span>

                  {/* Date or Key Metric Badge */}
                  {(project.date || project.metric) && (
                    <span
                      className={`text-xs sm:text-sm font-medium tracking-tight transition-colors duration-300 ${
                        isActive
                          ? "text-black/80 font-bold"
                          : "text-black/30"
                      }`}
                    >
                      [{project.date || project.metric}]
                    </span>
                  )}
                </button>
              );
            })}
          </motion.div>
        </div>
      </div>

      {/* ================= DRAGGABLE PREVIEW IMAGE CARD ON RIGHT (ONLY THE IMAGE) ================= */}
      {showPreview && (
        <div className="fixed right-6 sm:right-10 md:right-16 lg:right-24 top-[54%] -translate-y-1/2 z-30 pointer-events-none">
          <motion.div
            drag
            dragConstraints={{ left: -380, right: 80, top: -220, bottom: 220 }}
            dragElastic={0.16}
            whileDrag={{ scale: 1.03, cursor: "grabbing" }}
            whileHover={{ scale: 1.01 }}
            className={`pointer-events-auto rounded-[32px] sm:rounded-[36px] overflow-hidden shadow-2xl shadow-black/25 cursor-grab select-none p-0 bg-white/90 dark:bg-neutral-950/90 border border-black/10 dark:border-white/10 ${previewSizeClasses}`}
          >
            <AnimatePresence mode="wait">
              <motion.img
                key={activeProject.id}
                src={activeProject.image}
                alt={activeProject.name}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.04 }}
                transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                className="w-full h-full object-cover rounded-[32px] sm:rounded-[36px] select-none pointer-events-none"
                loading="eager"
              />
            </AnimatePresence>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default TikTikColorList;
