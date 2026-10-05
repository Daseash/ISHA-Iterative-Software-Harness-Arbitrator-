import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export interface Skiper35Item {
  id: string;
  title: string;
  metric: string;
  image: string;
}

export const defaultItems: Skiper35Item[] = [
  {
    id: "smoke50",
    title: "Smoke 50 · SWE-Bench",
    metric: "14.0% · 20.6%",
    image: "/demo-desktop.png",
  },
  {
    id: "pareto",
    title: "Pareto Cost Frontier",
    metric: "$0.00 / Task",
    image: "/isha_vs_baselines.png",
  },
  {
    id: "hygiene",
    title: "AST Patch Hygiene",
    metric: "0.0% Abort",
    image: "/demo-chat.png",
  },
  {
    id: "laya",
    title: "Laya Calibrated Gate",
    metric: "ECE = 0.0010",
    image: "/isha_vs_baselines.png",
  },
  {
    id: "devin",
    title: "Devin Launch Baseline",
    metric: "13.86% Beat",
    image: "/demo-desktop.png",
  },
  {
    id: "tournament",
    title: "Multi-Model Arena",
    metric: "3 Worktrees",
    image: "/demo-chat.png",
  },
  {
    id: "docker",
    title: "Docker Sandboxes",
    metric: "34 / 34 Graded",
    image: "/demo-desktop.png",
  },
  {
    id: "yield",
    title: "Patch Generation Yield",
    metric: "+26.7% Gain",
    image: "/isha_vs_baselines.png",
  },
  {
    id: "django-10914",
    title: "Django Suite 10914",
    metric: "Verified Green",
    image: "/demo-desktop.png",
  },
  {
    id: "django-11039",
    title: "Django Suite 11039",
    metric: "Verified Green",
    image: "/demo-chat.png",
  },
  {
    id: "django-11133",
    title: "Django Suite 11133",
    metric: "Verified Green",
    image: "/demo-desktop.png",
  },
  {
    id: "pytest-11143",
    title: "Pytest Suite 11143",
    metric: "Verified Green",
    image: "/demo-chat.png",
  },
  {
    id: "brier",
    title: "Brier Safety Metric",
    metric: "0.0000 Brier",
    image: "/isha_vs_baselines.png",
  },
  {
    id: "tdd",
    title: "TDD Test Synthesis",
    metric: "81 / 81 Pass",
    image: "/demo-desktop.png",
  },
  {
    id: "safety",
    title: "Zero False Approvals",
    metric: "100.0% τ=0.50",
    image: "/demo-chat.png",
  },
  {
    id: "arbitrator",
    title: "State Arbitrator",
    metric: "Deterministic",
    image: "/demo-desktop.png",
  },
  {
    id: "efficiency",
    title: "Global Pareto Leader",
    metric: "Rank #1 $0.00",
    image: "/isha_vs_baselines.png",
  },
];

export interface Skiper35Props {
  items?: Skiper35Item[];
  className?: string;
  defaultActiveIndex?: number;
}

export const Skiper35: React.FC<Skiper35Props> = ({
  items = defaultItems,
  className = "",
  defaultActiveIndex = 1,
}) => {
  const [activeIndex, setActiveIndex] = useState<number>(defaultActiveIndex);

  return (
    <div
      className={`relative w-full h-full bg-[#F9F7EF] dark:bg-black overflow-x-auto overflow-y-hidden select-none flex items-stretch [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden transition-colors duration-300 ${className}`}
    >
      <div className="mx-auto flex w-full h-full flex-col md:flex-row lg:min-w-[1600px] bg-[#F9F7EF] dark:bg-black transition-colors duration-300 pt-20 md:pt-24 pb-6 md:pb-8">
        {items.map((item, index) => {
          const isActive = activeIndex === index;

          return (
            <motion.div
              key={item.id}
              layout
              initial={false}
              animate={{
                width: isActive ? "36rem" : "4rem",
              }}
              transition={{
                type: "spring",
                stiffness: 260,
                damping: 26,
              }}
              onMouseEnter={() => setActiveIndex(index)}
              onClick={() => setActiveIndex(index)}
              className="lg:border-r relative h-full w-full cursor-pointer border-0 border-neutral-300 dark:border-white/20 md:border-r overflow-hidden shrink-0 transition-colors"
              style={{
                height: "100%",
              }}
            >
              {/* EXACT SKIPER35 ROTATED TEXT CONTAINER WITH LIGHT / DARK SUPPORT */}
              <div
                className={`absolute bottom-4 left-[2vw] flex w-[calc(100vh-9rem)] origin-[0_50%] transform justify-between pr-5 text-xl font-medium leading-[2.6vw] tracking-[-0.03em] md:-rotate-90 md:text-[1.8vw] transition-colors duration-200 pointer-events-none z-20 ${
                  isActive
                    ? "text-black dark:text-[#f1f1f1]"
                    : "text-neutral-900/40 dark:text-[#f1f1f1]/30 hover:text-black dark:hover:text-[#f1f1f1]"
                }`}
              >
                <p className="label w-full border-b border-transparent py-2 md:w-auto md:border-0 md:py-0 whitespace-nowrap font-black">
                  {item.title}
                </p>
                <AnimatePresence>
                  {isActive && (
                    <motion.p
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="year hidden md:block whitespace-nowrap font-mono font-black text-red-600 dark:text-red-500 tracking-wider"
                    >
                      {item.metric}
                    </motion.p>
                  )}
                </AnimatePresence>
              </div>

              {/* EXPANDED IMAGE WRAPPER WITH CLEAN OBJECT-CONTAIN - FULLY SHOWS IMAGE */}
              <motion.div
                animate={{ opacity: isActive ? 1 : 0 }}
                transition={{ duration: 0.35 }}
                className="h-[92%] rounded-2xl md:rounded-3xl p-2 md:p-3 pl-3 md:pl-[4.5vw] md:pr-4 md:pb-4 flex items-center justify-center"
              >
                <div className="w-full h-full rounded-2xl md:rounded-3xl overflow-hidden border border-neutral-300 dark:border-neutral-800 bg-white/70 dark:bg-neutral-950/90 shadow-2xl flex items-center justify-center p-2 sm:p-4 transition-colors">
                  <img
                    alt={item.title}
                    className="w-full h-full object-contain filter contrast-105 brightness-100"
                    src={item.image}
                  />
                </div>
              </motion.div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export const DemoSkiper35: React.FC = () => {
  return (
    <main className="w-full h-screen bg-[#F9F7EF] dark:bg-black transition-colors duration-300">
      <Skiper35 />
    </main>
  );
};

export default Skiper35;
