"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Volume2, VolumeX, Move, ShieldCheck, Check } from "lucide-react";
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
  const [isCopied, setIsCopied] = useState(false);
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
      // Don't hijack if user is scrolling inside a nested scrollable element
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

  const copyAuditProof = (text: string) => {
    navigator.clipboard.writeText(text);
    sounds.playSuccess();
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // Preview card sizing
  const previewSizeClasses = {
    sm: "w-[280px] h-[360px]",
    md: "w-[340px] sm:w-[380px] h-[440px] sm:h-[480px]",
    lg: "w-[320px] sm:w-[380px] md:w-[420px] lg:w-[460px] h-[400px] sm:h-[480px] md:h-[540px] lg:h-[580px]",
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
      {/* ================= TOP-LEFT AUDIO & NAVIGATION CONTROLS ================= */}
      <div className="fixed top-5 sm:top-6 left-4 sm:left-6 md:left-10 z-40 flex items-center gap-2">
        {/* Audio Toggle Button */}
        <button
          type="button"
          onClick={() => {
            setSoundEnabled(!soundEnabled);
            sounds.playClick();
          }}
          className="flex items-center justify-center w-10 h-10 rounded-2xl bg-black/20 dark:bg-black/40 hover:bg-black/30 dark:hover:bg-black/60 text-neutral-900 dark:text-white backdrop-blur-md transition-all cursor-pointer border border-black/10 dark:border-white/10 shadow-lg"
          title={soundEnabled ? "Mute tick sound" : "Enable tick sound"}
          aria-label={soundEnabled ? "Mute tick sound" : "Enable tick sound"}
        >
          {soundEnabled ? (
            <Volume2 className="w-4 h-4 text-neutral-950 dark:text-white" />
          ) : (
            <VolumeX className="w-4 h-4 text-neutral-700 dark:text-neutral-400" />
          )}
        </button>

        {/* Counter Badge */}
        <div className="px-3.5 py-2 rounded-2xl bg-black/20 dark:bg-black/40 text-neutral-950 dark:text-white backdrop-blur-md font-mono text-xs font-black tracking-wider border border-black/10 dark:border-white/10 shadow-lg flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>
            {String(activeIndex + 1).padStart(2, "0")} / {String(projects.length).padStart(2, "0")}
          </span>
        </div>

        {/* Scroll Hint */}
        <span className="hidden md:inline-block font-mono text-[11px] font-bold text-neutral-900/60 dark:text-white/60 uppercase tracking-widest pl-2">
          Scroll or click to explore
        </span>
      </div>

      {/* ================= MAIN VERTICAL TYPOGRAPHIC SCROLL LIST ================= */}
      <div className="relative w-full h-full flex items-center px-6 sm:px-12 md:px-16 lg:px-20 z-20">
        <div className="w-full max-w-xl sm:max-w-2xl md:max-w-3xl lg:max-w-4xl relative">
          {/* Spring-animated list container kept centered */}
          <motion.div
            animate={{
              y: -activeIndex * 88,
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
                    className={`text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black tracking-tight leading-none transition-colors duration-300 ${
                      isActive
                        ? "text-neutral-950 dark:text-white drop-shadow-sm font-black"
                        : "text-neutral-900/40 dark:text-white/40 group-hover:text-neutral-900 dark:group-hover:text-white font-bold"
                    }`}
                  >
                    {project.name}
                  </span>

                  {/* Category Badge Pill */}
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-[11px] sm:text-xs font-mono font-bold tracking-wider transition-all duration-300 ${
                      isActive
                        ? "bg-black/25 dark:bg-white/20 text-neutral-950 dark:text-white shadow-xs font-black ring-1 ring-black/10 dark:ring-white/20"
                        : "bg-black/10 dark:bg-white/10 text-neutral-900/60 dark:text-white/60 group-hover:bg-black/20"
                    }`}
                  >
                    {project.badge}
                  </span>

                  {/* Date or Key Metric Badge */}
                  {(project.date || project.metric) && (
                    <span
                      className={`font-mono text-xs sm:text-sm font-bold tracking-tight transition-colors duration-300 ${
                        isActive
                          ? "text-neutral-900 dark:text-white/90 font-black"
                          : "text-neutral-900/50 dark:text-white/40"
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

      {/* ================= DRAGGABLE PREVIEW IMAGE CARD ON RIGHT ================= */}
      {showPreview && (
        <div className="fixed right-4 sm:right-8 md:right-12 lg:right-16 top-1/2 -translate-y-1/2 z-30 pointer-events-none">
          <motion.div
            drag
            dragConstraints={{ left: -320, right: 80, top: -200, bottom: 200 }}
            dragElastic={0.16}
            whileDrag={{ scale: 1.03, cursor: "grabbing" }}
            whileHover={{ scale: 1.01 }}
            className={`pointer-events-auto rounded-[32px] sm:rounded-[38px] overflow-hidden bg-white/95 dark:bg-neutral-950/95 border border-black/15 dark:border-white/20 shadow-2xl shadow-black/30 backdrop-blur-2xl cursor-grab flex flex-col p-4 sm:p-5 select-none ${previewSizeClasses}`}
          >
            {/* Top Drag Pill + Status */}
            <div className="flex items-center justify-between pb-3 border-b border-neutral-200 dark:border-neutral-800 text-[11px] font-mono font-black text-neutral-500">
              <div className="flex items-center gap-1.5 text-neutral-700 dark:text-neutral-300">
                <Move className="w-3.5 h-3.5 text-neutral-400" />
                <span className="uppercase tracking-wider">DRAGGABLE PREVIEW</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="font-mono text-emerald-600 dark:text-emerald-400">
                  {activeProject.date || activeProject.metric}
                </span>
              </div>
            </div>

            {/* Middle Graphic / Image Display with AnimatePresence Crossfade */}
            <div className="relative flex-1 w-full my-3 rounded-2xl overflow-hidden bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 flex items-center justify-center shadow-inner">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeProject.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 1.05 }}
                  transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
                  className="w-full h-full flex items-center justify-center p-2"
                >
                  <img
                    src={activeProject.image}
                    alt={activeProject.name}
                    className="w-full h-full object-contain rounded-xl drop-shadow-md select-none pointer-events-none"
                    loading="eager"
                  />
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Bottom Card Summary & Audit Info */}
            <div className="pt-2 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2">
                  <h4 className="font-black text-sm sm:text-base tracking-tight text-neutral-900 dark:text-white truncate">
                    {activeProject.name}
                  </h4>
                  <span className="shrink-0 text-[10px] font-mono font-black px-2 py-0.5 rounded-md bg-neutral-200 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 uppercase">
                    {activeProject.badge}
                  </span>
                </div>
                <p className="mt-1 text-xs text-neutral-600 dark:text-neutral-400 line-clamp-2 leading-relaxed font-medium">
                  {activeProject.description}
                </p>
              </div>

              {/* Quick Copy Audit Proof Command */}
              {activeProject.auditProof && (
                <div className="mt-3 pt-2.5 border-t border-neutral-200 dark:border-neutral-800 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 truncate">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                    <span className="font-mono text-[10px] text-neutral-500 dark:text-neutral-400 truncate font-semibold">
                      {activeProject.auditProof}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      copyAuditProof(activeProject.auditProof!);
                    }}
                    className="shrink-0 px-2 py-1 rounded-md bg-neutral-900 hover:bg-neutral-800 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-white font-mono text-[10px] font-bold transition-colors cursor-pointer flex items-center gap-1"
                  >
                    {isCopied ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-400" />
                        <span>COPIED</span>
                      </>
                    ) : (
                      <span>COPY AUDIT</span>
                    )}
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}

      {/* ================= BOTTOM HINT FOOTER ================= */}
      <footer className="fixed bottom-4 sm:bottom-6 left-6 sm:left-12 md:left-16 lg:left-20 z-30 pointer-events-none">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/20 dark:bg-black/40 text-neutral-900 dark:text-white backdrop-blur-md text-[11px] font-mono font-bold border border-black/10 dark:border-white/10 shadow-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>ISHA AUDITED ARCHIVE · TIK-TIK COLOR LIST</span>
        </div>
      </footer>
    </div>
  );
};

export default TikTikColorList;
