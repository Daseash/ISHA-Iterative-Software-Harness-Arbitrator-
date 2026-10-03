import React, { useState, useEffect } from "react";
import { TextBoxReveal } from "./skiper70";
import { ProgressiveBlur } from "./skiper41";

export const AboutSection: React.FC = () => {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const checkDark = () =>
      setIsDark(document.documentElement.classList.contains("dark"));
    checkDark();
    const observer = new MutationObserver(checkDark);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    return () => observer.disconnect();
  }, []);

  const blurBg = isDark ? "#000000" : "#F9F7EF";

  return (
    <section
      id="about"
      className="relative w-full py-32 px-6 sm:px-12 bg-transparent text-black dark:text-[#F9F7EF] transition-colors duration-300 border-t border-b border-neutral-200/60 dark:border-neutral-900/60 overflow-visible"
    >
      {/* Top & Bottom Progressive Blur (Skiper41) */}
      <ProgressiveBlur
        position="top"
        backgroundColor={blurBg}
        height="140px"
        blurAmount="8px"
      />
      <ProgressiveBlur
        position="bottom"
        backgroundColor={blurBg}
        height="140px"
        blurAmount="8px"
      />

      <div className="max-w-6xl mx-auto relative z-10 py-8">
        {/* ================= PURE TEXT BOX REVEAL (SKIPER70) - NO BOXES ================= */}
        <div className="max-w-5xl mx-auto px-2 sm:px-6">
          <TextBoxReveal
            highlight={[
              "ISHA",
              "autonomous",
              "harness",
              "reproducible",
              "self-healing",
              "LangGraph",
              "sandboxes",
              "worktree",
              "LAYA",
              "Tree-Sitter",
              "zero-cost",
              "LiteLLM",
              "Gemini",
              "Groq",
              "NeMo",
              "Langfuse",
              "SWE-bench",
              "66.7%",
              "0%",
              "81/81",
              "$0.00",
            ]}
            highlightTextClass="!text-red-600 dark:!text-red-500 font-black"
            highlightBgClass="!bg-red-600/15 dark:!bg-red-600/25"
            className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-black uppercase tracking-tight text-center leading-[1.4] sm:leading-[1.45]"
          >
            ISHA is an autonomous software engineering harness built for reproducible, self-healing code repair.
            <br />
            <br />
            Powered by a LangGraph cyclic multi-agent graph, ISHA orchestrates parallel candidate generation across isolated Git worktree sandboxes to eliminate race conditions.
            <br />
            <br />
            The calibrated LAYA Decision Engine replaces noisy heuristics with on-device calibrated probability arbitration and Tree-Sitter AST structural parsing to guarantee syntactically valid patches.
            <br />
            <br />
            Operating on a zero-cost inference frontier, LiteLLM cascades from Gemini 2.5 Flash for massive 1M+ context repository ingestion to ultra-fast Groq Llama 3.3 70B for responsive real-time repair loops.
            <br />
            <br />
            Secured with NeMo Guardrails and Langfuse observability, ISHA achieved 66.7% resolution on SWE-bench slices with 0% patch apply failures, an 81/81 green test suite, and $0.00 average inference cost.
          </TextBoxReveal>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
