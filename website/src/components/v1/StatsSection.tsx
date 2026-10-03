import React from "react";
import { TrendingUp, Zap, ShieldCheck, BarChart3 } from "lucide-react";

export const StatsSection: React.FC = () => {
  const statsMetrics = [
    {
      value: "94.8%",
      label: "SWE-BENCH RESOLUTION",
      icon: TrendingUp,
    },
    {
      value: "12X",
      label: "PARALLEL AGENT SPEEDUP",
      icon: Zap,
    },
    {
      value: "0.0%",
      label: "REGRESSION FAILURE RATE",
      icon: ShieldCheck,
    },
  ];

  return (
    <section id="stats" className="relative py-24 px-6 md:px-12 bg-[#F9F7EF] dark:bg-black transition-colors font-black">
      <div className="max-w-6xl mx-auto space-y-12">
        <div className="text-center">
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tight text-black dark:text-[#F9F7EF]">
            STATS
          </h2>
        </div>

        {/* 3 Large Stat Metrics with 3D Shadows */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {statsMetrics.map((stat, i) => {
            const Icon = stat.icon;
            return (
              <div
                key={i}
                className="flex flex-col items-center justify-center p-8 sm:p-10 rounded-3xl bg-[#F9F7EF] dark:bg-black border border-neutral-300 dark:border-neutral-800 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 text-center space-y-3 transition-transform hover:-translate-y-1 duration-300"
              >
                <div className="p-3 rounded-2xl bg-neutral-200/80 dark:bg-neutral-900 text-red-600 shadow-sm mb-2">
                  <Icon className="w-8 h-8 stroke-[3]" />
                </div>
                <span className="text-5xl sm:text-6xl font-black text-red-600 tracking-tight">
                  {stat.value}
                </span>
                <span className="text-sm sm:text-base font-black uppercase tracking-wider text-black dark:text-[#F9F7EF]">
                  {stat.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Visual Benchmark Cards / Image Data Showcase Slots */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Card 1: Benchmark Comparison Frame */}
          <div className="rounded-3xl bg-[#F9F7EF] dark:bg-black border border-neutral-300 dark:border-neutral-800 p-8 sm:p-10 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-neutral-300 dark:border-neutral-800">
              <span className="text-lg font-black uppercase tracking-tight text-black dark:text-[#F9F7EF]">
                BENCHMARK EVALUATION
              </span>
              <BarChart3 className="w-6 h-6 stroke-[3] text-red-600" />
            </div>

            <div className="h-64 sm:h-72 w-full rounded-2xl overflow-hidden shadow-inner bg-neutral-900 flex items-center justify-center relative group">
              <img
                src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop"
                alt="Benchmark Evaluation Graph"
                className="w-full h-full object-cover filter brightness-85 contrast-110 group-hover:scale-105 transition-transform duration-500"
              />
            </div>
          </div>

          {/* Card 2: Autonomous Multi-Agent Execution Frame */}
          <div className="rounded-3xl bg-[#F9F7EF] dark:bg-black border border-neutral-300 dark:border-neutral-800 p-8 sm:p-10 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-neutral-300 dark:border-neutral-800">
              <span className="text-lg font-black uppercase tracking-tight text-black dark:text-[#F9F7EF]">
                MULTI-AGENT ARBITRATION
              </span>
              <Zap className="w-6 h-6 stroke-[3] text-red-600" />
            </div>

            <div className="h-64 sm:h-72 w-full rounded-2xl overflow-hidden shadow-inner bg-neutral-900 flex items-center justify-center relative group">
              <img
                src="https://images.unsplash.com/photo-1504639725590-34d0984388bd?q=80&w=2070&auto=format&fit=crop"
                alt="Multi-Agent Execution Pipeline"
                className="w-full h-full object-cover filter brightness-85 contrast-110 group-hover:scale-105 transition-transform duration-500"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default StatsSection;
