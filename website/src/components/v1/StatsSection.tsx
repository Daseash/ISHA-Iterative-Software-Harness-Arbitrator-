import React from "react";
import { Skiper35 } from "./skiper35";
import { CheckCircle2, DollarSign, ShieldAlert } from "lucide-react";

export const StatsSection: React.FC = () => {
  return (
    <section
      id="stats"
      className="relative py-24 px-6 md:px-12 bg-[#F9F7EF] dark:bg-black transition-colors font-black"
    >
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Section Header */}
        <div className="text-center space-y-4">
          <span className="font-mono text-xs uppercase tracking-[0.3em] text-red-600 font-bold block">
            EMPIRICAL VERIFICATION · SMOKE 50 · SWE-BENCH LITE
          </span>
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tight text-red-600">
            STATS
          </h2>
          <p className="max-w-3xl mx-auto font-mono text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 font-bold uppercase tracking-wider">
            Audited evaluation runs on official maintainer Docker environments. Hover or click each card to expand deep telemetry, benchmark comparisons, and verified test suites.
          </p>
        </div>

        {/* Skiper35 Interactive Hover-Expand Card Showcase */}
        <div className="w-full">
          <Skiper35 />
        </div>

        {/* Global Summary Metrics Strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-neutral-300 dark:border-neutral-800">
          <div className="p-5 rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-neutral-500 mb-2">
              <span className="font-mono text-[10px] uppercase tracking-wider">SWE-bench Lite</span>
              <CheckCircle2 className="w-4 h-4 text-green-500" />
            </div>
            <span className="text-2xl sm:text-3xl font-black text-black dark:text-white">
              7 Resolved
            </span>
            <span className="font-mono text-[11px] text-neutral-500 dark:text-neutral-400 mt-1">
              Official Docker maintainer suites
            </span>
          </div>

          <div className="p-5 rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-neutral-500 mb-2">
              <span className="font-mono text-[10px] uppercase tracking-wider">Resolve Rate</span>
              <span className="h-2 w-2 rounded-full bg-red-600 animate-pulse" />
            </div>
            <span className="text-2xl sm:text-3xl font-black text-red-600">
              20.6%
            </span>
            <span className="font-mono text-[11px] text-neutral-500 dark:text-neutral-400 mt-1">
              On produced patches (14.0% overall)
            </span>
          </div>

          <div className="p-5 rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-neutral-500 mb-2">
              <span className="font-mono text-[10px] uppercase tracking-wider">Cost Frontier</span>
              <DollarSign className="w-4 h-4 text-green-500" />
            </div>
            <span className="text-2xl sm:text-3xl font-black text-black dark:text-white">
              $0.00
            </span>
            <span className="font-mono text-[11px] text-neutral-500 dark:text-neutral-400 mt-1">
              Free-tier Groq + Gemini cascade
            </span>
          </div>

          <div className="p-5 rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-neutral-500 mb-2">
              <span className="font-mono text-[10px] uppercase tracking-wider">Patch Engine</span>
              <ShieldAlert className="w-4 h-4 text-red-500" />
            </div>
            <span className="text-2xl sm:text-3xl font-black text-black dark:text-white">
              0.0%
            </span>
            <span className="font-mono text-[11px] text-neutral-500 dark:text-neutral-400 mt-1">
              Apply failures & container aborts
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default StatsSection;
