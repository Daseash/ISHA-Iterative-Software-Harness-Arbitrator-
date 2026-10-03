import { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import { Preloader_002 } from "./components/Preloader_002";
import { Skiper29 } from "./components/v1/skiper29";
import { sounds } from "./utils/sound";

export const DemoSkiper29 = () => {
  const [showPreloader, setShowPreloader] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowPreloader(false);
    }, 2500);

    // Global tactile click sound for all buttons, links, and interactive elements
    const handleGlobalClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      if (
        target?.closest("button") ||
        target?.closest("a") ||
        target?.closest("[role='button']") ||
        target?.closest("input[type='submit']")
      ) {
        sounds.playClick();
      }
    };

    window.addEventListener("click", handleGlobalClick, { passive: true });

    return () => {
      clearTimeout(timer);
      window.removeEventListener("click", handleGlobalClick);
    };
  }, []);

  return (
    <main className="relative min-h-screen bg-[#F9F7EF] dark:bg-black transition-colors duration-300">
      <AnimatePresence mode="wait">
        {showPreloader && <Preloader_002 />}
      </AnimatePresence>
      <Skiper29 />
    </main>
  );
};

export default DemoSkiper29;
