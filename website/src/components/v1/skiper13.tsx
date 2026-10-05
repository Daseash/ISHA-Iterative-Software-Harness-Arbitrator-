import React, { useState, useEffect } from "react";
import { ArrowUpRight, Globe } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useEventListener } from "usehooks-ts";
import { ThemeToggleButton1 } from "./skiper4";

interface NavItem {
  id: string;
  number: string;
  name: string;
  href: string;
  sub: string;
  city: string;
  region: string;
  metric: string;
  status: "ONLINE" | "ACTIVE" | "VERIFIED" | "ZERO-COST";
  isExternal?: boolean;
}

const navItems: NavItem[] = [
  {
    id: "hero",
    number: "01",
    name: "HOME",
    href: "#hero",
    sub: "ITERATIVE SOFTWARE HARNESS ARBITRATOR",
    city: "SYDNEY",
    region: "AP-SOUTHEAST-2",
    metric: "NEURAL REPO INGESTION",
    status: "ONLINE",
  },
  {
    id: "about",
    number: "02",
    name: "ABOUT",
    href: "#about",
    sub: "TRIAGE, TEST SYNTHESIS & REPRO VERIFICATION",
    city: "TOKYO",
    region: "AP-NORTHEAST-1",
    metric: "RED-TO-GREEN TDD PIPELINE",
    status: "ACTIVE",
  },
  {
    id: "cli",
    number: "03",
    name: "CLI",
    href: "#cli",
    sub: "ONE-COMMAND PYTHON 3.10+ DEVELOPER RUNNER",
    city: "LOS ANGELES",
    region: "US-WEST-1",
    metric: "ZERO-CLONE PIP INSTALL",
    status: "VERIFIED",
  },
  {
    id: "fix",
    number: "04",
    name: "FIX",
    href: "#fix",
    sub: "AI REPAIR INPUT & TOURNAMENT ARBITRATION",
    city: "NEW YORK",
    region: "US-EAST-1",
    metric: "3-WORKTREE PARALLEL RACE",
    status: "ACTIVE",
  },
  {
    id: "stats",
    number: "05",
    name: "STATS",
    href: "#stats",
    sub: "SWE-BENCH LITE AUDIT & LAYA ECE CALIBRATION",
    city: "LONDON",
    region: "EU-WEST-1",
    metric: "66.7% YIELD · 0.0% ERRORS",
    status: "VERIFIED",
  },
  {
    id: "github",
    number: "06",
    name: "GIT HUB",
    href: "https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-",
    sub: "OPEN SOURCE REPOSITORY & REPRODUCIBLE RUNS",
    city: "MUMBAI",
    region: "AP-SOUTH-1",
    metric: "$0.00 INFERENCE BUDGET",
    status: "ZERO-COST",
    isExternal: true,
  },
];

export const Navbar_001: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState<number>(0);
  const [timeString, setTimeString] = useState<string>("");

  // Live UTC Clock update
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeString(
        now.toLocaleTimeString("en-US", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          timeZoneName: "short",
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Scroll listener for top bar styling
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 40);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Lock body scroll when overlay is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  // Close on Escape key
  useEventListener("keydown", (event: KeyboardEvent) => {
    if (event.key === "Escape" && isOpen) {
      setIsOpen(false);
    }
  });

  const activeItem = navItems[hoveredIndex] || navItems[0];

  return (
    <>
      {/* ================= FIXED TOP NAVBAR HEADER ================= */}
      <header
        className={`fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-5 sm:px-8 md:px-12 py-4 transition-all duration-300 font-black ${
          isScrolled || isOpen
            ? "bg-[#F9F7EF]/90 dark:bg-black/90 backdrop-blur-xl border-b border-neutral-300/40 dark:border-neutral-800/80 shadow-sm text-black dark:text-[#F9F7EF]"
            : "bg-transparent text-black dark:text-[#F9F7EF]"
        }`}
      >
        {/* Brand / Logo: EXACT Old Top-Left ISHA with Solid Red Dot */}
        <div className="flex items-center gap-6 md:gap-8">
          <a
            href="#hero"
            onClick={() => setIsOpen(false)}
            className="flex items-center gap-2.5 group"
          >
            <div className="h-3.5 w-3.5 rounded-full bg-red-600 transition-transform group-hover:scale-125 duration-300 shadow-sm shrink-0" />
            <span className="text-xl sm:text-2xl font-black tracking-tighter uppercase text-black dark:text-[#F9F7EF] group-hover:text-red-600 transition-colors">
              ISHA
            </span>
          </a>

          {/* Inline Quick Desktop Nav Links */}
          <nav className="hidden lg:flex items-center gap-6 font-mono text-xs uppercase tracking-widest font-black">
            {navItems.map((item) => (
              <a
                key={item.id}
                href={item.href}
                target={item.isExternal ? "_blank" : undefined}
                rel={item.isExternal ? "noreferrer" : undefined}
                className="hover:text-red-600 transition-colors inline-flex items-center gap-1 text-black dark:text-[#F9F7EF]"
              >
                <span>{item.name}</span>
                {item.isExternal && (
                  <ArrowUpRight className="w-3.5 h-3.5 stroke-[3] text-red-600" />
                )}
              </a>
            ))}
          </nav>
        </div>

        {/* Right Corner: Theme Toggle & Nike Expandable Menu Trigger Button */}
        <div className="flex items-center gap-2 sm:gap-3">
          <ThemeToggleButton1
            className="h-9 px-3 sm:h-10 sm:px-4 shadow-sm border border-neutral-300 dark:border-neutral-800 bg-neutral-200/80 dark:bg-neutral-900 text-black dark:text-[#F9F7EF]"
          />

          {/* NIKE MENU EXPANDABLE BUTTON */}
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            aria-label="Toggle Navigation Menu"
            className="flex items-center gap-2 h-9 sm:h-10 px-4 sm:px-5 rounded-full font-mono text-xs font-black uppercase tracking-widest transition-all cursor-pointer bg-neutral-900 dark:bg-[#F9F7EF] text-white dark:text-black hover:bg-red-600 dark:hover:bg-red-600 dark:hover:text-white shadow-md active:scale-95"
          >
            <div className="flex flex-col justify-center items-center w-3.5 h-3 relative">
              <span
                className={`w-3.5 h-0.5 bg-current transition-all duration-300 transform ${
                  isOpen ? "rotate-45 translate-y-1" : "-translate-y-1"
                }`}
              />
              <span
                className={`w-3.5 h-0.5 bg-current transition-all duration-300 transform ${
                  isOpen ? "-rotate-45 -translate-y-0.5" : "translate-y-1"
                }`}
              />
            </div>
            <span>{isOpen ? "CLOSE" : "MENU"}</span>
          </button>
        </div>
      </header>

      {/* ================= NIKE EXPANDABLE FULL-SCREEN OVERLAY & CITY TOUR DATA DISPLAY ================= */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, clipPath: "polygon(0 0, 100% 0, 100% 0, 0 0)" }}
            animate={{ opacity: 1, clipPath: "polygon(0 0, 100% 0, 100% 100%, 0 100%)" }}
            exit={{ opacity: 0, clipPath: "polygon(0 0, 100% 0, 100% 0, 0 0)" }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-0 z-40 bg-[#F9F7EF]/98 dark:bg-black/98 backdrop-blur-2xl text-black dark:text-[#F9F7EF] flex flex-col justify-between pt-20 sm:pt-24 pb-8 sm:pb-12 px-6 sm:px-12 md:px-16 overflow-y-auto selection:bg-red-600 selection:text-white"
          >
            {/* Top Subtitle Bar */}
            <div className="flex items-center justify-between py-3 border-b border-neutral-300 dark:border-neutral-800 text-xs font-mono font-bold text-neutral-500">
              <div className="flex items-center gap-2">
                <Globe className="w-3.5 h-3.5 text-red-600" />
                <span className="uppercase tracking-widest">
                  ISHA AUTONOMOUS SWE HARNESS // SYSTEM NAVIGATION
                </span>
              </div>
              <span className="hidden sm:inline font-mono text-red-600 dark:text-red-500">
                {timeString || "UTC LIVE"}
              </span>
            </div>

            {/* Main Interactive Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center my-auto py-8">
              {/* Left Column: Giant Bold Athletic Nike Navigation Menu */}
              <div className="lg:col-span-7 flex flex-col justify-center space-y-1 sm:space-y-2">
                {navItems.map((item, index) => {
                  const isHovered = hoveredIndex === index;
                  return (
                    <a
                      key={item.id}
                      href={item.href}
                      target={item.isExternal ? "_blank" : undefined}
                      rel={item.isExternal ? "noreferrer" : undefined}
                      onMouseEnter={() => setHoveredIndex(index)}
                      onClick={() => !item.isExternal && setIsOpen(false)}
                      className={`group flex items-center justify-between py-2 sm:py-3 border-b transition-all duration-300 ${
                        isHovered
                          ? "border-red-600"
                          : "border-neutral-300/40 dark:border-neutral-800/80"
                      }`}
                    >
                      <div className="flex items-baseline gap-4 sm:gap-6">
                        <span className="font-mono text-xs sm:text-sm font-black text-red-600 dark:text-red-500">
                          {item.number}
                        </span>
                        <div className="flex flex-col">
                          <span className="text-3xl sm:text-5xl md:text-6xl font-black uppercase tracking-tighter text-black dark:text-[#F9F7EF] group-hover:text-red-600 group-hover:translate-x-3 transition-all duration-300 leading-none">
                            {item.name}
                          </span>
                          <span className="font-mono text-[10px] sm:text-xs text-neutral-500 dark:text-neutral-400 font-bold uppercase tracking-wider mt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                            {item.sub}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {item.isExternal ? (
                          <ArrowUpRight className="w-6 h-6 stroke-[3] text-red-600 group-hover:scale-125 transition-transform" />
                        ) : (
                          <span className="hidden sm:inline-block w-2.5 h-2.5 rounded-full bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                        )}
                      </div>
                    </a>
                  );
                })}
              </div>

              {/* Right Column: Signature Nike City Tour Data Display */}
              <div className="lg:col-span-5 flex flex-col justify-center">
                <div className="p-6 sm:p-8 rounded-3xl bg-neutral-200/60 dark:bg-neutral-900/70 border border-neutral-300 dark:border-neutral-800 shadow-2xl shadow-neutral-900/10 dark:shadow-black/80 space-y-6">
                  {/* Card Header with Live Beacon */}
                  <div className="flex items-center justify-between pb-3 border-b border-neutral-300 dark:border-neutral-800">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-red-600 animate-ping" />
                      <span className="font-mono text-xs uppercase tracking-widest text-black dark:text-[#F9F7EF] font-black">
                        CITY TOUR DATA DISPLAY
                      </span>
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full bg-red-600/10 text-red-600 dark:text-red-500 font-mono text-[10px] font-black">
                      {activeItem.status}
                    </span>
                  </div>

                  {/* Active City Node Spotlight */}
                  <div className="space-y-2">
                    <span className="text-[11px] font-mono text-neutral-500 uppercase tracking-widest block font-bold">
                      ACTIVE TOUR NODE
                    </span>
                    <h3 className="text-3xl sm:text-4xl font-black uppercase tracking-tight text-red-600">
                      {activeItem.city}
                    </h3>
                    <p className="font-mono text-xs text-neutral-600 dark:text-neutral-400 font-bold">
                      {activeItem.region} · {activeItem.metric}
                    </p>
                  </div>

                  {/* Complete 6-Node Tour Itinerary */}
                  <div className="space-y-2 pt-2 border-t border-neutral-300 dark:border-neutral-800">
                    <span className="text-[10px] font-mono uppercase tracking-widest text-neutral-400 block font-bold">
                      ALL SYSTEM TOUR STOPS
                    </span>
                    <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                      {navItems.map((n, idx) => (
                        <div
                          key={n.id}
                          className={`p-2 rounded-xl transition-all ${
                            hoveredIndex === idx
                              ? "bg-red-600 text-white font-black shadow-md"
                              : "bg-neutral-300/40 dark:bg-neutral-800/40 text-neutral-700 dark:text-neutral-300"
                          }`}
                        >
                          <div className="flex items-center justify-between text-[10px]">
                            <span>{n.number}</span>
                            <span>{n.status}</span>
                          </div>
                          <span className="font-black truncate block mt-0.5">
                            {n.city}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Active Section Summary Footer */}
                  <div className="pt-3 border-t border-neutral-300 dark:border-neutral-800 text-xs font-mono text-neutral-600 dark:text-neutral-400">
                    <span className="text-red-600 font-bold mr-1.5">SPECS:</span>
                    <span>{activeItem.sub}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Telemetry Footer */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-neutral-300 dark:border-neutral-800 text-xs font-mono text-neutral-500 font-bold">
              <div className="flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-red-600" />
                <span>ISHA AUTONOMOUS SWE HARNESS // RELEASE CRITERIA 25/25 VERIFIED</span>
              </div>
              <div className="flex items-center gap-6">
                <span>SWE-BENCH LITE N=30 AUDITED</span>
                <span className="text-red-600 dark:text-red-500">MIT LICENSE</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export const DemoSkiper13: React.FC = () => {
  return (
    <section className="relative h-full bg-black">
      <Navbar_001 />
    </section>
  );
};

export default DemoSkiper13;
