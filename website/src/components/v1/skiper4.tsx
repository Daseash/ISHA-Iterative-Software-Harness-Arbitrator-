import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { sounds } from "../../utils/sound";

interface ThemeToggleProps {
  className?: string;
  onToggle?: (isDark: boolean) => void;
}

export const ThemeToggleButton1: React.FC<ThemeToggleProps> = ({
  className = "",
  onToggle,
}) => {
  const [isDark, setIsDark] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("theme");
      if (saved) return saved === "dark";
      return document.documentElement.classList.contains("dark");
    }
    return false;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
    if (onToggle) onToggle(isDark);
  }, [isDark, onToggle]);

  const toggleTheme = () => {
    sounds.playSwitch();
    setIsDark((prev) => !prev);
  };

  const raysVariants = {
    light: {
      scale: 1,
      opacity: 1,
      rotate: 0,
      transition: { duration: 0.35, ease: "easeOut" as const },
    },
    dark: {
      scale: 0,
      opacity: 0,
      rotate: 90,
      transition: { duration: 0.25, ease: "easeIn" as const },
    },
  };

  const centerCircleVariants = {
    light: {
      r: 5,
      transition: { duration: 0.35, ease: "easeOut" as const },
    },
    dark: {
      r: 8.5,
      transition: { duration: 0.35, ease: "easeOut" as const },
    },
  };

  const maskCircleVariants = {
    light: {
      cx: 24,
      cy: 6,
      r: 0,
      transition: { duration: 0.35, ease: "easeOut" as const },
    },
    dark: {
      cx: 17.5,
      cy: 7.5,
      r: 7.5,
      transition: { duration: 0.35, ease: "easeOut" as const },
    },
  };

  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle theme"
      className={`relative flex items-center justify-center h-10 px-5 rounded-full bg-neutral-200/80 dark:bg-neutral-800 text-black dark:text-[#F9F7EF] hover:scale-105 active:scale-95 transition-all duration-300 cursor-pointer shadow-md ${className}`}
    >
      <motion.svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="w-5 h-5"
        animate={{ rotate: isDark ? 40 : 0 }}
        transition={{ duration: 0.4, ease: "easeInOut" }}
      >
        <mask id="theme-toggle-mask-1">
          <rect x="0" y="0" width="24" height="24" fill="white" />
          <motion.circle
            animate={isDark ? "dark" : "light"}
            variants={maskCircleVariants}
            fill="black"
          />
        </mask>

        {/* Center Sun / Moon Body */}
        <motion.circle
          cx="12"
          cy="12"
          animate={isDark ? "dark" : "light"}
          variants={centerCircleVariants}
          fill="currentColor"
          mask="url(#theme-toggle-mask-1)"
        />

        {/* Sun Rays */}
        <motion.g
          animate={isDark ? "dark" : "light"}
          variants={raysVariants}
          stroke="currentColor"
          strokeWidth="2.5"
        >
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </motion.g>
      </motion.svg>
    </button>
  );
};

export default ThemeToggleButton1;
