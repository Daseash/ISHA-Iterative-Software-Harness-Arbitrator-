import React, { useState, useRef } from "react";
import { motion, AnimatePresence, useMotionValue, useSpring } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import { sounds } from "../../utils/sound";

export interface TeamMember {
  name: string;
  image: string;
  role?: string;
  link?: string;
}

export interface HoverMemberProps {
  teamMembers: TeamMember[];
  defaultName?: string;
  className?: string;
  backgroundColor?: string;
  textColor?: string;
  hoverTextColor?: string;
  cursorColor?: string;
}

export const HoverMember: React.FC<HoverMemberProps> = ({
  teamMembers = [],
  defaultName = "FEATURES",
  className = "",
  backgroundColor,
  textColor,
  hoverTextColor = "#dc2626", // ISHA signature bold red
  cursorColor = "#dc2626",
}) => {
  const [hoveredMember, setHoveredMember] = useState<TeamMember | null>(null);
  const [isInside, setIsInside] = useState(false);
  const [isHoveringCard, setIsHoveringCard] = useState(false);
  const containerRef = useRef<HTMLElement>(null);

  // Mouse follower smooth springs
  const rawMouseX = useMotionValue(-100);
  const rawMouseY = useMotionValue(-100);

  const springConfig = { damping: 25, stiffness: 350, mass: 0.5 };
  const cursorX = useSpring(rawMouseX, springConfig);
  const cursorY = useSpring(rawMouseY, springConfig);

  const handleMouseMove = (e: React.MouseEvent<HTMLElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    rawMouseX.set(e.clientX - rect.left);
    rawMouseY.set(e.clientY - rect.top);
  };

  const handleMouseEnterSection = () => {
    setIsInside(true);
  };

  const handleMouseLeaveSection = () => {
    setIsInside(false);
    setHoveredMember(null);
    setIsHoveringCard(false);
  };

  const activeName = hoveredMember ? hoveredMember.name : defaultName;
  const isHovered = hoveredMember !== null;

  const handleMemberHover = (member: TeamMember) => {
    if (hoveredMember?.name !== member.name) {
      setHoveredMember(member);
      setIsHoveringCard(true);
      sounds.playClick();
    }
  };

  const handleMemberLeave = () => {
    setHoveredMember(null);
    setIsHoveringCard(false);
  };

  const handleMemberClick = (member: TeamMember) => {
    sounds.playClick();
    if (!member.link) return;
    if (member.link.startsWith("http")) {
      window.open(member.link, "_blank", "noreferrer");
    } else {
      const el = document.querySelector(member.link);
      if (el) {
        el.scrollIntoView({ behavior: "smooth" });
      }
    }
  };

  // Determine custom text color styles
  const isCustomTextColor = textColor && (textColor.startsWith("#") || textColor.startsWith("rgb"));
  const isCustomHoverColor = hoverTextColor && (hoverTextColor.startsWith("#") || hoverTextColor.startsWith("rgb"));

  return (
    <section
      id="features"
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnterSection}
      onMouseLeave={handleMouseLeaveSection}
      style={backgroundColor ? { backgroundColor } : undefined}
      className={`relative w-full py-28 px-6 sm:px-12 overflow-hidden select-none transition-colors duration-300 ${className}`}
    >
      {/* ================= CUSTOM CURSOR FOLLOWER ================= */}
      <motion.div
        style={{
          x: cursorX,
          y: cursorY,
          translateX: "-50%",
          translateY: "-50%",
          borderColor: cursorColor,
        }}
        animate={{
          scale: !isInside ? 0 : isHoveringCard ? 1.8 : 1,
          opacity: isInside ? 1 : 0,
        }}
        transition={{ duration: 0.2 }}
        className="pointer-events-none absolute z-30 flex items-center justify-center rounded-full border-2 bg-transparent"
      >
        <motion.div
          style={{ backgroundColor: cursorColor }}
          animate={{
            scale: isHoveringCard ? 0.35 : 1,
          }}
          transition={{ duration: 0.2 }}
          className="pointer-events-none h-3 w-3 rounded-full shadow-lg shadow-red-600/30"
        />
        {isHoveringCard && (
          <motion.span
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            className="pointer-events-none absolute text-[8px] font-mono font-black uppercase tracking-wider text-red-600"
          >
            OPEN
          </motion.span>
        )}
      </motion.div>

      <div className="max-w-7xl mx-auto flex flex-col items-center justify-center space-y-16">
        {/* Section Subtitle Tag */}
        <div className="flex items-center gap-3">
          <span className="h-2 w-2 rounded-full bg-red-600 animate-pulse" />
          <span className="text-xs font-mono uppercase tracking-[0.35em] text-neutral-500 dark:text-neutral-400 font-black">
            ISHA ARCHITECTURE · HOVER TO EXPLORE
          </span>
        </div>

        {/* ================= CREATIVE REVEAL TEXT ANIMATION ================= */}
        {/* Inspired by opos.buzzworthystudio.com/directors */}
        <div className="relative h-24 sm:h-36 md:h-44 lg:h-52 w-full flex items-center justify-center overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeName}
              initial={{ y: 70, opacity: 0, rotateX: -25 }}
              animate={{ y: 0, opacity: 1, rotateX: 0 }}
              exit={{ y: -70, opacity: 0, rotateX: 25 }}
              transition={{
                duration: 0.45,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="flex items-center justify-center text-center px-4"
            >
              <h2
                style={{
                  color: isHovered
                    ? isCustomHoverColor
                      ? hoverTextColor
                      : undefined
                    : isCustomTextColor
                    ? textColor
                    : undefined,
                }}
                className={`text-5xl sm:text-7xl md:text-8xl lg:text-9xl font-black uppercase tracking-tighter transition-colors duration-200 ${
                  isHovered
                    ? !isCustomHoverColor
                      ? hoverTextColor
                      : ""
                    : !isCustomTextColor
                    ? textColor || "text-neutral-400 dark:text-neutral-500"
                    : ""
                }`}
              >
                {activeName}
              </h2>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* ================= FEATURES SHOWCASE (CLI · FIX · STATS · GITHUB) ================= */}
        <div className="w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8 max-w-7xl mx-auto">
          {teamMembers.map((member, idx) => {
            const isThisHovered = hoveredMember?.name === member.name;
            const isAnyHovered = hoveredMember !== null;

            return (
              <motion.div
                key={member.name + idx}
                onMouseEnter={() => handleMemberHover(member)}
                onMouseLeave={handleMemberLeave}
                onClick={() => handleMemberClick(member)}
                whileHover={{ y: -8 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
                className="group relative flex flex-col items-center cursor-pointer"
              >
                {/* Image Card Container */}
                <div
                  className={`relative w-full aspect-[3/4] rounded-3xl overflow-hidden shadow-2xl transition-all duration-500 ${
                    isThisHovered
                      ? "ring-2 ring-red-600 shadow-red-600/25 scale-[1.03]"
                      : isAnyHovered
                      ? "opacity-45 grayscale contrast-125 scale-[0.98]"
                      : "shadow-neutral-900/15 dark:shadow-black/70 grayscale hover:grayscale-0"
                  } bg-neutral-900`}
                >
                  <img
                    src={member.image}
                    alt={member.name}
                    className="w-full h-full object-cover object-center transition-transform duration-700 ease-out group-hover:scale-110"
                    onError={(e) => {
                      const target = e.currentTarget;
                      const fallbacks = [
                        "/eyes.jpg",
                        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070&auto=format&fit=crop",
                        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop",
                        "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=2034&auto=format&fit=crop",
                      ];
                      target.src = fallbacks[idx % fallbacks.length];
                    }}
                  />

                  {/* Gradient Overlay for Cinematic Lighting */}
                  <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-70 group-hover:opacity-40 transition-opacity duration-300" />

                  {/* Feature Index Badge */}
                  <div className="pointer-events-none absolute top-4 left-4 font-mono text-xs font-black text-white/90 bg-black/50 backdrop-blur-md px-2.5 py-1 rounded-full border border-white/10">
                    0{idx + 1}
                  </div>

                  {/* External / Anchor Arrow Indicator */}
                  <div className="pointer-events-none absolute top-4 right-4 h-7 w-7 rounded-full bg-black/50 backdrop-blur-md border border-white/10 flex items-center justify-center text-white/80 group-hover:text-red-500 group-hover:scale-110 transition-all">
                    <ArrowUpRight className="w-3.5 h-3.5 stroke-[2.5]" />
                  </div>

                  {/* Role / Description Tag */}
                  {member.role && (
                    <div className="pointer-events-none absolute bottom-4 left-4 right-4 font-mono text-[11px] font-black uppercase tracking-wider text-white/90 leading-snug">
                      {member.role}
                    </div>
                  )}
                </div>

                {/* Subtitle Label on Mobile / Accessibility */}
                <div className="mt-4 flex items-center justify-between w-full px-2">
                  <span
                    className={`font-black text-base uppercase tracking-wider transition-colors duration-300 ${
                      isThisHovered ? "text-red-600" : "text-black dark:text-[#F9F7EF]"
                    }`}
                  >
                    {member.name}
                  </span>
                  <span className="text-xs font-mono text-neutral-400 font-black">
                    [0{idx + 1}]
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export const DemoSkiper6: React.FC = () => {
  const teamMembers: TeamMember[] = [
    {
      name: "CLI",
      image: "/eyes.jpg",
      role: "Autonomous Terminal & Batch Execution Engine",
      link: "#cli",
    },
    {
      name: "FIX",
      image: "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070&auto=format&fit=crop",
      role: "Self-Healing AST & Patch Verification Pipeline",
      link: "#fix",
    },
    {
      name: "STATS",
      image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop",
      role: "Benchmark Telemetry & Resolution Metrics",
      link: "#stats",
    },
    {
      name: "GITHUB",
      image: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=2034&auto=format&fit=crop",
      role: "Open Source Codebase & Architecture",
      link: "https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-",
    },
  ];

  return (
    <HoverMember
      teamMembers={teamMembers}
      defaultName="FEATURES"
      hoverTextColor="#dc2626"
      cursorColor="#dc2626"
    />
  );
};

export default DemoSkiper6;
