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
  const [logoVariant, setLogoVariant] = useState<"dot" | "title">(() => {
    if (typeof window !== "undefined") {
      const p = new URLSearchParams(window.location.search);
      return p.get("logo") === "1" || p.get("logo") === "dot" ? "dot" : "title";
    }
    return "title";
  });

  const toggleLogoVariant = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    sounds.playClick();
    const next = logoVariant === "dot" ? "title" : "dot";
    setLogoVariant(next);
    if (typeof window !== "undefined") {
      const icon = document.getElementById("dynamic-favicon") as HTMLLinkElement;
      if (icon) icon.href = next === "title" ? "/favicon-clean.svg?v=3" : "/favicon-dot.svg?v=3";
      document.title =
        next === "title"
          ? "Isha · Iterative Software Harness Arbitrator"
          : "isha. · Iterative Software Harness Arbitrator";
      const u = new URL(window.location.href);
      u.searchParams.set("logo", next === "title" ? "2" : "1");
      window.history.replaceState(null, "", u.toString());
    }
  };

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
        {/* Back to Home Button with clean brand typography (no black background) */}
        <div className="flex items-center gap-3">
          <a
            href="/"
            onClick={handleNavigateHome}
            className="group flex items-center gap-3.5 text-neutral-900 hover:text-black dark:text-neutral-100 dark:hover:text-white transition-colors cursor-pointer"
          >
            <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-full flex items-center justify-center bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-sm group-hover:scale-105 group-hover:border-neutral-300 dark:group-hover:border-neutral-700 transition-all shrink-0">
              <ArrowLeft className="w-5 h-5 sm:w-6 sm:h-6 text-red-600 stroke-[2.5] group-hover:-translate-x-0.5 transition-transform" />
            </div>

            {/* Clean Brand Typography without dark background */}
            <div className="flex items-center gap-2 sm:gap-2.5 font-black text-2xl sm:text-3xl tracking-tight select-none">
              {logoVariant === "title" ? (
                <div
                  role="button"
                  tabIndex={0}
                  onClick={toggleLogoVariant}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      toggleLogoVariant(e as unknown as React.MouseEvent);
                    }
                  }}
                  aria-label="Logo: Isha with red node. Click or press Enter to toggle variant."
                  title="Option 2: Isha · Click to toggle logo"
                  className="flex items-center gap-1 cursor-pointer group/logo outline-none focus-visible:ring-1 focus-visible:ring-red-500 rounded"
                >
                  <span className="text-neutral-950 dark:text-white group-hover/logo:text-red-600 transition-colors">
                    Isha
                  </span>
                  <div className="w-2.5 h-2.5 rounded-full bg-red-600 mb-2.5 shrink-0 group-hover/logo:scale-125 transition-transform duration-300 shadow-sm" />
                </div>
              ) : (
                <div
                  role="button"
                  tabIndex={0}
                  onClick={toggleLogoVariant}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      toggleLogoVariant(e as unknown as React.MouseEvent);
                    }
                  }}
                  aria-label="Logo: isha with red period. Click or press Enter to toggle variant."
                  title="Option 1: isha. · Click to toggle logo"
                  className="flex items-center cursor-pointer group/logo outline-none focus-visible:ring-1 focus-visible:ring-red-500 rounded"
                >
                  <span className="text-neutral-950 dark:text-white group-hover/logo:text-red-600 transition-colors">
                    isha<span className="text-red-600">.</span>
                  </span>
                </div>
              )}

              <span className="text-neutral-400 dark:text-neutral-600 font-light select-none">
                /
              </span>

              <span className="text-red-600 font-mono font-black uppercase">
                FIX
              </span>
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
