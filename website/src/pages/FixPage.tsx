"use client";

import React, { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Skiper82 } from "../components/v1/skiper82";
import { Navbar_001 } from "../components/v1/skiper13";
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
    <main className="relative w-full h-screen min-h-screen bg-[#F9F7EF] dark:bg-black overflow-hidden select-none transition-colors duration-300 flex flex-col justify-between">
      <Navbar_001 hideStats hideGithub />

      {/* ================= CENTER CHAT INPUT EXPERIENCE ================= */}
      <section className="flex-1 w-full flex items-center justify-center px-4 pt-24 pb-6">
        <Skiper82 />
      </section>

      {/* ================= BOTTOM CLI BADGE (MATCHING SCREENSHOT) ================= */}
      <footer className="w-full flex items-center justify-center pb-6 px-4 z-20 shrink-0">
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
