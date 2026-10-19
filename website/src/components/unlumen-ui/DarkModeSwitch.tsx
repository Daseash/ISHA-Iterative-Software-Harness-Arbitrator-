import React, { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";
import { Switch } from "./switch";
import { sounds } from "../../utils/sound";
import { cn } from "../../lib/utils";

export interface DarkModeSwitchProps {
  className?: string;
  showIcons?: boolean;
  showLabel?: boolean;
  onToggle?: (isDark: boolean) => void;
}

export const DarkModeSwitch: React.FC<DarkModeSwitchProps> = ({
  className = "",
  showIcons = true,
  showLabel = false,
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

  const handleCheckedChange = (checked: boolean) => {
    sounds.playSwitch();
    setIsDark(checked);
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-full",
        "bg-neutral-900/90 dark:bg-neutral-950/90 backdrop-blur-md",
        "border border-neutral-800 dark:border-neutral-800/80 shadow-lg shadow-black/20",
        "transition-all duration-200 select-none",
        className,
      )}
    >
      {showIcons && (
        <Sun
          className={cn(
            "w-3.5 h-3.5 transition-colors duration-200",
            !isDark ? "text-amber-400 drop-shadow-[0_0_6px_rgba(251,191,36,0.5)]" : "text-neutral-500",
          )}
        />
      )}

      <Switch
        checked={isDark}
        onCheckedChange={handleCheckedChange}
        aria-label="Toggle dark mode"
      />

      {showIcons && (
        <Moon
          className={cn(
            "w-3.5 h-3.5 transition-colors duration-200",
            isDark ? "text-indigo-400 drop-shadow-[0_0_6px_rgba(129,140,248,0.5)]" : "text-neutral-500",
          )}
        />
      )}

      {showLabel && (
        <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-neutral-300 dark:text-neutral-400 pl-1">
          {isDark ? "Dark" : "Light"}
        </span>
      )}
    </div>
  );
};

export default DarkModeSwitch;
