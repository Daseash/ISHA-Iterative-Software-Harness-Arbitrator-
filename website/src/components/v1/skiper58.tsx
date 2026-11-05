import React, { useState } from "react";
import { motion } from "framer-motion";

interface TextRollProps {
  children: string;
  className?: string;
  center?: boolean;
  stagger?: number;
  duration?: number;
}

export const TextRoll: React.FC<TextRollProps> = ({
  children,
  className = "",
  center = false,
  stagger = 0.025,
  duration = 0.4,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const text = String(children);
  const characters = Array.from(text);
  const centerIndex = (characters.length - 1) / 2;

  return (
    <motion.span
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`relative inline-flex flex-wrap items-center overflow-hidden cursor-pointer select-none leading-none font-black ${className}`}
    >
      {characters.map((char, index) => {
        const delay = center
          ? Math.abs(index - centerIndex) * stagger
          : index * stagger;

        if (char === " ") {
          return (
            <span key={index} className="inline-block w-[0.28em]">
              &nbsp;
            </span>
          );
        }

        return (
          <span
            key={index}
            className="relative inline-flex h-[0.92em] items-center justify-center overflow-hidden leading-none font-black text-red-600"
          >
            {/* Base character rolls up on hover */}
            <motion.span
              animate={{
                y: isHovered ? "-140%" : "0%",
              }}
              transition={{
                duration,
                delay,
                ease: [0.76, 0, 0.24, 1] as const,
              }}
              className="inline-block font-black text-red-600"
            >
              {char}
            </motion.span>

            {/* Cloned character rolls in from bottom on hover */}
            <motion.span
              aria-hidden="true"
              animate={{
                y: isHovered ? "0%" : "140%",
              }}
              transition={{
                duration,
                delay,
                ease: [0.76, 0, 0.24, 1] as const,
              }}
              className="absolute inline-block font-black text-red-600"
            >
              {char}
            </motion.span>
          </span>
        );
      })}
    </motion.span>
  );
};

export const Skiper58: React.FC = () => {
  const navItems = [
    { title: "CLI", href: "#cli", desc: "Autonomous terminal-native coding agent" },
    { title: "CHAT", href: "#chat", desc: "Conversational pair programming companion" },
    { title: "Cloud", href: "#cloud", desc: "Connect GitHub & fix bugs autonomously" },
    { title: "GIT HUB", href: "https://github.com", desc: "Official ISHA Repository & Release Hub" },
  ];

  return (
    <div className="w-full flex flex-col items-center justify-center p-8 bg-[#F9F7EF] dark:bg-black text-red-600 font-black">
      <div className="w-full max-w-4xl space-y-6">
        <div className="border-b-2 border-red-200 pb-4 text-center">
          <span className="text-xs font-mono uppercase tracking-widest text-red-600 font-black">
            Text Roll Navigation · Skiper58
          </span>
          <p className="text-xs text-red-600 font-black mt-1">
            Text roll hover effects and staggered character animations
          </p>
        </div>

        <nav className="flex flex-wrap items-center justify-center gap-8 md:gap-12 py-4 font-black">
          {navItems.map((item, i) => (
            <a key={i} href={item.href} className="group">
              <TextRoll
                className="text-2xl md:text-3xl font-black uppercase text-red-600 hover:text-red-800 transition-colors"
                center={i % 2 === 1}
              >
                {item.title}
              </TextRoll>
            </a>
          ))}
        </nav>
      </div>
    </div>
  );
};

export default Skiper58;
