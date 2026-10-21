"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check } from "lucide-react";
import { sounds } from "../../utils/sound";

export interface Skiper46Props {
  currentRepo?: string;
  onSelectRepo?: (repo: string) => void;
  className?: string;
}

export const Skiper46: React.FC<Skiper46Props> = ({
  currentRepo = "django/django",
  onSelectRepo,
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [repoInput, setRepoInput] = useState(currentRepo);
  const [connectedRepo, setConnectedRepo] = useState(currentRepo);

  const presets = [
    { name: "django/django", issues: 3, branch: "main" },
    { name: "pallets/flask", issues: 1, branch: "main" },
    { name: "sympy/sympy", issues: 4, branch: "master" },
    { name: "scikit-learn/scikit-learn", issues: 2, branch: "main" },
  ];

  const handleConnect = (repo: string) => {
    setConnectedRepo(repo);
    setRepoInput(repo);
    sounds.playSuccess();
    if (onSelectRepo) onSelectRepo(repo);
  };

  return (
    <div className={`relative inline-flex flex-col items-center select-none ${className}`}>
      {/* SVG Gooey Filter for Fluid Morphing */}
      <svg className="absolute w-0 h-0 pointer-events-none" aria-hidden="true">
        <defs>
          <filter id="skiper46-gooey">
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
            <feColorMatrix
              in="blur"
              mode="matrix"
              values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 19 -9"
              result="goo"
            />
            <feComposite in="SourceGraphic" in2="goo" operator="atop" />
          </filter>
        </defs>
      </svg>

      {/* Floating Expandable Card (Inspired by Next.js Skiper46 Dev Card) */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 14, scale: 0.94 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.94 }}
            transition={{
              type: "spring",
              stiffness: 420,
              damping: 28,
            }}
            className="absolute bottom-14 z-50 w-72 sm:w-80 rounded-2xl bg-neutral-950 text-white p-4 shadow-2xl shadow-black/60 border border-neutral-800 backdrop-blur-xl"
          >
            {/* Header info matching Skiper46 screenshot 3 */}
            <div className="flex items-center justify-between pb-3 border-b border-neutral-800/80">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 fill-white" viewBox="0 0 24 24">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                </svg>
                <span className="font-mono text-xs font-black tracking-wider uppercase">
                  GitHub Target
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] text-neutral-400">v0.1.0</span>
                <span className="flex items-center justify-center px-1.5 py-0.5 rounded-full bg-red-600 text-white font-mono text-[10px] font-black">
                  3
                </span>
              </div>
            </div>

            {/* Status rows matching Skiper46 layout */}
            <div className="py-2.5 space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between text-neutral-300">
                <span className="text-neutral-500 font-bold">Errors</span>
                <span className="px-1.5 py-0.2 rounded bg-red-600/30 text-red-400 font-black border border-red-500/40">
                  3 Issues
                </span>
              </div>

              <div className="flex items-center justify-between text-neutral-300">
                <span className="text-neutral-500 font-bold">Connected Repo</span>
                <span className="text-white font-bold truncate max-w-[150px]">
                  {connectedRepo}
                </span>
              </div>

              <div className="flex items-center justify-between text-neutral-300">
                <span className="text-neutral-500 font-bold">AST Harness</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Ready
                </span>
              </div>
            </div>

            {/* Custom Repo Input Field */}
            <div className="pt-2">
              <div className="flex items-center gap-1.5 p-1 rounded-xl bg-neutral-900 border border-neutral-800">
                <input
                  type="text"
                  value={repoInput}
                  onChange={(e) => setRepoInput(e.target.value)}
                  placeholder="owner/repo (e.g. django/django)"
                  className="flex-1 bg-transparent px-2.5 py-1 text-xs font-mono text-white placeholder-neutral-500 outline-none"
                />
                <button
                  type="button"
                  onClick={() => handleConnect(repoInput)}
                  className="px-3 py-1 rounded-lg bg-red-600 hover:bg-red-700 text-white font-mono text-[11px] font-black transition-colors cursor-pointer"
                >
                  Connect
                </button>
              </div>
            </div>

            {/* Quick Presets */}
            <div className="mt-3 pt-2 border-t border-neutral-900">
              <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-500 block mb-1.5">
                Popular Golden Repos
              </span>
              <div className="grid grid-cols-2 gap-1.5">
                {presets.map((preset) => (
                  <button
                    key={preset.name}
                    type="button"
                    onClick={() => handleConnect(preset.name)}
                    className={`flex items-center justify-between p-1.5 rounded-lg text-left font-mono text-[10px] transition-all cursor-pointer ${
                      connectedRepo === preset.name
                        ? "bg-red-600/20 text-red-400 border border-red-500/40"
                        : "bg-neutral-900/60 hover:bg-neutral-800 text-neutral-400 hover:text-white"
                    }`}
                  >
                    <span className="truncate pr-1">{preset.name.split("/")[1]}</span>
                    {connectedRepo === preset.name && <Check className="w-3 h-3 text-red-400 shrink-0" />}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Trigger Button matching website theme (Skiper46 Style) */}
      <motion.button
        type="button"
        onClick={() => {
          sounds.playClick();
          setIsOpen(!isOpen);
        }}
        whileHover={{ scale: 1.06 }}
        whileTap={{ scale: 0.94 }}
        className="relative group flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F9F7EF] dark:bg-neutral-900 text-neutral-900 dark:text-white border border-neutral-300 dark:border-neutral-700 shadow-md hover:shadow-lg transition-all duration-200 cursor-pointer"
        title="Connect GitHub Repository for ISHA Fix"
      >
        {/* GitHub Logo Icon in Circle */}
        <div className="w-6 h-6 rounded-full bg-neutral-950 dark:bg-white text-white dark:text-black flex items-center justify-center shrink-0">
          <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
        </div>

        <span className="font-mono text-xs font-black tracking-tight">
          {connectedRepo}
        </span>

        {/* Status Dot */}
        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
      </motion.button>
    </div>
  );
};

export default Skiper46;
