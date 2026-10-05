import React from "react";
import { Skiper35 } from "../components/v1/skiper35";
import { Navbar_001 } from "../components/v1/skiper13";

interface StatsPageProps {
  onBack?: () => void;
}

export const StatsPage: React.FC<StatsPageProps> = () => {
  return (
    <main className="relative w-full min-h-screen md:h-screen bg-[#F9F7EF] dark:bg-black overflow-y-auto md:overflow-hidden select-none transition-colors duration-300 flex flex-col justify-start md:justify-between">
      {/* Floating Navbar */}
      <Navbar_001 />

      {/* Left-Corner STATS Heading */}
      <div className="w-full px-5 sm:px-10 md:px-14 lg:px-16 pt-20 sm:pt-24 pb-2 text-left z-20 shrink-0">
        <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black uppercase tracking-tight text-red-600">
          STATS
        </h1>
        <p className="font-mono text-xs uppercase tracking-widest text-neutral-500 dark:text-neutral-400 font-bold mt-1">
          AUDITED BENCHMARKS · SWE-BENCH LITE · SMOKE 50
        </p>
      </div>

      {/* Full-Height Skiper35 Interactive Gallery */}
      <div className="flex-1 w-full min-h-0">
        <Skiper35 className="h-full w-full" />
      </div>
    </main>
  );
};

export default StatsPage;
