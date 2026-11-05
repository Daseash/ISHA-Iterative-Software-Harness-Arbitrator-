import React, { useRef } from "react";
import { motion, useScroll, useTransform, MotionValue } from "framer-motion";

export interface TextBoxRevealProps {
  children: React.ReactNode;
  highlight?: string | string[];
  highlightTextClass?: string;
  highlightBgClass?: string;
  className?: string;
}

interface WordToken {
  type: "word" | "br";
  text?: string;
}

interface WordProps {
  text: string;
  progress: MotionValue<number>;
  range: [number, number];
  isHighlight?: boolean;
  highlightTextClass?: string;
  highlightBgClass?: string;
}

const Word: React.FC<WordProps> = ({
  text,
  progress,
  range,
  isHighlight,
  highlightTextClass = "!text-red-600 dark:!text-red-500",
  highlightBgClass = "!bg-red-600/10 dark:!bg-red-600/20",
}) => {
  const opacity = useTransform(progress, range, [0.18, 1]);
  const y = useTransform(progress, range, [4, 0]);
  const bgOpacity = useTransform(progress, range, [0, 1]);

  return (
    <span className="relative inline-block mx-[0.16em] my-[0.08em] whitespace-nowrap">
      {isHighlight && (
        <motion.span
          style={{ opacity: bgOpacity }}
          className={`absolute -inset-x-1.5 -inset-y-0.5 rounded-lg z-0 ${highlightBgClass}`}
        />
      )}
      <motion.span
        style={{ opacity, y }}
        className={`relative z-10 inline-block font-black transition-colors [text-shadow:_0_0_12px_rgba(249,247,239,0.95)] dark:[text-shadow:_0_0_12px_rgba(0,0,0,0.95)] ${
          isHighlight ? highlightTextClass : ""
        }`}
      >
        {text}
      </motion.span>
    </span>
  );
};

export const TextBoxReveal: React.FC<TextBoxRevealProps> = ({
  children,
  highlight,
  highlightTextClass = "!text-red-600",
  highlightBgClass = "!bg-red-600/10",
  className = "",
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start 0.85", "end 0.35"],
  });

  // Normalize highlight targets into a clean lowercase array
  const highlightList = (
    Array.isArray(highlight)
      ? highlight
      : highlight
      ? [highlight]
      : []
  ).map((h) => h.toLowerCase());

  // Flatten children (strings, br tags, etc.) into structured tokens
  const tokens: WordToken[] = [];

  const extractTokens = (nodes: React.ReactNode) => {
    React.Children.forEach(nodes, (node) => {
      if (typeof node === "string" || typeof node === "number") {
        const words = String(node).split(/\s+/);
        words.forEach((w) => {
          if (w.length > 0) {
            tokens.push({ type: "word", text: w });
          }
        });
      } else if (React.isValidElement(node)) {
        if (node.type === "br") {
          tokens.push({ type: "br" });
        } else if (node.props && (node.props as { children?: React.ReactNode }).children) {
          extractTokens((node.props as { children?: React.ReactNode }).children);
        }
      }
    });
  };

  extractTokens(children);

  const wordCount = tokens.filter((t) => t.type === "word").length;
  let wordIndex = 0;

  return (
    <div ref={containerRef} className={`relative leading-relaxed ${className}`}>
      {tokens.map((token, idx) => {
        if (token.type === "br") {
          return <br key={`br_${idx}`} className="my-2" />;
        }

        const currentIdx = wordIndex++;
        const step = 1 / Math.max(wordCount, 1);
        const start = currentIdx * step;
        const end = Math.min(1, start + step * 1.5);

        const rawLower = (token.text || "").toLowerCase().replace(/[.,!?;:]+$/, "");
        const cleanWord = rawLower.replace(/[^a-zA-Z0-9_$%/-]/g, "");
        const isHighlight = highlightList.includes(cleanWord) || highlightList.includes(rawLower);

        return (
          <Word
            key={`word_${idx}`}
            text={token.text || ""}
            progress={scrollYProgress}
            range={[start, end]}
            isHighlight={isHighlight}
            highlightTextClass={highlightTextClass}
            highlightBgClass={highlightBgClass}
          />
        );
      })}
    </div>
  );
};

export default TextBoxReveal;
