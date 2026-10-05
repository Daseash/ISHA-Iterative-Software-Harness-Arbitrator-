import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useEventListener } from "usehooks-ts";
import { ThemeToggleButton1 } from "./skiper4";

interface NavItem {
  name: string;
  href: string;
  badge?: string;
  isExternal?: boolean;
}

const navItems: NavItem[] = [
  { name: "HOME", href: "#hero", badge: "01" },
  { name: "ABOUT", href: "#about", badge: "02" },
  { name: "CLI", href: "#cli", badge: "03" },
  { name: "FIX", href: "#fix", badge: "04" },
  { name: "STATS", href: "#stats", badge: "05" },
  {
    name: "GIT HUB",
    href: "https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-",
    badge: "↗",
    isExternal: true,
  },
];

export const Navbar_001: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  // Close on Escape key
  useEventListener("keydown", (event: KeyboardEvent) => {
    if (event.key === "Escape" && isOpen) {
      setIsOpen(false);
    }
  });

  return (
    <>
      {/* Semi-transparent backdrop when menu is open */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setIsOpen(false)}
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          />
        )}
      </AnimatePresence>

      {/* Floating Pill Nav Bar in Top-Center (Exact Nike Menu style from screenshot) */}
      <div className="fixed top-5 sm:top-6 left-1/2 -translate-x-1/2 z-50 select-none">
        <motion.div
          layout
          transition={{
            type: "spring",
            stiffness: 380,
            damping: 32,
          }}
          className={`overflow-hidden border border-neutral-800/80 bg-neutral-900/90 dark:bg-black/90 text-white backdrop-blur-2xl shadow-2xl shadow-black/60 transition-colors ${
            isOpen
              ? "w-[310px] sm:w-[350px] rounded-3xl p-5"
              : "w-[270px] sm:w-[310px] rounded-2xl px-5 py-3"
          }`}
        >
          {/* Top Bar: Always has our exact top-left ISHA logo + MENU / CLOSE button */}
          <div className="flex items-center justify-between w-full">
            <a
              href="#hero"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2.5 group cursor-pointer"
            >
              <div className="h-3 w-3 rounded-full bg-red-600 transition-transform group-hover:scale-125 duration-300 shadow-sm shrink-0" />
              <span className="text-lg sm:text-xl font-black tracking-tighter uppercase text-white group-hover:text-red-500 transition-colors">
                ISHA
              </span>
            </a>

            <button
              type="button"
              onClick={() => setIsOpen(!isOpen)}
              className="font-mono text-xs font-black uppercase tracking-widest text-neutral-300 hover:text-red-500 transition-colors cursor-pointer py-1 px-2 rounded-lg"
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
                      <span className="text-2xl sm:text-3xl font-black uppercase tracking-tight text-red-600 group-hover:text-red-500 transition-colors leading-none">
                        {item.name}
                      </span>
                      {item.badge && (
                        <span className="font-mono text-[9px] sm:text-[10px] text-red-400 font-bold opacity-80 group-hover:opacity-100">
                          {item.badge}
                        </span>
                      )}
                    </motion.a>
                  ))}
                </nav>

                {/* Sub-links row */}
                <div className="flex items-center justify-between pt-3 border-t border-neutral-800 text-[11px] font-mono text-neutral-400 font-bold px-2">
                  <a
                    href="https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-#-architecture"
                    target="_blank"
                    rel="noreferrer"
                    className="hover:text-white transition-colors"
                  >
                    Architecture
                  </a>
                  <a
                    href="https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-/blob/main/LICENSE"
                    target="_blank"
                    rel="noreferrer"
                    className="hover:text-white transition-colors"
                  >
                    MIT License
                  </a>
                </div>

                {/* Bottom Segmented Pill Row: Exactly matching PB | EN | ES | FR from screenshot */}
                <div className="grid grid-cols-4 gap-1 p-1 rounded-xl bg-neutral-950/80 border border-neutral-800/80 text-center font-mono text-[10px] font-black uppercase text-neutral-400">
                  <span className="py-1 rounded-lg bg-red-600 text-white shadow-sm">
                    SWE
                  </span>
                  <span className="py-1 hover:text-white transition-colors">
                    AST
                  </span>
                  <span className="py-1 hover:text-white transition-colors">
                    TDD
                  </span>
                  <span className="py-1 hover:text-white transition-colors">
                    V0.3
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Theme Toggle Button: Floating in Top-Right Corner */}
      <div className="fixed top-5 sm:top-6 right-4 sm:right-8 z-50">
        <ThemeToggleButton1 className="h-10 px-4 rounded-full border border-neutral-300 dark:border-neutral-800 bg-[#F9F7EF]/90 dark:bg-black/90 backdrop-blur-md shadow-lg text-black dark:text-[#F9F7EF]" />
      </div>
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
