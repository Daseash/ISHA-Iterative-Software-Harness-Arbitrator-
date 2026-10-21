import React, { useState, useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";

export interface PhotoPlanesImage {
  src: string;
  alt?: string;
  caption?: string;
}

export interface PhotoPlanesProps {
  images: PhotoPlanesImage[];
  photoWidth?: number;
  photoHeight?: number;
  spread?: number;
  tilt?: number;
  depth?: number;
  stagger?: number;
  autoplay?: number;
  className?: string;
}

export const PhotoPlanes: React.FC<PhotoPlanesProps> = ({
  images,
  photoWidth = 170,
  photoHeight = 230,
  spread = 112,
  tilt = 10,
  depth = 0,
  stagger = 0.14,
  className = "",
}) => {
  const [hasLanded, setHasLanded] = useState(false);
  const [isFanned, setIsFanned] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, amount: 0.15 });

  // Trigger falling and fanning animation once when section enters view (or immediately on refresh)
  useEffect(() => {
    if (isInView && !hasLanded) {
      setHasLanded(true);
      const fanTimer = setTimeout(() => {
        setIsFanned(true);
      }, (images.length * stagger + 0.35) * 1000);

      return () => clearTimeout(fanTimer);
    }
  }, [isInView, hasLanded, images.length, stagger]);

  const centerIndex = (images.length - 1) / 2;

  return (
    <div
      ref={containerRef}
      className={`relative w-full flex flex-col items-center justify-center py-16 overflow-hidden select-none ${className}`}
      style={{ minHeight: `${photoHeight + 160}px` }}
    >
      {/* 3D Perspective Stage */}
      <div
        className="relative flex items-center justify-center w-full"
        style={{
          perspective: 1200,
          perspectiveOrigin: "center center",
          height: `${photoHeight + 40}px`,
        }}
      >
        <div className="relative flex items-center justify-center w-full h-full">
          {images.map((image, i) => {
            // Calculate fanned out X offset
            const baseOffset = (i - centerIndex) * spread;

            // When a plane is hovered, neighbours shift outwards to make room
            let hoverShift = 0;
            if (hoveredIndex !== null) {
              if (i < hoveredIndex) {
                hoverShift = -36;
              } else if (i > hoveredIndex) {
                hoverShift = 36;
              }
            }

            const isHovered = hoveredIndex === i;

            // Slanted plane angles matching design
            const normalRotateZ = -tilt * 0.75;
            const normalRotateY = 16;
            const normalRotateX = 4;

            return (
              <motion.div
                key={i}
                className="absolute cursor-pointer rounded-2xl overflow-hidden shadow-2xl bg-neutral-900 border border-white/10"
                style={{
                  width: `${photoWidth}px`,
                  height: `${photoHeight}px`,
                  transformStyle: "preserve-3d",
                  zIndex: isHovered ? 60 : i + 10,
                }}
                initial={{
                  x: 0,
                  y: -360,
                  scale: 1.25,
                  rotateZ: (i % 2 === 0 ? -1 : 1) * (8 + (i * 3) % 7),
                  rotateY: 0,
                  rotateX: 0,
                  opacity: 0,
                }}
                animate={
                  !hasLanded
                    ? {
                        x: 0,
                        y: -360,
                        scale: 1.25,
                        rotateZ: (i % 2 === 0 ? -1 : 1) * (8 + (i * 3) % 7),
                        rotateY: 0,
                        rotateX: 0,
                        opacity: 0,
                      }
                    : !isFanned
                    ? {
                        // Phase 1: Landing on pile (falling animation)
                        x: (i % 3 - 1) * 4,
                        y: (i - centerIndex) * -2,
                        scale: 1,
                        rotateZ: (i % 2 === 0 ? -1 : 1) * (4 + i * 2),
                        rotateY: 0,
                        rotateX: 0,
                        opacity: 1,
                        transition: {
                          delay: i * stagger,
                          duration: 0.5,
                          ease: [0.22, 1, 0.36, 1],
                        },
                      }
                    : {
                        // Phase 2: Fanned row
                        x: baseOffset + hoverShift,
                        y: isHovered ? -24 : (i - centerIndex) * depth,
                        scale: isHovered ? 1.14 : 1,
                        rotateZ: isHovered ? 0 : normalRotateZ,
                        rotateY: isHovered ? 0 : normalRotateY,
                        rotateX: isHovered ? 0 : normalRotateX,
                        opacity: 1,
                        transition: {
                          duration: 0.7,
                          ease: [0.25, 1, 0.5, 1],
                        },
                      }
                }
                whileHover={
                  isFanned
                    ? {
                        scale: 1.15,
                        y: -24,
                        rotateZ: 0,
                        rotateY: 0,
                        rotateX: 0,
                        transition: { duration: 0.3, ease: "easeOut" },
                      }
                    : {}
                }
                onMouseEnter={() => isFanned && setHoveredIndex(i)}
                onMouseLeave={() => isFanned && setHoveredIndex(null)}
                onClick={() => {
                  if (isFanned) {
                    setHoveredIndex(hoveredIndex === i ? null : i);
                  }
                }}
              >
                <img
                  src={image.src}
                  alt={image.alt || `Photo plane ${i + 1}`}
                  className="w-full h-full object-cover pointer-events-none select-none filter contrast-105"
                  loading="lazy"
                />
                {/* Subtle glass reflection highlight */}
                <div className="absolute inset-0 bg-gradient-to-tr from-black/20 via-transparent to-white/15 pointer-events-none" />
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PhotoPlanes;
