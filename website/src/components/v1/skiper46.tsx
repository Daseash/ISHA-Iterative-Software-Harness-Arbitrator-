"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Clipboard, Check } from "lucide-react";
import { sounds } from "../../utils/sound";

export interface Skiper46Props {
  currentRepo?: string;
  onSelectRepo?: (repo: string) => void;
  className?: string;
}

export const Skiper46: React.FC<Skiper46Props> = ({
  currentRepo = "",
  onSelectRepo,
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [repoInput, setRepoInput] = useState(currentRepo);
  const [connectedRepo, setConnectedRepo] = useState(currentRepo);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setConnectedRepo(currentRepo);
    setRepoInput(currentRepo);
  }, [currentRepo]);

  const cleanRepo = (val: string) => {
    let clean = val.trim();
    clean = clean.replace(/^https?:\/\/(www\.)?github\.com\//, "");
    clean = clean.replace(/\.git$/, "");
    clean = clean.replace(/^\/+|\/+$/g, "");
    return clean;
  };

  const handleConnect = (rawVal: string) => {
    const cleaned = cleanRepo(rawVal);
    if (!cleaned) return;
    setConnectedRepo(cleaned);
    setRepoInput(cleaned);
    sounds.playSuccess();
    if (onSelectRepo) onSelectRepo(cleaned);
    setIsOpen(false);
  };

  const handleClear = () => {
    setConnectedRepo("");
    setRepoInput("");
    sounds.playClick();
    if (onSelectRepo) onSelectRepo("");
  };

  const handlePasteClipboard = async () => {
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        const text = await navigator.clipboard.readText();
        if (text) {
          setRepoInput(text);
          sounds.playClick();
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        }
      }
    } catch {
      // clipboard access fallback
    }
  };

  return (
    <div className={`relative inline-flex flex-col items-center select-none ${className}`}>
      {/* Floating Expandable Card: Matches search bar colors (Light white / Dark neutral-900) */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 14, scale: 0.94 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.94 }}
            transition={{
              type: "spring",
              stiffness: 420,
              damping: 28,
            }}
            className="absolute bottom-14 z-50 w-80 sm:w-96 rounded-2xl bg-white/95 dark:bg-neutral-900/95 text-neutral-900 dark:text-neutral-100 p-4 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 border border-neutral-300 dark:border-neutral-700 backdrop-blur-xl"
          >
            {/* Header: GitHub Icon, Title, Close Button */}
            <div className="flex items-center justify-between pb-3 border-b border-neutral-200/80 dark:border-neutral-800">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 flex items-center justify-center shrink-0">
                  <svg className="w-3 h-3 fill-current" viewBox="0 0 24 24">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                  </svg>
                </div>
                <span className="font-mono text-xs font-black tracking-wider uppercase text-neutral-800 dark:text-neutral-200">
                  GitHub Repository
                </span>
              </div>

              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="w-6 h-6 rounded-full flex items-center justify-center text-neutral-400 hover:text-neutral-800 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors cursor-pointer"
                title="Close"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Area to paste link of GitHub repo (nothing else) */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleConnect(repoInput);
              }}
              className="pt-3 space-y-2.5"
            >
              <div className="flex items-center gap-1.5 p-1 rounded-xl bg-neutral-100 dark:bg-neutral-800/90 border border-neutral-200 dark:border-neutral-700 focus-within:border-red-500/50 transition-all">
                <input
                  type="text"
                  value={repoInput}
                  onChange={(e) => setRepoInput(e.target.value)}
                  placeholder="Paste GitHub repo link (e.g. https://github.com/...)"
                  className="flex-1 bg-transparent px-2.5 py-1 text-xs font-mono text-neutral-900 dark:text-white placeholder-neutral-400 dark:placeholder-neutral-500 outline-none"
                  autoFocus
                />
                <button
                  type="button"
                  onClick={handlePasteClipboard}
                  className="p-1.5 rounded-md text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors cursor-pointer"
                  title="Paste from clipboard"
                >
                  {copied ? (
                    <Check className="w-3.5 h-3.5 text-emerald-500" />
                  ) : (
                    <Clipboard className="w-3.5 h-3.5" />
                  )}
                </button>
                <button
                  type="submit"
                  disabled={!repoInput.trim()}
                  className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-mono text-[11px] font-black transition-colors cursor-pointer shrink-0 shadow-sm shadow-red-600/30"
                >
                  Connect
                </button>
              </div>

              {connectedRepo && (
                <div className="flex items-center justify-between px-1 text-[11px] font-mono text-neutral-500 dark:text-neutral-400">
                  <span className="truncate">
                    Current: <strong className="text-red-600 dark:text-red-400">{connectedRepo}</strong>
                  </span>
                  <button
                    type="button"
                    onClick={handleClear}
                    className="text-[10px] text-neutral-400 hover:text-red-600 transition-colors underline cursor-pointer ml-2 shrink-0"
                  >
                    Reset
                  </button>
                </div>
              )}
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Trigger Button: Clean GitHub Pill matching search bar styling */}
      <motion.button
        type="button"
        onClick={() => {
          sounds.playClick();
          setIsOpen(!isOpen);
        }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="relative group flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/95 dark:bg-neutral-900/95 text-neutral-900 dark:text-white border border-neutral-300 dark:border-neutral-700 shadow-md hover:shadow-lg transition-all duration-200 cursor-pointer backdrop-blur-xl"
        title="Connect GitHub Repository for ISHA Fix"
      >
        {/* GitHub Logo Icon in Circle */}
        <div className="w-5 h-5 rounded-full bg-neutral-950 dark:bg-white text-white dark:text-black flex items-center justify-center shrink-0">
          <svg className="w-3 h-3 fill-current" viewBox="0 0 24 24">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
        </div>

        <span className="font-mono text-xs font-black tracking-tight">
          {connectedRepo ? connectedRepo : "GitHub"}
        </span>

        {/* Status Dot */}
        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
      </motion.button>
    </div>
  );
};

export default Skiper46;
