"use client";

import React, { useState } from "react";
import { ArrowLeft, Check, Copy, ExternalLink } from "lucide-react";
import { Skiper82 } from "../components/v1/skiper82";
import { ThemeToggleButton1 } from "../components/v1/skiper4";
import { sounds } from "../utils/sound";

interface FixPageProps {
  onBack?: () => void;
}

export const FixPage: React.FC<FixPageProps> = () => {
  const [copied, setCopied] = useState(false);
  const [cliFlavor, setCliFlavor] = useState<"pip" | "mcp" | "pnpm">("pip");

  const pipCommand = "pip install isha && isha fix .";
  const mcpCommand = "isha-mcp";
  const pnpmCommand = "pnpm dlx shadcn add @skiper-ui/skiper82";

  const activeCommand =
    cliFlavor === "pip"
      ? pipCommand
      : cliFlavor === "mcp"
      ? mcpCommand
      : pnpmCommand;

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
        {/* Back to Home Button with enlarged branding */}
        <div className="flex items-center gap-3">
          <a
            href="/"
            onClick={handleNavigateHome}
            className="group flex items-center gap-3.5 text-neutral-900 hover:text-black dark:text-neutral-100 dark:hover:text-white transition-colors cursor-pointer"
          >
            <div className="w-12 h-12 rounded-full flex items-center justify-center bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm group-hover:scale-105 transition-transform">
              <ArrowLeft className="w-6 h-6 text-red-600 stroke-[2.5]" />
            </div>
            <div className="flex items-center gap-2 font-black text-2xl sm:text-3xl tracking-tight">
              <span>ISHA</span>
              <span className="text-neutral-400 dark:text-neutral-600">/</span>
              <span className="text-red-600 uppercase font-black">FIX</span>
            </div>
          </a>
        </div>

        {/* Right Actions: STATS link + GITHUB + Theme Toggle */}
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

          <ThemeToggleButton1 className="size-9 sm:size-10" />
        </div>
      </header>

      {/* ================= CENTER CHAT INPUT EXPERIENCE ================= */}
      <section className="flex-1 w-full flex items-center justify-center px-4 py-6">
        <Skiper82 />
      </section>

      {/* ================= BOTTOM CLI BADGE ================= */}
      <footer className="w-full flex items-center justify-center pb-6 px-4 z-20 shrink-0">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-2xl bg-neutral-900 text-neutral-300 dark:bg-neutral-900 dark:text-neutral-300 border border-neutral-800 shadow-xl text-xs font-mono">
          {/* Flavor toggle: pip / mcp / pnpm */}
          <button
            type="button"
            onClick={() => {
              sounds.playClick();
              setCliFlavor(
                cliFlavor === "pip"
                  ? "mcp"
                  : cliFlavor === "mcp"
                  ? "pnpm"
                  : "pip"
              );
            }}
            className="flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-neutral-800 text-neutral-400 hover:text-white transition-colors cursor-pointer text-[11px] font-bold"
            title="Toggle between pip, mcp, and pnpm CLI"
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
