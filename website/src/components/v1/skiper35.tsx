import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, ArrowUpRight } from "lucide-react";

export interface Skiper35Panel {
  id: string;
  tag: string;
  title: string;
  metric: string;
  sub: string;
  image: string;
  badge: string;
  statList: { label: string; value: string; highlight?: boolean }[];
  comparison?: { agent: string; cost: string; score: string; isIsha?: boolean }[];
  resolvedList?: string[];
  description: string;
}

export const defaultPanels: Skiper35Panel[] = [
  {
    id: "smoke50",
    tag: "BENCHMARK EVALUATION",
    title: "SMOKE 50 · SWE-BENCH LITE",
    metric: "14.0% Overall · 20.6% on Patches",
    sub: "7 Verified Resolved Tasks in Official Docker Containers",
    image: "/demo-desktop.png",
    badge: "SWE-BENCH LITE",
    statList: [
      { label: "Patches Produced", value: "35 / 50 (70%)" },
      { label: "Docker Graded", value: "34 / 34 (100%)" },
      { label: "Resolved Rate (Patches)", value: "20.6% (7/34)", highlight: true },
      { label: "Devin Launch Baseline", value: "13.86% Beat", highlight: true },
    ],
    resolvedList: [
      "django__django-10914",
      "django__django-11039",
      "django__django-11133",
      "pytest-dev__pytest-11143",
      "django__django-11099",
      "django__django-11583",
      "django__django-11049",
    ],
    description:
      "Evaluated on official maintainer Docker containers across Django, Pytest, and SymPy. 1 in 5 produced patches resolved the official benchmark suite completely green.",
  },
  {
    id: "comparison",
    tag: "EFFICIENCY FRONTIER",
    title: "ISHA VS OTHERS IN FIELD",
    metric: "$0.00 / Task vs $10–$25 Commercial",
    sub: "Free-Tier Groq LPU + Gemini 3.8 Flash Cascade",
    image: "/isha_vs_baselines.png",
    badge: "PARETO LEADER",
    statList: [
      { label: "ISHA Inference Cost", value: "$0.00", highlight: true },
      { label: "Commercial Cost / Task", value: "$5.00 – $20.00" },
      { label: "Multi-Model Tournament", value: "3 Worktrees", highlight: true },
      { label: "Token Consumption", value: "Optimized RAG" },
    ],
    comparison: [
      { agent: "ISHA (Your Agent)", cost: "$0.00", score: "14.0% - 20.6%", isIsha: true },
      { agent: "Devin (Cognition)", cost: "$10 – $20", score: "13.86% (Launch)" },
      { agent: "SWE-agent (Princeton)", cost: "$3.50 – $8", score: "18.0% – 23%" },
      { agent: "OpenHands (OpenDevin)", cost: "$4 – $10", score: "19.0% – 26%" },
      { agent: "Raw GPT-4 (Base)", cost: "$2 – $5", score: "3.8%" },
    ],
    description:
      "ISHA sets the global Pareto efficiency frontier: high resolution accuracy without burning hundreds of dollars in proprietary API credits.",
  },
  {
    id: "patch-engine",
    tag: "SYSTEM ARCHITECTURE",
    title: "PATCH HYGIENE & ENGINE",
    metric: "0.0% Apply Failures · 0/30 Aborts",
    sub: "Atomic LF Writes & Cross-Platform CRLF Repair",
    image: "/demo-chat.png",
    badge: "100% CLEAN AST",
    statList: [
      { label: "Patch Apply Failures", value: "0.0% (down from 26.7%)", highlight: true },
      { label: "Container Aborts", value: "0/30 (0.0%)", highlight: true },
      { label: "Patch Generation Yield", value: "66.7% (+26.7% Gain)", highlight: true },
      { label: "Environment Health", value: "30/30 (100%)" },
    ],
    description:
      "Eliminates line-ending corruption and diff context mismatches. Every candidate patch undergoes static compilation gates before entering isolated test containers.",
  },
  {
    id: "laya-gate",
    tag: "CALIBRATED SAFETY",
    title: "LAYA CALIBRATED GATE",
    metric: "ECE = 0.0010 · 100% Precision",
    sub: "Temperature-Scaled T=0.35 over 315 Developer Labels",
    image: "/isha_vs_baselines.png",
    badge: "ZERO FALSE APPROVALS",
    statList: [
      { label: "Calibration Error (ECE)", value: "0.0010 (-98.9%)", highlight: true },
      { label: "Brier Score", value: "0.0000 (Perfect)", highlight: true },
      { label: "Auto-Approve Precision", value: "100.0% (at τ=0.50)", highlight: true },
      { label: "Test Suite Passing", value: "81/81 in ~18s" },
    ],
    description:
      "A calibrated logistic combiner over reproduction test status, regression counts, and blast radius that reliably decides when to auto-merge and when to escalate to senior review.",
  },
];

export const Skiper35: React.FC<{ panels?: Skiper35Panel[] }> = ({
  panels = defaultPanels,
}) => {
  const [activeId, setActiveId] = useState<string>(panels[0].id);

  return (
    <div className="w-full flex flex-col space-y-6 select-none font-black">
      {/* Interactive Expandable Panels Container */}
      <div className="flex flex-col lg:flex-row gap-4 w-full min-h-[580px] lg:min-h-[520px]">
        {panels.map((panel) => {
          const isActive = activeId === panel.id;

          return (
            <motion.div
              key={panel.id}
              layout
              onMouseEnter={() => setActiveId(panel.id)}
              onClick={() => setActiveId(panel.id)}
              transition={{
                type: "spring",
                stiffness: 260,
                damping: 26,
              }}
              className={`relative overflow-hidden rounded-3xl border transition-all duration-300 cursor-pointer flex flex-col justify-between ${
                isActive
                  ? "lg:flex-[3.5] border-red-600 shadow-2xl shadow-red-600/10 bg-neutral-900 text-white"
                  : "lg:flex-[1] border-neutral-300 dark:border-neutral-800 bg-[#F9F7EF] dark:bg-black text-black dark:text-[#F9F7EF] hover:border-neutral-400 dark:hover:border-neutral-700"
              }`}
            >
              {/* Background preview image on active panel with rich overlay */}
              {isActive && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.18 }}
                  transition={{ duration: 0.4 }}
                  className="absolute inset-0 z-0 pointer-events-none overflow-hidden"
                >
                  <img
                    src={panel.image}
                    alt={panel.title}
                    className="w-full h-full object-cover filter contrast-125 brightness-75 scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-neutral-950 via-neutral-950/80 to-transparent" />
                </motion.div>
              )}

              {/* Header area */}
              <div className="p-6 relative z-10 space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[10px] sm:text-xs uppercase tracking-widest text-red-500 font-bold">
                    {panel.tag}
                  </span>
                  <span
                    className={`font-mono text-[10px] font-black px-2.5 py-0.5 rounded-full ${
                      isActive
                        ? "bg-red-600 text-white"
                        : "bg-red-600/10 text-red-600 dark:text-red-400"
                    }`}
                  >
                    {panel.badge}
                  </span>
                </div>

                <h3
                  className={`font-black uppercase tracking-tight transition-all duration-300 ${
                    isActive
                      ? "text-2xl sm:text-3xl text-white"
                      : "text-lg lg:text-base xl:text-lg text-black dark:text-[#F9F7EF] lg:line-clamp-2"
                  }`}
                >
                  {panel.title}
                </h3>

                <p
                  className={`font-mono text-xs transition-colors ${
                    isActive
                      ? "text-red-400 font-bold"
                      : "text-neutral-500 dark:text-neutral-400 font-bold"
                  }`}
                >
                  {panel.metric}
                </p>
              </div>

              {/* Active Expanded Content: Graphs, Comparisons, & Resolved Lists */}
              <AnimatePresence mode="wait">
                {isActive && (
                  <motion.div
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    transition={{ duration: 0.35, delay: 0.1 }}
                    className="p-6 pt-0 relative z-10 space-y-5"
                  >
                    {/* Stat Badges Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                      {panel.statList.map((stat, i) => (
                        <div
                          key={i}
                          className="p-3 rounded-2xl bg-neutral-800/80 border border-neutral-700/60 flex flex-col justify-between"
                        >
                          <span className="font-mono text-[10px] text-neutral-400 uppercase tracking-wider block">
                            {stat.label}
                          </span>
                          <span
                            className={`font-mono text-xs sm:text-sm font-black mt-1 ${
                              stat.highlight ? "text-red-500" : "text-white"
                            }`}
                          >
                            {stat.value}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Comparison Table (If ISHA vs Others) */}
                    {panel.comparison && (
                      <div className="rounded-2xl bg-neutral-950/80 border border-neutral-800 p-4 space-y-2.5 overflow-x-auto">
                        <span className="font-mono text-[10px] uppercase tracking-widest text-neutral-400 block font-bold">
                          Empirical Efficiency Benchmark (Resolution vs Cost)
                        </span>
                        <table className="w-full text-left font-mono text-xs">
                          <thead>
                            <tr className="border-b border-neutral-800 text-neutral-500 uppercase text-[10px]">
                              <th className="pb-1.5">Agent / Architecture</th>
                              <th className="pb-1.5">Cost / Issue</th>
                              <th className="pb-1.5 text-right">SWE-bench Score</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-neutral-800/60 font-bold">
                            {panel.comparison.map((c, idx) => (
                              <tr
                                key={idx}
                                className={c.isIsha ? "text-red-400 font-black" : "text-neutral-300"}
                              >
                                <td className="py-1.5">{c.agent}</td>
                                <td className="py-1.5">{c.cost}</td>
                                <td className="py-1.5 text-right">{c.score}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* Verified Resolved Tasks (If Smoke50) */}
                    {panel.resolvedList && (
                      <div className="rounded-2xl bg-neutral-950/80 border border-neutral-800 p-4 space-y-2">
                        <span className="font-mono text-[10px] uppercase tracking-widest text-neutral-400 block font-bold">
                          7 Officially Resolved Docker Test Suites (Verified Green):
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {panel.resolvedList.map((task) => (
                            <span
                              key={task}
                              className="px-2.5 py-1 rounded-lg bg-neutral-800 border border-neutral-700 font-mono text-[11px] text-white font-bold inline-flex items-center gap-1.5"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                              {task}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Bottom description */}
                    <p className="text-neutral-300 font-bold text-xs sm:text-sm leading-relaxed border-t border-neutral-800 pt-3">
                      {panel.description}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Collapsed Footer preview tag */}
              {!isActive && (
                <div className="p-6 pt-0 relative z-10 flex items-center justify-between text-xs font-mono text-neutral-500">
                  <span className="truncate">{panel.sub}</span>
                  <ArrowUpRight className="w-4 h-4 shrink-0 text-red-600" />
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export const DemoSkiper35: React.FC = () => {
  return (
    <main className="w-full">
      <Skiper35 />
    </main>
  );
};

export default Skiper35;
