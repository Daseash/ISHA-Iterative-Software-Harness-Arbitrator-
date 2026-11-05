"use client";

import React from "react";
import { VercelSnapText } from "../unlumen-ui/vercel-snap-text";

export interface Skiper44Props {
  className?: string;
}

export const Skiper44: React.FC<Skiper44Props> = ({ className = "" }) => {
  return (
    <section
      id="engineering-pillars"
      className={`relative w-full bg-[#F9F7EF] dark:bg-black transition-colors py-12 sm:py-16 ${className}`}
    >
      <VercelSnapText
        prefix="WE ENGINEER"
        items={[
          "THE AUTONOMOUS HARNESS",
          "THE REPRODUCTION PROOF FIRST",
          "THE 3 ISOLATED WORKTREES",
          "THE PRE-SANDBOX AST GATES",
          "THE CALIBRATED LAYA SCORE",
          "THE VERIFIED MINIMAL PULL REQUEST",
          "ZERO FALSE APPROVALS",
          "THE 8 CONTAINER INVARIANTS",
          "THE FUTURE OF SOFTWARE",
        ]}
        itemHeight={96}
        className="w-full h-[65vh] sm:h-[75vh] min-h-[580px]"
      />
    </section>
  );
};

export default Skiper44;
