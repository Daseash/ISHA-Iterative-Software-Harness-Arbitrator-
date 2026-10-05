import React from "react";
import { Skiper35 } from "./skiper35";

export const StatsSection: React.FC = () => {
  return (
    <section
      id="stats"
      className="relative w-full h-screen bg-[#F9F7EF] dark:bg-black overflow-hidden select-none border-t border-b border-neutral-300 dark:border-neutral-900 transition-colors duration-300"
    >
      <Skiper35 className="h-full w-full" />
    </section>
  );
};

export default StatsSection;
