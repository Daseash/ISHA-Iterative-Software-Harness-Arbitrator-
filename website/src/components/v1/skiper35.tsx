import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export interface Skiper35Panel {
  id: string;
  verticalLabel: string;
  metric: string;
  title: string;
  badge?: string;
  image: string;
  subMetric?: string;
}

export const defaultPanels: Skiper35Panel[] = [
  {
    id: "smoke50",
    verticalLabel: "Smoke 50 SWE-Bench",
    metric: "14.0% · 20.6%",
    title: "Smoke 50 Lite",
    badge: "7 Resolved Suites",
    image: "/demo-desktop.png",
    subMetric: "Official Maintainer Docker Sandboxes",
  },
  {
    id: "pareto",
    verticalLabel: "Pareto Cost Frontier",
    metric: "$0.00 / Task",
    title: "Cost Frontier",
    badge: "Free Tier Cascade",
    image: "/isha_vs_baselines.png",
    subMetric: "vs $10–$25 Commercial Agents",
  },
  {
    id: "hygiene",
    verticalLabel: "AST Patch Hygiene",
    metric: "0.0% Aborts",
    title: "Patch Engine",
    badge: "0.0% Apply Failures",
    image: "/demo-chat.png",
    subMetric: "Cross-Platform LF Repair",
  },
  {
    id: "laya",
    verticalLabel: "Laya Calibrated Gate",
    metric: "ECE = 0.0010",
    title: "Laya Decision",
    badge: "100% Precision",
    image: "/isha_vs_baselines.png",
    subMetric: "Zero False Auto-Approve",
  },
  {
    id: "devin",
    verticalLabel: "Devin Launch Baseline",
    metric: "13.86% Beat",
    title: "Devin Baseline",
    badge: "20.6% on Patches",
    image: "/demo-desktop.png",
    subMetric: "1 in 5 Patches Resolved",
  },
  {
    id: "tournament",
    verticalLabel: "Multi-Model Arena",
    metric: "3 Worktrees",
    title: "Parallel Arena",
    badge: "Multi-Candidate",
    image: "/demo-chat.png",
    subMetric: "Groq LPU + Gemini 3.8 Flash",
  },
  {
    id: "docker",
    verticalLabel: "Docker Maintainer Suites",
    metric: "34 / 34 Graded",
    title: "Docker Sandbox",
    badge: "100% Hermetic",
    image: "/demo-desktop.png",
    subMetric: "Isolated Container Run",
  },
  {
    id: "yield",
    verticalLabel: "Patch Generation Yield",
    metric: "+26.7% Gain",
    title: "Yield Elevation",
    badge: "66.7% Clean AST",
    image: "/isha_vs_baselines.png",
    subMetric: "Down from 26.7% Failures",
  },
  {
    id: "django",
    verticalLabel: "Django Suites Resolved",
    metric: "6 Resolved",
    title: "Django Sandboxes",
    badge: "10914 · 11039 · 11133",
    image: "/demo-desktop.png",
    subMetric: "Complex ORM & Migrations",
  },
  {
    id: "pytest",
    verticalLabel: "Pytest Suite Resolved",
    metric: "pytest-11143",
    title: "Pytest Verified",
    badge: "100% Green Suite",
    image: "/demo-chat.png",
    subMetric: "Maintainer Unit Verification",
  },
  {
    id: "brier",
    verticalLabel: "Brier Safety Calibration",
    metric: "0.0000",
    title: "Brier Calibration",
    badge: "Perfect Reliability",
    image: "/isha_vs_baselines.png",
    subMetric: "Temperature Scaled T=0.35",
  },
  {
    id: "t_tests",
    verticalLabel: "TDD Test Synthesis",
    metric: "81 / 81 Pass",
    title: "Test Synthesis",
    badge: "~18s Execution",
    image: "/demo-desktop.png",
    subMetric: "Isolated Reproduction First",
  },
  {
    id: "safety",
    verticalLabel: "Zero False Approvals",
    metric: "100.0%",
    title: "Safety Gate",
    badge: "τ = 0.50 Threshold",
    image: "/demo-chat.png",
    subMetric: "315 Developer Labels",
  },
  {
    id: "arbitrator",
    verticalLabel: "State Arbitrator",
    metric: "100% Deterministic",
    title: "Arbitrator",
    badge: "Multi-Worktree Merge",
    image: "/demo-desktop.png",
    subMetric: "AST Tree Difference Arbiter",
  },
  {
    id: "self_heal",
    verticalLabel: "Closed-Loop Self-Healing",
    metric: "4 Rounds Max",
    title: "Self-Healing",
    badge: "Feedback Loop",
    image: "/demo-chat.png",
    subMetric: "Live Linter & Pytest Guard",
  },
  {
    id: "efficiency",
    verticalLabel: "Global Pareto Leader",
    metric: "Rank #1 Cost/Acc",
    title: "Pareto Leader",
    badge: "$0.00 vs $20.00",
    image: "/isha_vs_baselines.png",
    subMetric: "Commercial Benchmark Parity",
  },
];

export interface Skiper35Props {
  panels?: Skiper35Panel[];
  className?: string;
  onSelect?: (panel: Skiper35Panel) => void;
}

export const Skiper35: React.FC<Skiper35Props> = ({
  panels = defaultPanels,
  className = "",
  onSelect,
}) => {
  // Default to the 3rd panel active like in the screenshot ("Midnight Canvas" was 3rd)
  const [activeId, setActiveId] = useState<string>(panels[2]?.id || panels[0].id);

  return (
    <div
      className={`relative w-full h-full flex flex-col md:flex-row items-stretch bg-black overflow-x-auto overflow-y-hidden select-none border border-neutral-900 rounded-3xl ${className}`}
    >
      {panels.map((panel) => {
        const isActive = activeId === panel.id;

        return (
          <motion.div
            key={panel.id}
            layout
            onMouseEnter={() => {
              setActiveId(panel.id);
              onSelect?.(panel);
            }}
            onClick={() => {
              setActiveId(panel.id);
              onSelect?.(panel);
            }}
            transition={{
              type: "spring",
              stiffness: 260,
              damping: 26,
            }}
            className={`relative flex flex-col justify-between cursor-pointer border-b md:border-b-0 md:border-r border-neutral-900 transition-colors duration-200 overflow-hidden ${
              isActive
                ? "flex-[6] min-w-[320px] sm:min-w-[420px] md:min-w-[500px] lg:min-w-[560px] bg-[#0c0c0c] z-10"
                : "flex-[0.6] min-w-[48px] sm:min-w-[54px] md:min-w-[58px] min-h-[60px] md:min-h-full bg-black hover:bg-neutral-950"
            }`}
          >
            {/* COLLAPSED VIEW: Exact vertical text running upwards from bottom */}
            {!isActive && (
              <div className="absolute inset-0 flex items-center md:items-end justify-center md:justify-center p-3 pb-8 pointer-events-none">
                <span className="block md:hidden font-mono text-xs uppercase tracking-widest text-neutral-400 font-bold truncate">
                  {panel.verticalLabel}
                </span>
                <span className="hidden md:block [writing-mode:vertical-rl] rotate-180 font-mono text-xs lg:text-sm uppercase tracking-widest text-neutral-500 hover:text-white transition-colors duration-200 font-bold whitespace-nowrap">
                  {panel.verticalLabel}
                </span>
              </div>
            )}

            {/* EXPANDED VIEW: Pure data & core visual matching the skiper35 preview */}
            <AnimatePresence mode="wait">
              {isActive && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.25 }}
                  className="relative z-10 flex flex-col justify-between h-full p-6 sm:p-8 md:p-10 w-full"
                >
                  {/* TOP: Core Metric (e.g. 2024 / 14.0% · 20.6% / $0.00 / 0.0%) */}
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <span className="text-3xl sm:text-4xl md:text-5xl font-black font-mono tracking-tight text-white block">
                        {panel.metric}
                      </span>
                      {panel.subMetric && (
                        <span className="font-mono text-xs sm:text-sm text-neutral-400 uppercase tracking-widest font-bold mt-1 block">
                          {panel.subMetric}
                        </span>
                      )}
                    </div>
                    {panel.badge && (
                      <span className="px-3 py-1 rounded-full bg-red-600/20 border border-red-600/40 text-red-400 font-mono text-xs uppercase tracking-wider font-bold shrink-0">
                        {panel.badge}
                      </span>
                    )}
                  </div>

                  {/* CENTER: Rounded visual card showcasing the graph / demo */}
                  <div className="relative flex-1 my-5 w-full min-h-[240px] sm:min-h-[280px] md:min-h-[340px] rounded-3xl overflow-hidden border border-neutral-800 bg-neutral-950 shadow-2xl">
                    <img
                      src={panel.image}
                      alt={panel.title}
                      className="w-full h-full object-cover filter contrast-110 brightness-90 hover:scale-105 transition-transform duration-700"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent pointer-events-none" />
                  </div>

                  {/* BOTTOM: Core bold title */}
                  <div className="flex items-end justify-between gap-4">
                    <h2 className="text-2xl sm:text-3xl md:text-4xl font-black uppercase tracking-tight text-white">
                      {panel.title}
                    </h2>
                    <span className="font-mono text-xs uppercase tracking-widest text-neutral-500 font-bold hidden sm:inline-block">
                      ISHA · AUDITED RUNS
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        );
      })}
    </div>
  );
};

export const DemoSkiper35: React.FC = () => {
  return (
    <main className="w-full h-full">
      <Skiper35 />
    </main>
  );
};

export default Skiper35;
