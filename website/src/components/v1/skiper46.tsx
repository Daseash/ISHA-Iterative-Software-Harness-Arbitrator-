"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Clipboard, Check, FolderGit2 } from "lucide-react";
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

  const handleConnect = (rawVal: string) => {
    const cleaned = rawVal.trim();
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

  const quickPresets = [
    { label: "Local Sandbox", value: "tests/dummy_repo" },
    { label: "Django", value: "django/django" },
    { label: "Requests", value: "psf/requests" },
    { label: "Sympy", value: "sympy/sympy" },
  ];

  return (
    <div className={`relative inline-flex flex-col items-center select-none ${className}`}>
      {/* Floating Expandable Card */}
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
                  <FolderGit2 className="w-3 h-3 text-red-500" />
                </div>
                <span className="font-mono text-xs font-black tracking-wider uppercase text-neutral-800 dark:text-neutral-200">
                  Connect Target Repository
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

            {/* Input Form */}
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
                  placeholder="Local path or GitHub URL (e.g. tests/dummy_repo)"
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

              {/* Quick Presets */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {quickPresets.map((qp, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleConnect(qp.value)}
                    className="px-2 py-0.5 rounded-md bg-neutral-200/60 dark:bg-neutral-800 text-[10px] font-mono font-bold text-neutral-600 dark:text-neutral-300 hover:bg-red-500/20 hover:text-red-500 transition-colors cursor-pointer"
                  >
                    {qp.label}
                  </button>
                ))}
              </div>

              {connectedRepo && (
                <div className="flex items-center justify-between px-1 text-[11px] font-mono text-neutral-500 dark:text-neutral-400 pt-1">
                  <span className="truncate">
                    Active: <strong className="text-red-600 dark:text-red-400">{connectedRepo}</strong>
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

      {/* Main Trigger Button */}
      <motion.button
        type="button"
        onClick={() => {
          sounds.playClick();
          setIsOpen(!isOpen);
        }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="relative group flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/95 dark:bg-neutral-900/95 text-neutral-900 dark:text-white border border-neutral-300 dark:border-neutral-700 shadow-md hover:shadow-lg transition-all duration-200 cursor-pointer backdrop-blur-xl"
        title="Connect Repository for ISHA Fix"
      >
        <div className="w-5 h-5 rounded-full bg-neutral-950 dark:bg-white text-white dark:text-black flex items-center justify-center shrink-0">
          <FolderGit2 className="w-3 h-3 text-red-500" />
        </div>

        <span className="font-mono text-xs font-black tracking-tight">
          {connectedRepo ? connectedRepo : "Connect Repo"}
        </span>

        {/* Status Dot */}
        <span className={`w-2 h-2 rounded-full ${connectedRepo ? "bg-emerald-500 animate-pulse" : "bg-neutral-400"}`} />
      </motion.button>
    </div>
  );
};

export default Skiper46;
