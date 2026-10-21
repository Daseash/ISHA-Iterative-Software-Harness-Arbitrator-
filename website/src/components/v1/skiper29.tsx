import { useEffect, useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import Lenis from "lenis";
import { RollingText } from "./skiper27";
import { TextRoll } from "./skiper58";
import { Navbar_001 } from "./skiper13";
import { PipelinePlanes } from "../ui/PipelinePlanes";
import { ScrollHighlight } from "./ScrollHighlight";
import { AboutSection } from "./AboutSection";
import { VercelSnapText } from "../unlumen-ui/vercel-snap-text";
import { CliSection } from "./CliSection";
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

  // Hero scale
  const heroScale = useTransform(scrollYProgress, [0, 0.2], [1, 0.96]);

  // Photo 1 parallax layer
  const yBg1 = useTransform(scrollYProgress, [0, 0.4], ["0%", "-20%"]);

  // Photo 2 (Eyes banner) - Authentic Skiper29 Dolly Zoom (Vertigo effect)
  // Dedicated useScroll directly tracking this section's viewport progress
  const photo2SectionRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress: photo2Scroll } = useScroll({
    target: photo2SectionRef,
    offset: ["start end", "end start"],
  });

  // Authentic Skiper29: Container zooms out from 1 to 0.72 while inner image zooms in from 1 to 1.35
  const photo2Scale = useTransform(photo2Scroll, [0, 1], [1, 0.72]);
  const photo2InnerScale = useTransform(photo2Scroll, [0, 1], [1, 1.35]);
  const photo2Radius = useTransform(photo2Scroll, [0, 1], ["24px", "40px"]);
  const photo2ImageY = useTransform(photo2Scroll, [0, 1], ["-6%", "6%"]);

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
      <Navbar_001 showThemeToggle={true} />

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

      {/* ================= HERO & ABOUT CONTINUOUS FLOW ================= */}
      <div className="relative w-full bg-[#F9F7EF] dark:bg-black transition-colors">

        {/* ================= HERO: EXACT SKIPER27 ROLLING TEXT & SCROLL INDICATOR ================= */}
        <section
          id="hero"
          className="relative z-10 min-h-[85vh] w-full flex flex-col justify-center items-center px-4 sm:px-8 py-20 bg-transparent"
        >
          {/* Top: Authentic Skiper27 Scroll Down Indicator with Gradient Line */}
          <div className="relative mb-8 sm:mb-10 flex flex-col items-center justify-center text-center z-20 select-none">
            <span className="relative max-w-[14ch] text-[10px] sm:text-xs font-mono uppercase tracking-[0.25em] opacity-40 text-neutral-900 dark:text-[#F9F7EF] leading-tight after:absolute after:left-1/2 after:top-full after:mt-2 after:h-12 sm:after:h-16 after:w-px after:bg-gradient-to-b after:from-neutral-900 dark:after:from-[#F9F7EF] after:to-transparent after:content-['']">
              scroll down to see
            </span>
          </div>

          <motion.div
            style={{ scale: heroScale }}
            className="relative z-10 w-full max-w-5xl flex flex-col items-center justify-center text-center mt-6 sm:mt-8"
          >
            {/* Authentic Skiper27 2-Line Stacked Rolling Typography */}
            <div className="flex flex-col items-center justify-center w-full select-none text-center">
              <RollingText
                text="ISHA"
                speed={0.05}
                duration={4}
                className="text-6xl sm:text-8xl md:text-9xl lg:text-[140px] font-black tracking-tight text-red-600 dark:text-red-500 uppercase leading-[0.9]"
              />
              <RollingText
                text="ARBITRATOR"
                speed={0.05}
                duration={4}
                className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tight text-neutral-900 dark:text-[#F9F7EF] uppercase leading-[0.9] mt-2 sm:mt-3"
              />
            </div>

            {/* Acronym Expansion Tagline */}
            <div className="mt-5 sm:mt-6 flex flex-wrap items-center justify-center gap-2 sm:gap-3 font-mono text-[10px] sm:text-xs font-bold tracking-[0.28em] uppercase text-neutral-500 dark:text-neutral-400">
              <span>ITERATIVE</span>
              <span className="text-red-600">•</span>
              <span>SOFTWARE</span>
              <span className="text-red-600">•</span>
              <span>HARNESS</span>
              <span className="text-red-600">•</span>
              <span>ARBITRATOR</span>
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

        {/* ================= PHOTO 2: DOWN OF ISHA (AUTHENTIC SKIPER29 SCROLL ZOOM OUT & ZOOM IN) ================= */}
        <section
          ref={photo2SectionRef}
          className="relative z-10 min-h-[70vh] sm:min-h-[85vh] w-full flex flex-col items-center justify-center py-16 sm:py-24 px-4 sm:px-8 overflow-hidden bg-transparent"
        >
          <motion.div
            style={{
              scale: photo2Scale,
              borderRadius: photo2Radius,
            }}
            className="relative w-full max-w-7xl h-[50vh] sm:h-[65vh] md:h-[72vh] mx-auto overflow-hidden rounded-3xl shadow-2xl shadow-neutral-900/25 dark:shadow-black/85 bg-neutral-950 transform-gpu will-change-transform"
          >
            {/* Background Parallax Layer with Inner Zoom In */}
            <motion.div
              style={{
                scale: photo2InnerScale,
                y: photo2ImageY,
              }}
              className="absolute inset-0 w-full h-full transform-gpu will-change-transform"
            >
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent z-10 pointer-events-none" />
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

      {/* ================= VERCEL SNAP TEXT (UNLUMEN UI: SCROLL-DRIVEN SNAPPING LIST) ================= */}
      <section id="engineering-tenets" className="relative w-full bg-[#F9F7EF] dark:bg-black transition-colors py-12 sm:py-16">
        <VercelSnapText
          prefix="WE ENGINEER"
          items={[
            "THE AUTONOMOUS HARNESS",
            "REPRODUCTION PROOFS FIRST",
            "THE 3 ISOLATED WORKTREES",
            "PRE-SANDBOX AST GATES",
            "THE CALIBRATED LAYA SCORE",
            "VERIFIED MINIMAL PULL REQUESTS",
            "ZERO FALSE APPROVALS",
            "THE 8 CONTAINER INVARIANTS",
            "THE FUTURE OF SOFTWARE",
          ]}
          itemHeight={72}
          className="w-full h-[65vh] sm:h-[75vh] min-h-[520px]"
        />
      </section>

      {/* ================= THE COMPLETE AUTONOMOUS PIPELINE (3D INTERACTIVE DECK) ================= */}
      <section id="pipeline" className="relative py-24 px-4 sm:px-6 bg-[#F9F7EF] dark:bg-black transition-colors overflow-hidden">
        <div className="max-w-7xl mx-auto flex flex-col items-center justify-center text-center space-y-4 mb-4 relative z-10">
          <p className="inline-flex items-center gap-2 font-mono text-[10px] sm:text-xs font-black uppercase tracking-[0.28em] text-red-600 dark:text-red-500">
            <svg className="h-3.5 w-3.5 fill-current" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 1l2.2 7.1L21 5l-3.6 6.5L24 14l-7.1 1.3L19 22l-7-3.9L5 22l2.1-6.7L0 14l6.6-2.5L3 5l6.8 3.1z" />
            </svg>
            THE COMPLETE AUTONOMOUS PIPELINE
          </p>
          <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black tracking-tight text-neutral-950 dark:text-[#F9F7EF]">
            The harness,{" "}
            <ScrollHighlight variant="brush" color="sun" delay={0.1}>
              end to end.
            </ScrollHighlight>
          </h2>
          <p className="max-w-2xl text-neutral-600 dark:text-neutral-400 text-sm sm:text-base font-bold">
            The 8-stage empirical loop behind every verified, minimal-churn pull request.
          </p>
        </div>

        <PipelinePlanes />
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
