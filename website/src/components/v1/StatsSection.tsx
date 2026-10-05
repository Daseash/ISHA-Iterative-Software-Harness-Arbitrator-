import React from "react";
import { Skiper35 } from "./skiper35";

export const StatsSection: React.FC = () => {
  return (
    <section
      id="stats"
      className="relative w-full min-h-screen bg-[#F9F7EF] dark:bg-black overflow-hidden select-none border-t border-b border-neutral-300 dark:border-neutral-900 transition-colors duration-300 flex flex-col justify-between"
    >
      {/* STATS Section Heading */}
      <div className="w-full text-center pt-16 sm:pt-20 pb-2 z-20 relative px-4">
        <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tight text-red-600">
          STATS
        </h2>
        <p className="font-mono text-xs uppercase tracking-widest text-neutral-500 dark:text-neutral-400 font-bold mt-2">
          AUDITED BENCHMARKS · SWE-BENCH LITE · SMOKE 50
        </p>
      </div>

      {/* Full-Height Skiper35 Gallery */}
      <div className="flex-1 w-full min-h-[620px] md:min-h-[720px]">
        <Skiper35 className="h-full w-full" />
      </div>
    </section>
  );
};

export default StatsSection;
