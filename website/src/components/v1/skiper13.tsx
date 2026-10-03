import React, { useState, useEffect } from "react";
import { ArrowUpRight } from "lucide-react";
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

  useEffect(() => {
    const handleScroll = () => {
      // Toggle navbar style once scrolled past hero image
      setIsScrolled(window.scrollY > window.innerHeight * 0.7);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-5 md:px-12 transition-all duration-300 font-black ${
        isScrolled
          ? "bg-[#F9F7EF]/90 dark:bg-black/90 backdrop-blur-md shadow-md shadow-black/5 dark:shadow-black/70 text-black dark:text-[#F9F7EF]"
          : "bg-transparent text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)]"
      }`}
    >
      {/* Brand / Logo */}
      <div className="flex items-center gap-6">
        <a href="#hero" className="flex items-center gap-3 group">
          <div className="h-3.5 w-3.5 rounded-full bg-red-600 transition-transform group-hover:scale-125 duration-300 shadow-sm" />
          <span
            className={`text-2xl font-black tracking-tighter transition-colors ${
              isScrolled ? "text-black dark:text-[#F9F7EF]" : "text-white"
            }`}
          >
            ISHA
          </span>
        </a>

        {/* Nav Links */}
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

      {/* Right Corner: Theme Toggle Button in place of Menu Button (no text, clean shadow) */}
      <div className="flex items-center">
        <ThemeToggleButton1
          className={`h-10 px-5 shadow-lg transition-all ${
            isScrolled
              ? "bg-neutral-200/80 dark:bg-neutral-800 text-black dark:text-[#F9F7EF]"
              : "bg-black/30 hover:bg-black/50 text-white backdrop-blur-md"
          }`}
        />
      </div>
    </header>
  );
};

export default Navbar_001;
