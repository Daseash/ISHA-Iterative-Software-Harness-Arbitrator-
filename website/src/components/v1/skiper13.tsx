import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useEventListener } from "usehooks-ts";
import { ThemeToggleButton1 } from "./skiper4";

export interface NavItem {
  name: string;
  href: string;
  badge?: string;
  isExternal?: boolean;
}

export interface NavbarProps {
  hideStats?: boolean;
  hideGithub?: boolean;
  position?: "auto" | "left" | "center" | "right";
  showThemeToggle?: boolean;
  className?: string;
}

export const Navbar_001: React.FC<NavbarProps> = ({
  hideStats = false,
  hideGithub = false,
  position = "auto",
  showThemeToggle = false,
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  const navItems: NavItem[] = [
    { name: "HOME", href: "/#hero", badge: "01" },
    { name: "ABOUT", href: "/#about", badge: "02" },
    { name: "CLI", href: "/#cli", badge: "03" },
    { name: "FIX", href: "/fix", badge: "04" },
    ...(!hideStats ? [{ name: "STATS", href: "/stats", badge: "05" }] : []),
    ...(!hideGithub
      ? [
          {
            name: "GIT HUB",
            href: "https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-",
            badge: "↗",
            isExternal: true,
          },
        ]
      : []),
  ];

  // Scroll listener to move bar to top-left corner when scrolling
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close on Escape key
  useEventListener("keydown", (event: KeyboardEvent) => {
    if (event.key === "Escape" && isOpen) {
      setIsOpen(false);
    }
  });

  return (
    <>
      {/* Semi-transparent backdrop when menu is open: matches website background (#F9F7EF in light, black in dark) */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setIsOpen(false)}
            className="fixed inset-0 z-40 bg-[#F9F7EF]/80 dark:bg-black/80 backdrop-blur-sm"
          />
        )}
      </AnimatePresence>

      {/* Floating Pill Nav Bar: Centered at top, slowly moves to top-left corner on scroll (or pinned to left/right) */}
      {/* Background: Black in Light Mode, #F9F7EF in Dark Mode */}
      <motion.div
        initial={
          position === "left"
            ? { left: "clamp(1rem, 3vw, 2.5rem)", right: "auto", x: "0%" }
            : position === "right"
            ? { right: "clamp(1rem, 3vw, 2.5rem)", left: "auto", x: "0%" }
            : position === "center"
            ? { left: "50%", right: "auto", x: "-50%" }
            : false
        }
        animate={
          position === "right"
            ? { right: "clamp(1rem, 3vw, 2.5rem)", left: "auto", x: "0%" }
            : {
                left:
                  position === "left" || (position === "auto" && isScrolled)
                    ? "clamp(1rem, 3vw, 2.5rem)"
                    : "50%",
                right: "auto",
                x:
                  position === "left" || (position === "auto" && isScrolled)
                    ? "0%"
                    : "-50%",
              }
        }
        transition={{
          duration: 0.85,
          ease: [0.16, 1, 0.3, 1],
        }}
        className={`fixed top-5 sm:top-6 z-50 select-none ${className}`}
      >
        <motion.div
          layout
          transition={{
            type: "spring",
            stiffness: 380,
            damping: 32,
          }}
          className={`overflow-hidden border border-neutral-800 dark:border-neutral-300/80 bg-neutral-950/95 dark:bg-[#F9F7EF]/95 text-white dark:text-neutral-900 backdrop-blur-2xl shadow-2xl shadow-black/20 dark:shadow-black/60 transition-colors duration-300 ${
            isOpen
              ? "w-[310px] sm:w-[350px] rounded-3xl p-5"
              : "w-[270px] sm:w-[310px] rounded-2xl px-5 py-3"
          }`}
        >
          {/* Top Bar: Always has our exact top-left ISHA logo + MENU / CLOSE button */}
          <div className="flex items-center justify-between w-full">
            <a
              href="/"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2.5 group cursor-pointer"
            >
              <div className="h-3 w-3 rounded-full bg-red-600 transition-transform group-hover:scale-125 duration-300 shadow-sm shrink-0" />
              <span className="text-lg sm:text-xl font-black tracking-tighter uppercase text-white dark:text-neutral-900 group-hover:text-red-500 transition-colors">
                ISHA
              </span>
            </a>

            <button
              type="button"
              onClick={() => setIsOpen(!isOpen)}
              className="font-mono text-xs font-black uppercase tracking-widest text-neutral-400 dark:text-neutral-600 hover:text-red-500 dark:hover:text-red-600 transition-colors cursor-pointer py-1 px-2 rounded-lg"
            >
              {isOpen ? "CLOSE" : "MENU"}
            </button>
          </div>

          {/* Expanded Menu Content: Shown when MENU is pressed */}
          <AnimatePresence>
            {isOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
                className="flex flex-col space-y-6 pt-5"
              >
                {/* Vertical Stacked Navigation Links in Bold Red Nike Typography */}
                <nav className="flex flex-col items-center justify-center space-y-2 py-3">
                  {navItems.map((item, idx) => (
                    <motion.a
                      key={item.name}
                      href={item.href}
                      target={item.isExternal ? "_blank" : undefined}
                      rel={item.isExternal ? "noreferrer" : undefined}
                      onClick={() => {
                        if (!item.isExternal) setIsOpen(false);
                      }}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.04, duration: 0.2 }}
                      className="group relative flex items-baseline justify-center gap-1.5 transition-transform duration-200 hover:scale-105 active:scale-95"
                    >
                      <span className="text-2xl sm:text-3xl font-black uppercase tracking-tight text-red-600 group-hover:text-red-500 dark:group-hover:text-red-500 transition-colors leading-none">
                        {item.name}
                      </span>
                      {item.badge && (
                        <span className="font-mono text-[9px] sm:text-[10px] text-red-400 dark:text-red-600 font-bold opacity-80 group-hover:opacity-100">
                          {item.badge}
                        </span>
                      )}
                    </motion.a>
                  ))}
                </nav>

                {/* Sub-links row */}
                <div className="flex items-center justify-between pt-3 border-t border-neutral-800 dark:border-neutral-300 text-[11px] font-mono text-neutral-400 dark:text-neutral-500 font-bold px-2">
                  <a
                    href="https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-#-architecture"
                    target="_blank"
                    rel="noreferrer"
                    className="hover:text-white dark:hover:text-neutral-900 transition-colors"
                  >
                    Architecture
                  </a>
                  <a
                    href="https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-/blob/main/LICENSE"
                    target="_blank"
                    rel="noreferrer"
                    className="hover:text-white dark:hover:text-neutral-900 transition-colors"
                  >
                    MIT License
                  </a>
                </div>

                {/* Bottom Segmented Pill Row: PB | EN | ES | FR style */}
                <div className="grid grid-cols-4 gap-1 p-1 rounded-xl bg-neutral-900/90 dark:bg-neutral-200/80 border border-neutral-800 dark:border-neutral-300/80 text-center font-mono text-[10px] font-black uppercase text-neutral-400 dark:text-neutral-600">
                  <span className="py-1 rounded-lg bg-red-600 text-white shadow-sm">
                    SWE
                  </span>
                  <span className="py-1 hover:text-white dark:hover:text-neutral-900 transition-colors">
                    AST
                  </span>
                  <span className="py-1 hover:text-white dark:hover:text-neutral-900 transition-colors">
                    TDD
                  </span>
                  <span className="py-1 hover:text-white dark:hover:text-neutral-900 transition-colors">
                    V0.3
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </motion.div>

      {/* Skiper4 Theme Toggle Button 1: Rendered ONLY on Home Page */}
      {showThemeToggle && (
        <div className="fixed top-5 sm:top-6 right-4 sm:right-8 z-50">
          <ThemeToggleButton1 className="size-11 sm:size-12" />
        </div>
      )}
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
