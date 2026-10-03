import React from "react";
import { RollingText } from "./v1/skiper27";

export const Main: React.FC = () => {
  const ishaLines = [
    "ISHA",
    "ITERATIVE",
    "SOFTWARE",
    "HARNESS",
    "ARBITRATOR",
  ];

  return (
    <div className="min-h-screen w-full bg-[#F9F7EF] dark:bg-black text-red-600 flex flex-col justify-center items-center px-4 sm:px-8 py-16 select-none overflow-hidden">
      <div className="w-full max-w-5xl flex flex-col items-center justify-center space-y-2 sm:space-y-3 md:space-y-4 text-center">
        {ishaLines.map((line, index) => (
          <div key={index} className="flex justify-center w-full">
            <RollingText
              text={line}
              speed={0.05}
              duration={3.5}
              repeatDelay={1.5}
              className={`${
                index === 0
                  ? "text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tight text-red-600 uppercase mb-2"
                  : "text-2xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-red-600 uppercase"
              }`}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default Main;
