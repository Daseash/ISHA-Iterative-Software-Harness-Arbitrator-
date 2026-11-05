import React from "react";
import { RollingText } from "./v1/skiper27";

export const Main: React.FC = () => {
  const subLines = [
    "ITERATIVE",
    "SOFTWARE",
    "HARNESS",
    "ARBITRATOR",
  ];

  return (
    <div className="min-h-screen w-full bg-[#F9F7EF] dark:bg-black text-red-600 flex flex-col justify-center items-center px-4 sm:px-8 py-16 select-none overflow-hidden">
      <div className="w-full max-w-5xl flex flex-col items-center justify-center text-center">
        {/* ISHA hero title: Big & Spaced */}
        <div className="flex justify-center w-full mb-8 sm:mb-10 md:mb-12">
          <RollingText
            text="ISHA"
            speed={0.05}
            duration={3.5}
            repeatDelay={1.5}
            className="text-5xl sm:text-7xl md:text-8xl lg:text-9xl font-black tracking-tight text-red-600 uppercase"
          />
        </div>

        {/* Down all texts: Kept attached with NO gap and decreased in size */}
        <div className="flex flex-col items-center justify-center w-full gap-0 space-y-0 leading-none">
          {subLines.map((line, index) => (
            <div key={index} className="flex justify-center w-full py-0 leading-none">
              <RollingText
                text={line}
                speed={0.05}
                duration={3.5}
                repeatDelay={1.5}
                className="text-base sm:text-lg md:text-xl lg:text-2xl font-black tracking-widest text-neutral-900 dark:text-[#F9F7EF] uppercase leading-none"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Main;
