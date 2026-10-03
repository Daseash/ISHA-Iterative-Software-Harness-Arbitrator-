import React, { useRef } from "react";
import { motion, useTransform, type MotionValue, useScroll } from "framer-motion";

export const GithubIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

interface ProjectItem {
  title: string;
  src: string;
  link: string;
}

const projects: ProjectItem[] = [
  {
    title: "CLI",
    src: "/eyes.jpg",
    link: "#cli",
  },
  {
    title: "FIX",
    src: "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070&auto=format&fit=crop",
    link: "#fix",
  },
  {
    title: "GIT HUB",
    src: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=2034&auto=format&fit=crop",
    link: "https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-",
  },
];

interface ImageCardProps {
  i: number;
  src: string;
  progress: MotionValue<number>;
  range: [number, number];
  targetScale: number;
}

const ImageCard: React.FC<ImageCardProps> = ({
  i,
  src,
  progress,
  range,
  targetScale,
}) => {
  const scale = useTransform(progress, range, [1, targetScale]);

  return (
    <div className="sticky top-28 flex h-[60vh] sm:h-[65vh] w-full items-center justify-center">
      <motion.div
        style={{
          scale,
          top: `calc(-2vh + ${i * 20}px)`,
        }}
        className="relative h-full w-full rounded-3xl overflow-hidden shadow-2xl shadow-neutral-900/30 dark:shadow-black/70 bg-neutral-900 transition-all duration-300"
      >
        <img
          src={src}
          alt={`ISHA Visual ${i + 1}`}
          className="w-full h-full object-cover filter brightness-90 contrast-110"
        />
      </motion.div>
    </div>
  );
};

interface TextCardProps {
  i: number;
  project: ProjectItem;
  progress: MotionValue<number>;
  range: [number, number];
  targetScale: number;
}

const TextCard: React.FC<TextCardProps> = ({
  i,
  project,
  progress,
  range,
  targetScale,
}) => {
  const scale = useTransform(progress, range, [1, targetScale]);

  return (
    <div className="sticky top-28 flex h-[60vh] sm:h-[65vh] w-full items-center justify-center">
      <motion.a
        href={project.link}
        target={project.link.startsWith("http") ? "_blank" : undefined}
        rel={project.link.startsWith("http") ? "noreferrer" : undefined}
        style={{
          scale,
          top: `calc(-2vh + ${i * 20}px)`,
        }}
        className="relative flex h-[16vh] sm:h-[18vh] w-full max-w-xl items-center justify-center rounded-2xl sm:rounded-3xl px-8 py-6 shadow-2xl shadow-neutral-900/15 dark:shadow-black/70 bg-[#F9F7EF] dark:bg-black transition-all duration-300 group cursor-pointer border border-neutral-300 dark:border-neutral-800 hover:scale-[1.02]"
      >
        {/* Only the large bold text - selective red text accent */}
        <span
          className={`text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black uppercase tracking-wider text-center group-hover:scale-105 transition-transform duration-300 ${
            i === 0 ? "text-red-600" : i === 1 ? "text-black dark:text-[#F9F7EF]" : "text-red-600"
          }`}
        >
          {project.title}
        </span>
      </motion.a>
    </div>
  );
};

export const DemoSkiper16: React.FC = () => {
  const container = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: container,
    offset: ["start start", "end end"],
  });

  return (
    <section className="relative w-full py-16 sm:py-24 bg-[#F9F7EF] dark:bg-black transition-colors">
      <div
        ref={container}
        className="max-w-7xl mx-auto px-4 sm:px-8 md:px-12 pb-24"
      >
        {/* Mobile / Tablet Unified Card Stack */}
        <div className="lg:hidden flex flex-col items-center justify-center w-full space-y-8">
          {projects.map((project, i) => (
            <motion.a
              key={`mobile_${i}`}
              href={project.link}
              target={project.link.startsWith("http") ? "_blank" : undefined}
              rel={project.link.startsWith("http") ? "noreferrer" : undefined}
              whileTap={{ scale: 0.98 }}
              className="w-full rounded-3xl overflow-hidden bg-[#F9F7EF] dark:bg-black border border-neutral-300 dark:border-neutral-800 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 p-5 space-y-4 group cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <span
                  className={`text-2xl sm:text-3xl font-black uppercase tracking-wider ${
                    i === 0
                      ? "text-red-600"
                      : i === 1
                      ? "text-black dark:text-[#F9F7EF]"
                      : "text-red-600"
                  }`}
                >
                  {project.title}
                </span>
                <span className="p-2 rounded-xl bg-neutral-200/80 dark:bg-neutral-900 text-red-600 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform">
                  ↗
                </span>
              </div>
              <div className="w-full h-52 sm:h-64 rounded-2xl overflow-hidden bg-neutral-900">
                <img
                  src={project.src}
                  alt={project.title}
                  className="w-full h-full object-cover filter brightness-90 contrast-110 group-hover:scale-105 transition-transform duration-300"
                />
              </div>
            </motion.a>
          ))}
        </div>

        {/* Desktop Side-by-Side Dual Card Stack (lg+) */}
        <div className="hidden lg:grid grid-cols-12 gap-16 items-start">
          {/* Left Column: Pure Text Stack */}
          <div className="col-span-6 flex flex-col items-center justify-center w-full">
            {projects.map((project, i) => {
              const targetScale = Math.max(0.7, 1 - (projects.length - i - 1) * 0.08);
              return (
                <TextCard
                  key={`text_${i}`}
                  i={i}
                  project={project}
                  progress={scrollYProgress}
                  range={[i * 0.33, 1]}
                  targetScale={targetScale}
                />
              );
            })}
          </div>

          {/* Right Column: Pure Image Card Stack */}
          <div className="col-span-6 flex flex-col items-center justify-center w-full">
            {projects.map((project, i) => {
              const targetScale = Math.max(0.7, 1 - (projects.length - i - 1) * 0.08);
              return (
                <ImageCard
                  key={`img_${i}`}
                  i={i}
                  src={project.src}
                  progress={scrollYProgress}
                  range={[i * 0.33, 1]}
                  targetScale={targetScale}
                />
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};

export default DemoSkiper16;
