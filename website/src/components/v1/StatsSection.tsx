import React from "react";
import { Skiper35 } from "./skiper35";

export const StatsSection: React.FC = () => {
  return (
    <section
      id="stats"
      className="relative w-full h-screen bg-black overflow-hidden select-none border-t border-b border-neutral-900"
    >
      <Skiper35 className="h-full w-full" />
    </section>
  );
};

export default StatsSection;
