"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { GripHorizontal, RefreshCcw } from "lucide-react";
import { cn } from "../../lib/utils";
import { sounds } from "../../utils/sound";

export interface ThemeToggleProps {
  className?: string;
  onToggle?: (isDark: boolean) => void;
}

//..................................................... //
// Theme Toggle Button 1 (Yin-Yang Contrast Rotate - Used on Home Page)
//..................................................... //
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

  const handleToggle = () => {
    sounds.playSwitch();
    setIsDark((prev) => !prev);
  };

  return (
    <button
      type="button"
      aria-label="Toggle theme"
      title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
      className={cn(
        "rounded-full bg-black text-white transition-all duration-300 active:scale-95 shadow-xl shadow-black/30 border border-neutral-800 hover:scale-105 cursor-pointer flex items-center justify-center p-2 select-none",
        className,
      )}
      onClick={handleToggle}
    >
      <svg
        viewBox="0 0 240 240"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        <motion.g
          animate={{ rotate: isDark ? -180 : 0 }}
          transition={{ ease: "easeInOut", duration: 0.35 }}
          style={{ originX: "120px", originY: "120px" }}
        >
          <path
            d="M120 67.5C149.25 67.5 172.5 90.75 172.5 120C172.5 149.25 149.25 172.5 120 172.5"
            fill="white"
          />
          <path
            d="M120 67.5C90.75 67.5 67.5 90.75 67.5 120C67.5 149.25 90.75 172.5 120 172.5"
            fill="black"
          />
        </motion.g>
        <motion.path
          animate={{ rotate: isDark ? 180 : 0 }}
          transition={{ ease: "easeInOut", duration: 0.35 }}
          style={{ originX: "120px", originY: "120px" }}
          d="M120 3.75C55.5 3.75 3.75 55.5 3.75 120C3.75 184.5 55.5 236.25 120 236.25C184.5 236.25 236.25 184.5 236.25 120C236.25 55.5 184.5 3.75 120 3.75ZM120 214.5V172.5C90.75 172.5 67.5 149.25 67.5 120C67.5 90.75 90.75 67.5 120 67.5V25.5C172.5 25.5 214.5 67.5 214.5 120C214.5 172.5 172.5 214.5 120 214.5Z"
          fill="white"
        />
      </svg>
    </button>
  );
};

//..................................................... //
// Theme Toggle Button 2 (Moon Eclipse ClipPath)
//..................................................... //
export const ThemeToggleButton2: React.FC<ThemeToggleProps> = ({
  className = "",
  onToggle,
}) => {
  const [isDark, setIsDark] = useState(false);
  const handleToggle = () => {
    sounds.playSwitch();
    setIsDark(!isDark);
    if (onToggle) onToggle(!isDark);
  };
  return (
    <button
      type="button"
      className={cn(
        "rounded-full transition-all duration-300 active:scale-95 cursor-pointer",
        isDark ? "bg-black text-white" : "bg-white text-black",
        className,
      )}
      onClick={handleToggle}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        fill="currentColor"
        strokeLinecap="round"
        viewBox="0 0 32 32"
        className="w-full h-full"
      >
        <clipPath id="skiper-btn-2">
          <motion.path
            animate={{ y: isDark ? 10 : 0, x: isDark ? -12 : 0 }}
            transition={{ ease: "easeInOut", duration: 0.35 }}
            d="M0-5h30a1 1 0 0 0 9 13v24H0Z"
          />
        </clipPath>
        <g clipPath="url(#skiper-btn-2)">
          <motion.circle
            animate={{ r: isDark ? 10 : 8 }}
            transition={{ ease: "easeInOut", duration: 0.35 }}
            cx="16"
            cy="16"
          />
          <motion.g
            animate={{
              rotate: isDark ? -100 : 0,
              scale: isDark ? 0.5 : 1,
              opacity: isDark ? 0 : 1,
            }}
            transition={{ ease: "easeInOut", duration: 0.35 }}
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="M16 5.5v-4" />
            <path d="M16 30.5v-4" />
            <path d="M1.5 16h4" />
            <path d="M26.5 16h4" />
            <path d="m23.4 8.6 2.8-2.8" />
            <path d="m5.7 26.3 2.9-2.9" />
            <path d="m5.8 5.8 2.8 2.8" />
            <path d="m23.4 23.4 2.9 2.9" />
          </motion.g>
        </g>
      </svg>
    </button>
  );
};

//..................................................... //
// Theme Toggle Button 3 (Sun Dots Expand)
//..................................................... //
export const ThemeToggleButton3: React.FC<ThemeToggleProps> = ({
  className = "",
  onToggle,
}) => {
  const [isDark, setIsDark] = useState(false);
  const handleToggle = () => {
    sounds.playSwitch();
    setIsDark(!isDark);
    if (onToggle) onToggle(!isDark);
  };
  return (
    <button
      type="button"
      className={cn(
        "rounded-full transition-all duration-300 active:scale-95 cursor-pointer",
        isDark ? "bg-black text-white" : "bg-white text-black",
        className,
      )}
      onClick={handleToggle}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        fill="currentColor"
        strokeLinecap="round"
        viewBox="0 0 32 32"
        className="w-full h-full"
      >
        <clipPath id="skiper-btn-3">
          <motion.path
            animate={{ y: isDark ? 14 : 0, x: isDark ? -11 : 0 }}
            transition={{ ease: "easeInOut", duration: 0.35 }}
            d="M0-11h25a1 1 0 0017 13v30H0Z"
          />
        </clipPath>
        <g clipPath="url(#skiper-btn-3)">
          <motion.circle
            animate={{ r: isDark ? 10 : 8 }}
            transition={{ ease: "easeInOut", duration: 0.35 }}
            cx="16"
            cy="16"
          />
          <motion.g
            animate={{
              scale: isDark ? 0.5 : 1,
              opacity: isDark ? 0 : 1,
            }}
            transition={{ ease: "easeInOut", duration: 0.35 }}
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="M18.3 3.2c0 1.3-1 2.3-2.3 2.3s-2.3-1-2.3-2.3S14.7.9 16 .9s2.3 1 2.3 2.3zm-4.6 25.6c0-1.3 1-2.3 2.3-2.3s2.3 1 2.3 2.3-1 2.3-2.3 2.3-2.3-1-2.3-2.3zm15.1-10.5c-1.3 0-2.3-1-2.3-2.3s1-2.3 2.3-2.3 2.3 1 2.3 2.3-1 2.3-2.3 2.3zM3.2 13.7c1.3 0 2.3 1 2.3 2.3s-1 2.3-2.3 2.3S.9 17.3.9 16s1-2.3 2.3-2.3zm5.8-7C9 7.9 7.9 9 6.7 9S4.4 8 4.4 6.7s1-2.3 2.3-2.3S9 5.4 9 6.7zm16.3 21c-1.3 0-2.3-1-2.3-2.3s1-2.3 2.3-2.3 2.3 1 2.3 2.3-1 2.3-2.3 2.3zm2.4-21c0 1.3-1 2.3-2.3 2.3S23 7.9 23 6.7s1-2.3 2.3-2.3 2.4 1 2.4 2.3zM6.7 23C8 23 9 24 9 25.3s-1 2.3-2.3 2.3-2.3-1-2.3-2.3 1-2.3 2.3-2.3z" />
          </motion.g>
        </g>
      </svg>
    </button>
  );
};

//..................................................... //
// Theme Toggle Button 4 (Lightbulb Filament Wire)
//..................................................... //
export const ThemeToggleButton4: React.FC<ThemeToggleProps> = ({
  className = "",
  onToggle,
}) => {
  const [isDark, setIsDark] = useState(false);
  const handleToggle = () => {
    sounds.playSwitch();
    setIsDark(!isDark);
    if (onToggle) onToggle(!isDark);
  };
  return (
    <button
      type="button"
      className={cn(
        "rounded-full transition-all duration-300 active:scale-95 cursor-pointer",
        isDark ? "bg-black text-white" : "bg-white text-black",
        className,
      )}
      onClick={handleToggle}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        strokeWidth="0.7"
        stroke="currentColor"
        fill="currentColor"
        strokeLinecap="round"
        viewBox="0 0 32 32"
        className="w-full h-full"
      >
        <path
          strokeWidth="0"
          d="M9.4 9.9c1.8-1.8 4.1-2.7 6.6-2.7 5.1 0 9.3 4.2 9.3 9.3 0 2.3-.8 4.4-2.3 6.1-.7.8-2 2.8-2.5 4.4 0 .2-.2.4-.5.4-.2 0-.4-.2-.4-.5v-.1c.5-1.8 2-3.9 2.7-4.8 1.4-1.5 2.1-3.5 2.1-5.6 0-4.7-3.7-8.5-8.4-8.5-2.3 0-4.4.9-5.9 2.5-1.6 1.6-2.5 3.7-2.5 6 0 2.1.7 4 2.1 5.6.8.9 2.2 2.9 2.7 4.9 0 .2-.1.5-.4.5h-.1c-.2 0-.4-.1-.4-.4-.5-1.7-1.8-3.7-2.5-4.5-1.5-1.7-2.3-3.9-2.3-6.1 0-2.3 1-4.7 2.7-6.5z"
        />
        <path d="M19.8 28.3h-7.6" />
        <path d="M19.8 29.5h-7.6" />
        <path d="M19.8 30.7h-7.6" />
        <motion.path
          animate={{
            pathLength: isDark ? 0 : 1,
            opacity: isDark ? 0 : 1,
          }}
          transition={{ ease: "easeInOut", duration: 0.35 }}
          pathLength="1"
          fill="none"
          d="M14.6 27.1c0-3.4 0-6.8-.1-10.2-.2-1-1.1-1.7-2-1.7-1.2-.1-2.3 1-2.2 2.3.1 1 .9 1.9 2.1 2h7.2c1.1-.1 2-1 2.1-2 .1-1.2-1-2.3-2.2-2.3-.9 0-1.7.7-2 1.7 0 3.4 0 6.8-.1 10.2"
        />
        <motion.g
          animate={{
            scale: isDark ? 0.5 : 1,
            opacity: isDark ? 0 : 1,
          }}
          transition={{ ease: "easeInOut", duration: 0.35 }}
        >
          <path pathLength="1" d="M16 6.4V1.3" />
          <path pathLength="1" d="M26.3 15.8h5.1" />
          <path pathLength="1" d="m22.6 9 3.7-3.6" />
          <path pathLength="1" d="M9.4 9 5.7 5.4" />
          <path pathLength="1" d="M5.7 15.8H.6" />
        </motion.g>
      </svg>
    </button>
  );
};

//..................................................... //
// Theme Toggle Button 5 (Slide Horizon)
//..................................................... //
export const ThemeToggleButton5: React.FC<ThemeToggleProps> = ({
  className = "",
  onToggle,
}) => {
  const [isDark, setIsDark] = useState(false);
  const handleToggle = () => {
    sounds.playSwitch();
    setIsDark(!isDark);
    if (onToggle) onToggle(!isDark);
  };
  return (
    <button
      type="button"
      className={cn(
        "rounded-full transition-all duration-300 active:scale-95 cursor-pointer",
        isDark ? "bg-black text-white" : "bg-white text-black",
        className,
      )}
      onClick={handleToggle}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        fill="currentColor"
        viewBox="0 0 32 32"
        className="w-full h-full"
      >
        <clipPath id="skiper-btn-4">
          <motion.path
            animate={{ y: isDark ? 5 : 0, x: isDark ? -20 : 0 }}
            transition={{ ease: "easeInOut", duration: 0.35 }}
            d="M0-5h55v37h-55zm32 12a1 1 0 0025 0 1 1 0 00-25 0"
          />
        </clipPath>
        <g clipPath="url(#skiper-btn-4)">
          <circle cx="16" cy="16" r="15" />
        </g>
      </svg>
    </button>
  );
};

//..................................................... //
// Skiper4 Options Container
//..................................................... //
type OptionsProps = {
  scale: number;
  setScale: (value: number) => void;
  gap: number;
  setGap: (value: number) => void;
  setFlexDirection: (value: string) => void;
};

const Options = ({
  scale,
  setScale,
  gap,
  setGap,
  setFlexDirection,
}: OptionsProps) => {
  const [isDragging, setIsDragging] = useState(false);

  return (
    <motion.div
      className="top-30 border-foreground/10 bg-muted2 absolute right-1/2 flex w-[245px] translate-x-1/2 flex-col gap-3 rounded-3xl border p-3 backdrop-blur-sm lg:right-4 lg:translate-x-0"
      drag={isDragging}
      dragMomentum={false}
    >
      <div className="flex items-center justify-between">
        <span
          onPointerDown={() => setIsDragging(true)}
          onPointerUp={() => setIsDragging(false)}
          className="size-4 cursor-grab active:cursor-grabbing"
        >
          <GripHorizontal className="size-4 opacity-50" />
        </span>

        <p
          onClick={() => {
            setScale(0);
            setGap(0);
            setFlexDirection("row");
          }}
          className="hover:bg-foreground/10 group flex cursor-pointer items-center justify-center gap-2 rounded-lg px-2 py-1 text-sm opacity-50"
        >
          Options
          <span className="group-active:-rotate-360 rotate-0 cursor-pointer transition-all duration-300 group-hover:rotate-90">
            <RefreshCcw className="size-4 opacity-50" />
          </span>{" "}
        </p>
      </div>

      <div className="flex flex-col">
        <div className="flex items-center justify-between py-1">
          <p className="text-sm opacity-50">Scale </p>
          <input
            type="range"
            min={0}
            max={100}
            value={scale}
            onChange={(e) => setScale(Number(e.target.value))}
            className="h-1.5 w-[150px] cursor-pointer appearance-none rounded-lg bg-neutral-300 dark:bg-neutral-700"
          />
        </div>
        <div className="flex items-center justify-between py-1">
          <p className="text-sm opacity-50">Gap </p>
          <input
            type="range"
            min={0}
            max={100}
            value={gap}
            onChange={(e) => setGap(Number(e.target.value))}
            className="h-1.5 w-[150px] cursor-pointer appearance-none rounded-lg bg-neutral-300 dark:bg-neutral-700"
          />
        </div>

        <div className="mt-1 flex items-center justify-between py-1">
          <p className="text-sm opacity-50">Flex </p>
          <div className="flex items-center justify-end gap-2">
            <button
              type="button"
              className="cursor-pointer text-sm opacity-50 hover:opacity-100"
              onClick={() => setFlexDirection("column")}
            >
              coloumn
            </button>
            <button
              type="button"
              className="cursor-pointer text-sm opacity-50 hover:opacity-100"
              onClick={() => setFlexDirection("row")}
            >
              Row
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export const Skiper4 = () => {
  const [scale, setScale] = useState(0);
  const [gap, setGap] = useState(0);
  const [flexDirection, setFlexDirection] = useState("row");

  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-5">
      <motion.div
        className="relative flex items-center justify-center gap-1"
        animate={{
          gap: gap ? `${gap}px` : "4px",
          scale: scale ? `${scale / 20}` : "1",
        }}
        style={{
          flexDirection: flexDirection === "column" ? "column" : "row",
        }}
        transition={{ duration: 0.35 }}
      >
        <motion.div layout>
          <ThemeToggleButton1 className="size-12" />
        </motion.div>
        <motion.div layout>
          <ThemeToggleButton2 className="size-12 p-2" />
        </motion.div>
        <motion.div layout>
          <ThemeToggleButton3 className="size-12 p-2" />
        </motion.div>
        <motion.div layout>
          <ThemeToggleButton4 className="size-12 p-2" />
        </motion.div>
        <motion.div layout>
          <ThemeToggleButton5 className="size-12 p-3" />
        </motion.div>
      </motion.div>

      {/* options */}
      <Options
        scale={scale}
        setScale={setScale}
        gap={gap}
        setGap={setGap}
        setFlexDirection={setFlexDirection}
      />
    </div>
  );
};

export default Skiper4;
