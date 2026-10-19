"use client";

import React, { useState } from "react";
import { ArrowLeft, Check, Copy, Sparkles, ExternalLink } from "lucide-react";
import { Skiper82 } from "../components/v1/skiper82";
import { DarkModeSwitch } from "../components/unlumen-ui/DarkModeSwitch";
import { sounds } from "../utils/sound";

interface FixPageProps {
  onBack?: () => void;
}

export const FixPage: React.FC<FixPageProps> = () => {
  const [copied, setCopied] = useState(false);
  const [cliFlavor, setCliFlavor] = useState<"pnpm" | "pip">("pnpm");

  const pnpmCommand = "pnpm dlx shadcn add @skiper-ui/skiper82";
  const pipCommand = "pip install -e isha-agent/";

  const activeCommand = cliFlavor === "pnpm" ? pnpmCommand : pipCommand;

  const handleCopyCommand = () => {
    navigator.clipboard.writeText(activeCommand);
    sounds.playSuccess();
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  const handleNavigateHome = (e: React.MouseEvent) => {
    e.preventDefault();
    sounds.playClick();
    window.history.pushState({}, "", "/");
    window.dispatchEvent(new PopStateEvent("popstate"));
  };

  const handleNavigateStats = (e: React.MouseEvent) => {
    e.preventDefault();
    sounds.playClick();
    window.history.pushState({}, "", "/stats");
    window.dispatchEvent(new PopStateEvent("popstate"));
  };

  return (
    <main className="relative w-full h-screen min-h-screen bg-[#F9F7EF] dark:bg-black overflow-hidden select-none transition-colors duration-300 flex flex-col justify-between">
      {/* ================= TOP NAVIGATION BAR ================= */}
      <header className="w-full flex items-center justify-between px-6 sm:px-10 py-5 z-20 shrink-0 border-b border-neutral-200/60 dark:border-neutral-900">
        {/* Back to Home Button */}
        <div className="flex items-center gap-3">
          <a
            href="/"
            onClick={handleNavigateHome}
            className="group flex items-center gap-2.5 text-neutral-600 hover:text-black dark:text-neutral-400 dark:hover:text-white transition-colors cursor-pointer"
          >
            <div className="w-8 h-8 rounded-full flex items-center justify-center bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-xs group-hover:scale-105 transition-transform">
              <ArrowLeft className="w-4 h-4 text-red-600 stroke-[2.5]" />
            </div>
            <div className="flex items-center gap-1.5 font-black text-sm tracking-tight">
              <span>ISHA</span>
              <span className="text-neutral-400 dark:text-neutral-600">/</span>
              <span className="text-red-600 uppercase font-black">FIX</span>
            </div>
          </a>

          <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-red-600/10 text-red-600 border border-red-600/20 text-[10px] font-mono font-bold tracking-wider uppercase ml-2">
            <Sparkles className="w-3 h-3" />
            AI Input 002
          </span>
        </div>

        {/* Right Actions: STATS link + Theme Toggle */}
        <div className="flex items-center gap-4">
          <a
            href="/stats"
            onClick={handleNavigateStats}
            className="font-mono text-xs font-bold uppercase tracking-wider text-neutral-600 hover:text-red-600 dark:text-neutral-400 dark:hover:text-red-400 transition-colors"
          >
            STATS ↗
          </a>

          <a
            href="https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden md:flex items-center gap-1 font-mono text-xs font-bold uppercase tracking-wider text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white transition-colors"
          >
            <span>GITHUB</span>
            <ExternalLink className="w-3 h-3" />
          </a>

          <DarkModeSwitch />
        </div>
      </header>

      {/* ================= CENTER CHAT INPUT EXPERIENCE ================= */}
      <section className="flex-1 w-full flex items-center justify-center px-4 py-6">
        <Skiper82 />
      </section>

      {/* ================= BOTTOM CLI BADGE (MATCHING SCREENSHOT) ================= */}
      <footer className="w-full flex items-center justify-center pb-6 px-4 z-20 shrink-0">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-2xl bg-neutral-900/90 text-neutral-300 dark:bg-neutral-900 dark:text-neutral-300 border border-neutral-800 shadow-xl text-xs font-mono backdrop-blur-md">
          {/* Flavor toggle: pnpm / pip */}
          <button
            type="button"
            onClick={() => {
              sounds.playClick();
              setCliFlavor(cliFlavor === "pnpm" ? "pip" : "pnpm");
            }}
            className="flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-neutral-800 text-neutral-400 hover:text-white transition-colors cursor-pointer text-[11px] font-bold"
            title="Toggle between pnpm and pip CLI"
          >
            <span>{cliFlavor}</span>
            <span className="text-[10px] text-neutral-500">↕</span>
          </button>

          <span className="text-neutral-600">|</span>

          {/* Command text */}
          <span className="text-neutral-200 select-all font-mono text-[11px] sm:text-xs tracking-tight">
            {activeCommand}
          </span>

          {/* Copy button */}
          <button
            type="button"
            onClick={handleCopyCommand}
            className="ml-1 p-1 rounded hover:bg-neutral-800 text-neutral-400 hover:text-white transition-colors cursor-pointer"
            title="Copy command"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>
        </div>
      </footer>
    </main>
  );
};

export default FixPage;
