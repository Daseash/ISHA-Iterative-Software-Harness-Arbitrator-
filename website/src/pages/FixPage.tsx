"use client";

import React, { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Skiper82 } from "../components/v1/skiper82";
import { Navbar_001 } from "../components/v1/skiper13";
import { ScrollHighlight } from "../components/v1/ScrollHighlight";
import { sounds } from "../utils/sound";

interface FixPageProps {
  onBack?: () => void;
}

export const FixPage: React.FC<FixPageProps> = () => {
  const [copied, setCopied] = useState(false);

  const command = "pip install isha";

  const handleCopyCommand = () => {
    navigator.clipboard.writeText(command);
    sounds.playSuccess();
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  return (
    <main className="relative w-full min-h-screen md:h-screen bg-[#F9F7EF] dark:bg-black overflow-y-auto md:overflow-hidden select-none transition-colors duration-300 flex flex-col justify-start md:justify-between">
      {/* Floating Home Navbar with Red Dot & Menu */}
      <Navbar_001 />

      {/* Left-Corner FIX Heading in Exact STATS Style */}
      <div className="w-full px-5 sm:px-10 md:px-14 lg:px-16 pt-20 sm:pt-24 pb-2 text-left z-20 shrink-0">
        <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black uppercase tracking-tight text-red-600">
          <ScrollHighlight variant="round" color="coral">
            FIX
          </ScrollHighlight>
        </h1>
        <p className="font-mono text-xs uppercase tracking-widest text-neutral-500 dark:text-neutral-400 font-bold mt-1">
          <ScrollHighlight variant="brush" color="sun">
            AUTONOMOUS HARNESS • AST SYNTHESIZER
          </ScrollHighlight>
        </p>
      </div>

      {/* ================= CENTER CHAT INPUT EXPERIENCE ================= */}
      <section className="flex-1 w-full flex items-center justify-center px-4 py-2 min-h-0">
        <Skiper82 className="h-full" />
      </section>

      {/* ================= BOTTOM CLI BADGE ================= */}
      <footer className="w-full flex items-center justify-center pb-4 sm:pb-6 px-4 z-20 shrink-0">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-2xl bg-neutral-900/90 text-neutral-300 dark:bg-neutral-900 dark:text-neutral-300 border border-neutral-800 shadow-xl text-xs font-mono backdrop-blur-md">
          {/* Command text */}
          <span className="text-neutral-200 select-all font-mono text-[11px] sm:text-xs tracking-tight">
            {command}
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
