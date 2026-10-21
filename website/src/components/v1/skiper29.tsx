import { useEffect, useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import Lenis from "lenis";
import { RollingText } from "./skiper27";
import { TextRoll } from "./skiper58";
import { Navbar_001 } from "./skiper13";
import { PhotoPlanes } from "../ui/PhotoPlanes";
import { AboutSection } from "./AboutSection";
import { CliSection } from "./CliSection";
import { LinePath } from "./skiper19";
import { HoverExpand_001 } from "./skiper52";
import { ArrowUpRight } from "lucide-react";

export function Skiper29() {
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize Lenis smooth scroll and start at top
  useEffect(() => {
    window.scrollTo(0, 0);

    const lenis = new Lenis({
      duration: 1.2,
      easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      touchMultiplier: 2,
      infinite: false,
    });

    lenis.scrollTo(0, { immediate: true });

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);

    return () => {
      lenis.destroy();
    };
  }, []);

  // Scroll triggers for parallax and SVG mask transformations
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  const flowContainerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress: flowScrollProgress } = useScroll({
    target: flowContainerRef,
    offset: ["start 0.85", "end 0.95"],
  });

  // Hero scale
  const heroScale = useTransform(scrollYProgress, [0, 0.2], [1, 0.96]);

  // Photo 2 scaling
  const photo2Scale = useTransform(scrollYProgress, [0.35, 0.55], [0.9, 1]);
  const photo2Radius = useTransform(scrollYProgress, [0.35, 0.55], ["28px", "0px"]);

  // Image parallax layers
  const yBg1 = useTransform(scrollYProgress, [0, 0.4], ["0%", "-20%"]);
  const yBg2 = useTransform(scrollYProgress, [0.3, 0.7], ["0%", "-25%"]);

  const subLines = [
    "ITERATIVE",
    "SOFTWARE",
    "HARNESS",
    "ARBITRATOR",
  ];

  const eyesGallery = [
    {
      src: "/eyes.jpg",
      alt: "Neural Repo Ingestion",
      code: "# 01",
    },
    {
      src: "/eyes.jpg",
      alt: "AST Structural Mapping",
      code: "# 02",
    },
    {
      src: "/eyes.jpg",
      alt: "TDD Test Synthesis",
      code: "# 03",
    },
    {
      src: "/eyes.jpg",
      alt: "3-Worktree Parallel Tournament",
      code: "# 04",
    },
    {
      src: "/eyes.jpg",
      alt: "State Arbitrator",
      code: "# 05",
    },
    {
      src: "/eyes.jpg",
      alt: "LAYA Calibrated Decision",
      code: "# 06",
    },
    {
      src: "/eyes.jpg",
      alt: "Closed-Loop Self-Healing",
      code: "# 07",
    },
  ];

  const sitemapScreenshotLinks = [
    {
      title: "HOME",
      href: "#hero",
    },
    {
      title: "ABOUT",
      href: "#about",
    },
    {
      title: "CLI",
      href: "#cli",
    },
    {
      title: "FIX",
      href: "/fix",
    },
    {
      title: "STATS",
      href: "/stats",
    },
    {
      title: "GIT HUB",
      href: "https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-",
      isExternal: true,
    },
  ];

  return (
    <div
      ref={containerRef}
      className="relative w-full bg-[#F9F7EF] dark:bg-black text-black dark:text-[#F9F7EF] font-black selection:bg-red-600 selection:text-white transition-colors duration-300"
    >
      {/* ================= FIXED TOP NAVIGATION (ABOVE IMAGE LIKE TEXT ON IMAGE) ================= */}
      <Navbar_001 />

      {/* SVG Mask Definition */}
      <svg className="absolute w-0 h-0 pointer-events-none">
        <defs>
          <clipPath id="sienaMask" clipPathUnits="objectBoundingBox">
            <path
              d="M 0.05,0 
                 Q 0,0.05 0,0.1 
                 L 0,0.9 
                 Q 0,0.95 0.05,1 
                 L 0.95,1 
                 Q 1,0.95 1,0.9 
                 L 1,0.1 
                 Q 1,0.05 0.95,0 
                 Z"
            />
          </clipPath>
        </defs>
      </svg>

      {/* ================= PHOTO 1: HOVER EXPAND GALLERY (SKIPER 52 - 5 SECTIONS) ================= */}
      <section className="relative w-full h-screen min-h-screen overflow-hidden bg-[#F9F7EF] dark:bg-black transition-colors duration-300 flex items-center justify-center pt-16">
        <motion.div
          style={{ y: yBg1 }}
          className="relative w-full max-w-7xl mx-auto flex items-center justify-center z-10 px-4"
        >
          <HoverExpand_001 images={eyesGallery} defaultActive={2} />
        </motion.div>
      </section>

      {/* ================= CONTINUOUS FLOW: BEHIND ISHA TEXT TILL END OF ABOUT SECTION ================= */}
      <div
        ref={flowContainerRef}
        className="relative w-full bg-[#F9F7EF] dark:bg-black transition-colors"
      >
        {/* Red scrolling LinePath (Skiper 19) starting behind ISHA text till end of About section text */}
        <div className="pointer-events-none absolute inset-0 z-0 overflow-visible flex justify-center">
          <LinePath
            scrollYProgress={flowScrollProgress}
            start={0}
            end={1}
            strokeColor="#dc2626"
            strokeWidth={18}
            className="w-full max-w-7xl h-full"
          />
        </div>

        {/* ================= HERO: ISHA IN BOLD RED, OTHERS IN BLACK/CREAM ================= */}
        <section
          id="hero"
          className="relative z-10 min-h-[80vh] w-full flex flex-col justify-center items-center px-4 sm:px-8 py-24 bg-transparent"
        >
          <motion.div
            style={{ scale: heroScale }}
            className="relative z-10 w-full max-w-5xl flex flex-col items-center justify-center text-center"
          >
            {/* ISHA hero title: Big & Spaced */}
            <div className="flex justify-center items-center w-full py-0.5 relative z-20 mb-8 sm:mb-10 md:mb-12">
              <RollingText
                text="ISHA"
                speed={0.05}
                duration={3.5}
                repeatDelay={1.5}
                className="text-5xl sm:text-7xl md:text-8xl lg:text-9xl font-black tracking-tight text-red-600 dark:text-red-500 uppercase [text-shadow:_0_0_16px_rgba(249,247,239,0.95),_0_0_6px_rgba(249,247,239,0.9)] dark:[text-shadow:_0_0_16px_rgba(0,0,0,0.95),_0_0_6px_rgba(0,0,0,0.9)]"
              />
            </div>

            {/* Down all texts: Kept attached with NO gap and decreased in size */}
            <div className="flex flex-col items-center justify-center w-full gap-0 space-y-0 leading-none relative z-20">
              {subLines.map((line, index) => (
                <div key={index} className="flex justify-center items-center w-full py-0 leading-none">
                  <RollingText
                    text={line}
                    speed={0.05}
                    duration={3.5}
                    repeatDelay={1.5}
                    className="text-base sm:text-lg md:text-xl lg:text-2xl font-black tracking-widest text-neutral-900 dark:text-[#F9F7EF] uppercase leading-none [text-shadow:_0_0_16px_rgba(249,247,239,0.95),_0_0_6px_rgba(249,247,239,0.9)] dark:[text-shadow:_0_0_16px_rgba(0,0,0,0.95),_0_0_6px_rgba(0,0,0,0.9)]"
                  />
                </div>
              ))}
            </div>


            {/* Direct Hero Action Buttons */}
            <div className="mt-8 flex flex-wrap items-center justify-center gap-4 z-30">
              <a
                href="/fix"
                className="group relative inline-flex items-center gap-2.5 px-7 py-3.5 rounded-full bg-red-600 hover:bg-red-700 text-white font-black text-sm tracking-wide shadow-xl shadow-red-600/30 hover:shadow-red-600/50 hover:scale-105 active:scale-95 transition-all duration-200 cursor-pointer"
              >
                <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                <span>TRY ISHA FIX</span>
                <ArrowUpRight className="w-4 h-4 stroke-[3] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </a>

              <a
                href="/stats"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-full border-2 border-neutral-800 dark:border-neutral-200 hover:border-red-600 dark:hover:border-red-500 text-neutral-900 dark:text-white hover:text-red-600 dark:hover:text-red-500 font-black text-sm tracking-wide hover:scale-105 active:scale-95 transition-all duration-200 cursor-pointer backdrop-blur-md"
              >
                <span>LIVE BENCHMARKS</span>
              </a>
            </div>
          </motion.div>
        </section>

        {/* ================= PHOTO 2: DOWN OF ISHA (NO TEXT ON IMAGE, 3D SHADOW, NO RED BORDER) ================= */}
        <section className="relative z-10 min-h-[65vh] sm:min-h-[80vh] w-full flex flex-col items-center justify-center py-12 px-4 sm:px-8 overflow-hidden bg-transparent">
          <motion.div
            style={{
              scale: photo2Scale,
              borderRadius: photo2Radius,
            }}
            className="relative w-full max-w-7xl h-[55vh] sm:h-[72vh] mx-auto overflow-hidden rounded-3xl shadow-2xl shadow-neutral-900/20 dark:shadow-black/80 bg-neutral-900"
          >
            {/* Background Parallax Layer */}
            <motion.div
              style={{ y: yBg2 }}
              className="absolute inset-0 w-full h-[130%] -top-[15%]"
            >
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent z-10" />
              <img
                src="/eyes.jpg"
                alt="Neural AST Processing Unit"
                className="w-full h-full object-cover filter brightness-90 contrast-110"
              />
            </motion.div>
          </motion.div>
        </section>

        {/* ================= ABOUT SECTION ================= */}
        <div className="relative z-10">
          <AboutSection />
        </div>
      </div>

      {/* ================= PHOTO PLANES GALLERY (REPLACES DEMOSKIPER16) ================= */}
      <section className="relative py-24 px-4 sm:px-6 bg-[#F9F7EF] dark:bg-black transition-colors overflow-hidden">
        <div className="max-w-7xl mx-auto flex flex-col items-center justify-center text-center space-y-4 mb-8 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-neutral-300 bg-white/80 text-xs font-mono text-neutral-600 dark:border-neutral-800 dark:bg-neutral-900/80 dark:text-neutral-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 absolute ml-[3px]" />
            ISHA AUTONOMOUS FLIGHT GALLERY
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight text-black dark:text-[#F9F7EF]">
            Live Benchmarks & Visual Telemetry
          </h2>
          <p className="max-w-2xl text-neutral-600 dark:text-neutral-400 text-sm sm:text-base">
            Inspect real-time AST graphs, container sandbox executions, and agent telemetry.
          </p>
        </div>

        <PhotoPlanes
          images={[
            { src: "/eyes.jpg", alt: "Neural Vision & Semantic Search", caption: "AST Invariant Engine" },
            { src: "/isha_vs_baselines.png", alt: "SWE-bench Tournament Scores", caption: "Benchmark Tournament" },
            { src: "/demo-desktop.png", alt: "Desktop Runtime Environment", caption: "Local Daemon Pipeline" },
            { src: "/demo-chat.png", alt: "Interactive Problem Solver", caption: "Candidate Generator" },
            { src: "/images/team/mike.jpg", alt: "Agent Telemetry Node", caption: "Static Compilation Gate" },
            { src: "/images/team/sarah.jpg", alt: "Closed Loop Verifier", caption: "Docker Sandbox Verifier" },
          ]}
          photoWidth={190}
          photoHeight={260}
          spread={130}
          tilt={12}
          depth={20}
          stagger={0.12}
        />
      </section>

      {/* ================= CLI SECTION: DOWNLOAD METHOD OF ISHA ================= */}
      <CliSection />

      {/* ================= SITEMAP SECTION ================= */}
      <section id="sitemap" className="relative py-20 px-6 md:px-12 bg-[#F9F7EF] dark:bg-black transition-colors">
        <div className="max-w-3xl mx-auto flex flex-col items-center justify-center text-center space-y-4">
          <span className="text-xs font-mono uppercase tracking-[0.35em] text-neutral-500 dark:text-neutral-400 font-black">
            SITEMAP
          </span>

          {/* Vertically Stacked Links Sticking Closely Together like skiper58 Text Roll Navigation */}
          {/* Vertically Stacked Links Attached Together - No Gap Between All 6 */}
          <nav className="flex flex-col items-center justify-center py-6 w-full select-none">
            {sitemapScreenshotLinks.map((item, i) => (
              <a
                key={item.title}
                href={item.href}
                target={item.isExternal ? "_blank" : undefined}
                rel={item.isExternal ? "noreferrer" : undefined}
                style={{ marginTop: i === 0 ? "0" : "-0.26em" }}
                className="group relative flex items-center justify-center p-0 m-0 leading-none transition-transform duration-200 hover:scale-105 hover:z-20"
              >
                <TextRoll
                  className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black uppercase tracking-tight text-red-600 hover:text-red-700 transition-colors leading-none"
                  center={i % 2 === 1}
                >
                  {item.title}
                </TextRoll>
              </a>
            ))}
          </nav>
        </div>
      </section>

      {/* ================= FOOTER (SIENA PARALLAX REMOVED AS REQUESTED) ================= */}
      <footer className="w-full py-12 px-6 md:px-12 bg-[#F9F7EF] dark:bg-black text-black dark:text-[#F9F7EF] text-xs font-mono font-black border-t border-neutral-200 dark:border-neutral-900 transition-colors">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <span className="h-3 w-3 rounded-full bg-red-600" />
            <span className="font-black">
              ISHA · Iterative Software Harness Arbitrator
            </span>
          </div>
          <div className="flex items-center gap-6">
            <a
              href="https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-/blob/main/LICENSE"
              target="_blank"
              rel="noreferrer"
              className="font-black hover:text-red-600 transition-colors inline-flex items-center gap-1"
            >
              MIT License <ArrowUpRight className="w-3.5 h-3.5 stroke-[3]" />
            </a>
            <a
              href="https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-"
              target="_blank"
              rel="noreferrer"
              className="font-black hover:text-red-600 transition-colors inline-flex items-center gap-1"
            >
              GitHub Repository <ArrowUpRight className="w-3.5 h-3.5 stroke-[3]" />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Skiper29;
