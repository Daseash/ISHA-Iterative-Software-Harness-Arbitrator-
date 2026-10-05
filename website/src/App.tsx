import { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import { Preloader_002 } from "./components/Preloader_002";
import { Skiper29 } from "./components/v1/skiper29";
import { StatsPage } from "./pages/StatsPage";
import { sounds } from "./utils/sound";

export const DemoSkiper29 = () => {
  const [showPreloader, setShowPreloader] = useState(true);
  const [currentRoute, setCurrentRoute] = useState<"home" | "stats">(() => {
    if (typeof window === "undefined") return "home";
    const p = window.location.pathname.toLowerCase();
    const h = window.location.hash.toLowerCase();
    const s = window.location.search.toLowerCase();
    return p === "/stats" || p.startsWith("/stats") || h === "#stats" || s.includes("page=stats")
      ? "stats"
      : "home";
  });

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowPreloader(false);
    }, 2500);

    // Route listener
    const handleLocationChange = () => {
      const p = window.location.pathname.toLowerCase();
      const h = window.location.hash.toLowerCase();
      const s = window.location.search.toLowerCase();
      if (p === "/stats" || p.startsWith("/stats") || h === "#stats" || s.includes("page=stats")) {
        setCurrentRoute("stats");
      } else {
        setCurrentRoute("home");
      }
    };

    window.addEventListener("popstate", handleLocationChange);
    window.addEventListener("hashchange", handleLocationChange);

    // Global tactile click sound and client-side link interception for STATS
    const handleGlobalClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      const anchor = target?.closest("a") as HTMLAnchorElement | null;

      if (anchor) {
        const href = anchor.getAttribute("href");
        if (href === "/stats" || href === "#stats") {
          e.preventDefault();
          sounds.playClick();
          window.history.pushState({}, "", "/stats");
          setCurrentRoute("stats");
          window.scrollTo({ top: 0, behavior: "instant" });
          return;
        }
      }

      if (
        target?.closest("button") ||
        anchor ||
        target?.closest("[role='button']") ||
        target?.closest("input[type='submit']")
      ) {
        sounds.playClick();
      }
    };

    window.addEventListener("click", handleGlobalClick);

    return () => {
      clearTimeout(timer);
      window.removeEventListener("popstate", handleLocationChange);
      window.removeEventListener("hashchange", handleLocationChange);
      window.removeEventListener("click", handleGlobalClick);
    };
  }, []);

  const handleBackHome = () => {
    sounds.playClick();
    window.history.pushState({}, "", "/");
    setCurrentRoute("home");
    window.scrollTo({ top: 0, behavior: "instant" });
  };

  return (
    <main className="relative min-h-screen bg-[#F9F7EF] dark:bg-black transition-colors duration-300">
      <AnimatePresence mode="wait">
        {showPreloader && currentRoute === "home" && <Preloader_002 />}
      </AnimatePresence>

      {currentRoute === "stats" ? (
        <StatsPage onBack={handleBackHome} />
      ) : (
        <Skiper29 />
      )}
    </main>
  );
};

export default DemoSkiper29;
