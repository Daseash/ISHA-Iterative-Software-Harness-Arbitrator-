import React from "react";
import { Skiper35 } from "./skiper35";

export const StatsSection: React.FC = () => {
  return (
    <section
      id="stats"
      className="relative w-full min-h-screen bg-[#F9F7EF] dark:bg-black overflow-hidden select-none border-t border-b border-neutral-300 dark:border-neutral-900 transition-colors duration-300 flex flex-col justify-between"
    >
      {/* Below the fix bar: Left corner STATS text in same red font */}
      <div className="w-full px-6 sm:px-10 md:px-14 lg:px-16 pt-8 sm:pt-12 pb-2 text-left z-20">
        <h2 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black uppercase tracking-tight text-red-600">
          STATS
        </h2>
      </div>

      {/* Full-Height Skiper35 Gallery */}
      <div className="flex-1 w-full min-h-[620px] md:min-h-[720px]">
        <Skiper35 className="h-full w-full" />
      </div>
    </section>
  );
};

export default StatsSection;
