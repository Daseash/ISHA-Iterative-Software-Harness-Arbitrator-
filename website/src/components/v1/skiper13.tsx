import React, { useState, useEffect } from "react";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ThemeToggleButton1 } from "./skiper4";
import { TextRoll } from "./skiper58";

interface NavItem {
  name: string;
  href: string;
  isExternal?: boolean;
}

const navItems: NavItem[] = [
  { name: "Home", href: "#hero" },
  { name: "About", href: "#about" },
  { name: "CLI", href: "#cli" },
  { name: "Fix", href: "#fix" },
  { name: "STATS", href: "#stats" },
  {
    name: "GIT HUB",
    href: "https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-",
    isExternal: true,
  },
];

export const Navbar_001: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      // Toggle navbar style once scrolled past hero image
      setIsScrolled(window.scrollY > window.innerHeight * 0.7);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close mobile menu on Esc key or resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) setMobileMenuOpen(false);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-5 py-4 sm:px-8 sm:py-5 md:px-12 transition-all duration-300 font-black ${
          isScrolled
            ? "bg-[#F9F7EF]/90 dark:bg-black/90 backdrop-blur-md shadow-md shadow-black/5 dark:shadow-black/70 text-black dark:text-[#F9F7EF]"
            : "bg-transparent text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)]"
        }`}
      >
        {/* Brand / Logo */}
        <div className="flex items-center gap-6">
          <a
            href="#hero"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2.5 group"
          >
            <div className="h-3.5 w-3.5 rounded-full bg-red-600 transition-transform group-hover:scale-125 duration-300 shadow-sm shrink-0" />
            <span
              className={`text-xl sm:text-2xl font-black tracking-tighter transition-colors ${
                isScrolled ? "text-black dark:text-[#F9F7EF]" : "text-white"
              }`}
            >
              ISHA
            </span>
          </a>

          {/* Desktop Nav Links (hidden on mobile/tablet) */}
          <nav className="hidden lg:flex items-center gap-7 text-xs font-mono uppercase tracking-widest font-black pl-6">
            {navItems.map((item) => (
              <a
                key={item.name}
                href={item.href}
                target={item.isExternal ? "_blank" : undefined}
                rel={item.isExternal ? "noreferrer" : undefined}
                className={`hover:text-red-500 transition-colors inline-flex items-center gap-1 group font-black ${
                  isScrolled ? "text-black dark:text-[#F9F7EF]" : "text-white"
                }`}
              >
                <TextRoll
                  className={`text-xs font-mono uppercase tracking-widest font-black ${
                    isScrolled ? "text-black dark:text-[#F9F7EF]" : "text-white"
                  }`}
                >
                  {item.name}
                </TextRoll>
                {item.isExternal && (
                  <ArrowUpRight className="w-3.5 h-3.5 stroke-[3] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                )}
              </a>
            ))}
          </nav>
        </div>

        {/* Right Corner: Theme Toggle Button & Mobile Menu Hamburger */}
        <div className="flex items-center gap-2 sm:gap-3">
          <ThemeToggleButton1
            className={`h-9 px-3 sm:h-10 sm:px-5 shadow-lg transition-all ${
              isScrolled
                ? "bg-neutral-200/80 dark:bg-neutral-800 text-black dark:text-[#F9F7EF]"
                : "bg-black/30 hover:bg-black/50 text-white backdrop-blur-md"
            }`}
          />

          {/* Mobile Hamburger Toggle (hidden on desktop) */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle Navigation Menu"
            className={`lg:hidden flex items-center justify-center h-9 w-9 sm:h-10 sm:w-10 rounded-xl transition-all cursor-pointer ${
              isScrolled
                ? "bg-neutral-200/80 dark:bg-neutral-800 text-black dark:text-[#F9F7EF]"
                : "bg-black/30 hover:bg-black/50 text-white backdrop-blur-md"
            }`}
          >
            {mobileMenuOpen ? (
              <X className="w-5 h-5 stroke-[2.5]" />
            ) : (
              <Menu className="w-5 h-5 stroke-[2.5]" />
            )}
          </button>
        </div>
      </header>

      {/* Mobile Fullscreen Animated Menu Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="fixed inset-0 z-40 lg:hidden flex flex-col justify-between pt-24 pb-12 px-6 sm:px-10 bg-[#F9F7EF]/95 dark:bg-black/95 backdrop-blur-2xl text-black dark:text-[#F9F7EF] font-black"
          >
            {/* Nav list */}
            <div className="flex flex-col space-y-4 my-auto">
              <span className="text-[11px] font-mono uppercase tracking-[0.3em] text-neutral-400 font-bold mb-2">
                Navigation
              </span>
              {navItems.map((item, index) => (
                <motion.a
                  key={item.name}
                  href={item.href}
                  target={item.isExternal ? "_blank" : undefined}
                  rel={item.isExternal ? "noreferrer" : undefined}
                  onClick={() => setMobileMenuOpen(false)}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05, duration: 0.2 }}
                  className="flex items-center justify-between text-3xl sm:text-4xl font-black uppercase tracking-tight py-2 border-b border-neutral-300/40 dark:border-neutral-800/80 hover:text-red-600 transition-colors group"
                >
                  <span className="group-hover:translate-x-2 transition-transform duration-200">
                    {item.name}
                  </span>
                  {item.isExternal && (
                    <ArrowUpRight className="w-6 h-6 stroke-[3] text-red-600" />
                  )}
                </motion.a>
              ))}
            </div>

            {/* Bottom info */}
            <div className="pt-6 border-t border-neutral-300 dark:border-neutral-800 text-xs font-mono text-neutral-500 flex items-center justify-between">
              <span>ISHA AUTONOMOUS HARNESS</span>
              <span className="text-red-600 font-bold">V0.3.0</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default Navbar_001;
