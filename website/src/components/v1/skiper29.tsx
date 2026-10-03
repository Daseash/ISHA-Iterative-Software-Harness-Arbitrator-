import { useEffect, useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import Lenis from "lenis";
import { RollingText } from "./skiper27";
import { TextRoll } from "./skiper58";
import { Navbar_001 } from "./skiper13";
import { DemoSkiper16 } from "./skiper16";
import { AboutSection } from "./AboutSection";
import { Skiper82 } from "./skiper82";
import { CliSection } from "./CliSection";
import { StatsSection } from "./StatsSection";
import { LinePath } from "./skiper19";
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

  const ishaLines = [
    "ISHA",
    "ITERATIVE",
    "SOFTWARE",
    "HARNESS",
    "ARBITRATOR",
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
      href: "#fix",
    },
    {
      title: "STATS",
      href: "#stats",
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

      {/* ================= PHOTO 1: FULL SCREEN OCCUPIED, ZOOMED OUT & CLEAR ================= */}
      <section className="relative w-full h-screen min-h-screen overflow-hidden bg-black">
        <div className="relative w-full h-full overflow-hidden flex items-center justify-center">
          {/* Background Parallax Layer */}
          <motion.div
            style={{ y: yBg1 }}
            className="absolute inset-0 w-full h-[115%] -top-[7%] flex items-center justify-center"
          >
            <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-black/30 z-10 pointer-events-none" />
            <img
              src="/eyes.jpg"
              alt="ISHA Vision System"
              className="w-full h-full object-cover object-center scale-100 filter brightness-95 contrast-110"
            />
          </motion.div>
        </div>
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
            className="relative z-10 w-full max-w-5xl flex flex-col items-center justify-center space-y-4 text-center"
          >
            {/* 5 Lines of Rolling Text: ISHA in bold red, remaining 4 lines in black/cream */}
            <div className="w-full flex flex-col items-center justify-center gap-2 sm:gap-3 md:gap-3.5 py-2">
              {ishaLines.map((line, index) => (
                <div key={index} className="flex justify-center items-center w-full py-0.5 relative z-20">
                  <RollingText
                    text={line}
                    speed={0.05}
                    duration={3.5}
                    repeatDelay={1.5}
                    className={`${
                      index === 0
                        ? "text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tight text-red-600 dark:text-red-500 uppercase [text-shadow:_0_0_16px_rgba(249,247,239,0.95),_0_0_6px_rgba(249,247,239,0.9)] dark:[text-shadow:_0_0_16px_rgba(0,0,0,0.95),_0_0_6px_rgba(0,0,0,0.9)]"
                        : "text-2xl sm:text-4xl md:text-5xl lg:text-6xl font-black tracking-tight text-neutral-900 dark:text-[#F9F7EF] uppercase [text-shadow:_0_0_16px_rgba(249,247,239,0.95),_0_0_6px_rgba(249,247,239,0.9)] dark:[text-shadow:_0_0_16px_rgba(0,0,0,0.95),_0_0_6px_rgba(0,0,0,0.9)]"
                    }`}
                  />
                </div>
              ))}
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

      {/* ================= CARD STACK SCROLL (SKIPER16: SIDE-BY-SIDE TEXT & IMAGE STACKS) ================= */}
      <DemoSkiper16 />

      {/* ================= CLI SECTION: DOWNLOAD METHOD OF ISHA ================= */}
      <CliSection />

      {/* ================= FIX SECTION WITH SKIPER82 ================= */}
      <section id="fix" className="relative py-24 px-6 md:px-12 bg-[#F9F7EF] dark:bg-black transition-colors">
        <div className="max-w-5xl mx-auto space-y-10">
          <div className="text-center">
            <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tight text-red-600">
              FIX
            </h2>
          </div>

          {/* Interactive Skiper82 AI Input 002 Chat */}
          <div className="w-full flex flex-col">
            <Skiper82 />
          </div>
        </div>
      </section>

      {/* ================= STATS SECTION: BENCHMARKS & IMAGE DATA SLOTS ================= */}
      <StatsSection />

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
