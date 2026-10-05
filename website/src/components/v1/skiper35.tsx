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
  defaultActiveIndex = 2,
}) => {
  const [activeIndex, setActiveIndex] = useState<number>(defaultActiveIndex);

  return (
    <div
      className={`relative w-full h-full bg-black overflow-x-auto overflow-y-hidden select-none flex items-stretch ${className}`}
    >
      <div className="mx-auto flex w-full h-full flex-col md:flex-row lg:min-w-[1600px] bg-black">
        {items.map((item, index) => {
          const isActive = activeIndex === index;

          return (
            <motion.div
              key={item.id}
              layout
              initial={false}
              animate={{
                width: isActive ? "28rem" : "4rem",
              }}
              transition={{
                type: "spring",
                stiffness: 260,
                damping: 26,
              }}
              onMouseEnter={() => setActiveIndex(index)}
              onClick={() => setActiveIndex(index)}
              className="lg:border-r relative h-full w-full cursor-pointer border-0 border-white/30 md:border-r overflow-hidden shrink-0 transition-colors"
              style={{
                height: "100%",
              }}
            >
              {/* EXACT SKIPER35 ROTATED TEXT CONTAINER */}
              <div
                className={`absolute bottom-0 left-[2vw] flex w-[calc(100vh-2.6vw)] origin-[0_50%] transform justify-between pr-5 text-xl font-medium leading-[2.6vw] tracking-[-0.03em] md:-rotate-90 md:text-[2vw] transition-colors duration-200 pointer-events-none z-10 ${
                  isActive ? "text-[#f1f1f1]" : "text-[#f1f1f1]/30 hover:text-[#f1f1f1]/60"
                }`}
              >
                <p className="label w-full border-b py-2 md:w-auto md:border-0 md:py-0 whitespace-nowrap font-bold">
                  {item.title}
                </p>
                <AnimatePresence>
                  {isActive && (
                    <motion.p
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="year hidden md:block whitespace-nowrap font-mono font-bold text-white tracking-wider"
                    >
                      {item.metric}
                    </motion.p>
                  )}
                </AnimatePresence>
              </div>

              {/* EXACT SKIPER35 EXPANDED IMAGE WRAPPER */}
              <motion.div
                animate={{ opacity: isActive ? 1 : 0 }}
                transition={{ duration: 0.35 }}
                className="h-[92%] rounded-[0.6vw] object-cover pl-2 pr-[1.3vw] pt-[1.3vw] md:h-[100%] md:pb-[1.3vw] md:pl-[4vw]"
              >
                <img
                  alt={item.title}
                  className="w-full h-full rounded-2xl md:rounded-3xl object-cover filter contrast-110 brightness-95"
                  src={item.image}
                  style={{
                    height: "100%",
                    objectFit: "cover",
                  }}
                />
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
    <main className="w-full h-screen bg-black">
      <Skiper35 />
    </main>
  );
};

export default Skiper35;
