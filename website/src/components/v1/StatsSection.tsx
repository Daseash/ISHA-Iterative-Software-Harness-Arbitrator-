import React from "react";
import { Skiper35 } from "./skiper35";
import { ArrowUpRight, Flame, ShieldCheck, DollarSign } from "lucide-react";
import { sounds } from "../../utils/sound";

export const StatsSection: React.FC = () => {
  const handleOpenStatsPage = () => {
    sounds.playClick();
    window.history.pushState({}, "", "/stats");
    window.dispatchEvent(new PopStateEvent("popstate"));
  };

  return (
    <section
      id="stats"
      className="relative py-20 px-4 sm:px-8 md:px-12 bg-[#F9F7EF] dark:bg-black transition-colors font-black"
    >
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 border-b border-neutral-300 dark:border-neutral-800 pb-6">
          <div className="space-y-2">
            <span className="font-mono text-xs uppercase tracking-[0.3em] text-red-600 font-bold block">
              AUDITED BENCHMARKS · SWE-BENCH LITE
            </span>
            <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tight text-red-600">
              STATS
            </h2>
          </div>

          <button
            onClick={handleOpenStatsPage}
            className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-black text-[#F9F7EF] dark:bg-[#F9F7EF] dark:text-black font-mono text-xs sm:text-sm uppercase tracking-wider font-black hover:scale-105 transition-all shadow-xl cursor-pointer shrink-0 self-start sm:self-auto"
          >
            <span>OPEN FULL-SCREEN STATS</span>
            <ArrowUpRight className="w-4 h-4 stroke-[3]" />
          </button>
        </div>

        {/* Skiper35 Interactive Expandable Showcase */}
        <div className="w-full h-[540px] sm:h-[600px] md:h-[640px]">
          <Skiper35 className="h-full" />
        </div>

        {/* Bottom Quick Metric Pills */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 text-black dark:text-white font-mono text-xs">
          <div className="p-4 rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 flex items-center gap-3">
            <Flame className="w-5 h-5 text-red-600 shrink-0" />
            <div>
              <span className="font-black text-sm block">14.0% - 20.6%</span>
              <span className="text-[10px] text-neutral-500 uppercase">SWE-bench Lite</span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 flex items-center gap-3">
            <ShieldCheck className="w-5 h-5 text-green-500 shrink-0" />
            <div>
              <span className="font-black text-sm block">7 Resolved</span>
              <span className="text-[10px] text-neutral-500 uppercase">Official Docker</span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 flex items-center gap-3">
            <DollarSign className="w-5 h-5 text-blue-500 shrink-0" />
            <div>
              <span className="font-black text-sm block">$0.00 / Task</span>
              <span className="text-[10px] text-neutral-500 uppercase">Pareto Leader</span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-red-600 animate-ping shrink-0" />
            <div>
              <span className="font-black text-sm block">0.0% Abort</span>
              <span className="text-[10px] text-neutral-500 uppercase">Clean AST Engine</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default StatsSection;
