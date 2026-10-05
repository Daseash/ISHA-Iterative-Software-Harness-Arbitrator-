import React from "react";
import { ArrowLeft, ExternalLink, ShieldCheck, Flame, Cpu } from "lucide-react";
import { Skiper35 } from "../components/v1/skiper35";
import { sounds } from "../utils/sound";

interface StatsPageProps {
  onBack?: () => void;
}

export const StatsPage: React.FC<StatsPageProps> = ({ onBack }) => {
  const handleBack = () => {
    sounds.playClick();
    if (onBack) {
      onBack();
    } else {
      window.history.pushState({}, "", "/");
      window.dispatchEvent(new PopStateEvent("popstate"));
    }
  };

  return (
    <main className="w-full h-screen bg-black text-white flex flex-col justify-between p-4 sm:p-6 md:p-8 overflow-hidden select-none font-black">
      {/* Top Bar: Navigation & Core Indicators */}
      <header className="flex items-center justify-between gap-4 pb-4 border-b border-neutral-900 shrink-0">
        <button
          onClick={handleBack}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-neutral-900 hover:bg-neutral-800 text-white font-mono text-xs sm:text-sm font-bold uppercase tracking-wider transition-all duration-200 cursor-pointer border border-neutral-800 hover:border-neutral-700"
        >
          <ArrowLeft className="w-4 h-4 text-red-500" />
          <span>BACK TO HOME</span>
        </button>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-neutral-400">
            <span className="h-2 w-2 rounded-full bg-red-600 animate-pulse" />
            <span>EMPIRICAL BENCHMARKS</span>
            <span className="text-neutral-700">/</span>
            <span className="text-white">SWE-BENCH LITE</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <a
            href="https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-neutral-950 hover:bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-white font-mono text-xs uppercase tracking-wider transition-colors"
          >
            <span>GITHUB</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </header>

      {/* Main Full-Height Skiper35 Accordion Showcase */}
      <section className="flex-1 w-full min-h-0 my-4 sm:my-6">
        <Skiper35 className="h-full" />
      </section>

      {/* Footer Strip */}
      <footer className="flex flex-col sm:flex-row items-center justify-between gap-2 pt-3 border-t border-neutral-900 text-neutral-500 font-mono text-[11px] uppercase tracking-wider shrink-0">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-neutral-400">
            <Flame className="w-3.5 h-3.5 text-red-500" /> SMOKE 50
          </span>
          <span className="text-neutral-700">·</span>
          <span className="flex items-center gap-1 text-neutral-400">
            <ShieldCheck className="w-3.5 h-3.5 text-green-500" /> 7 DOCKER GREEN
          </span>
          <span className="text-neutral-700">·</span>
          <span className="flex items-center gap-1 text-neutral-400">
            <Cpu className="w-3.5 h-3.5 text-blue-500" /> $0.00 INFERENCE
          </span>
        </div>
        <div className="text-neutral-600 font-bold">
          HOVER OR TAP PANELS TO EXPAND BENCHMARK TELEMETRY
        </div>
      </footer>
    </main>
  );
};

export default StatsPage;
