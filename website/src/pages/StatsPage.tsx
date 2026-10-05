import React from "react";
import { Skiper35 } from "../components/v1/skiper35";
import { Navbar_001 } from "../components/v1/skiper13";

interface StatsPageProps {
  onBack?: () => void;
}

export const StatsPage: React.FC<StatsPageProps> = () => {
  return (
    <main className="relative w-full h-screen bg-[#F9F7EF] dark:bg-black overflow-hidden select-none transition-colors duration-300">
      {/* Our floating navbar above the full-screen gallery */}
      <Navbar_001 />

      {/* Full-Screen Skiper35 Interactive Gallery */}
      <Skiper35 className="h-full w-full" />
    </main>
  );
};

export default StatsPage;
