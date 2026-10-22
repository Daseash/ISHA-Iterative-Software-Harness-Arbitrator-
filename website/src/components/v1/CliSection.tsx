import React, { useState } from "react";
import { Copy, Check, Terminal, ArrowUpRight } from "lucide-react";
import { sounds } from "../../utils/sound";
import { ScrollHighlight } from "./ScrollHighlight";

export const CliSection: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"pip" | "curl" | "git" | "mcp">("pip");
  const [copied, setCopied] = useState(false);

  const commands = {
    pip: `# Install ISHA globally\npip install isha\n\n# Solve a bug and create a GitHub PR\nisha fix https://github.com/org/repo --issue "Fix bug..." --pr\n\n# Open visual web dashboard\nisha ui`,
    curl: `curl -sSL https://raw.githubusercontent.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-/main/install.sh | bash`,
    git: `# Direct install from GitHub\npip install git+https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-.git\n\n# Run environment health check\nisha doctor\n\n# Launch Web Dashboard\nisha ui`,
    mcp: `# 1. Start FastMCP stdio server\nisha-mcp\n\n# 2. Add to Claude Desktop / Cursor / Antigravity (mcp_config.json):\n{\n  "mcpServers": {\n    "isha": {\n      "command": "isha-mcp"\n    }\n  }\n}\n\n# Exposes: isha_solve, isha_localize, isha_tournament, isha_verify_patch`,
  };

  const handleCopy = () => {
    sounds.playSuccess();
    navigator.clipboard.writeText(commands[activeTab]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="cli" className="relative py-24 px-6 md:px-12 bg-[#F9F7EF] dark:bg-black transition-colors font-black">
      <div className="max-w-5xl mx-auto space-y-10">
        <div className="text-center">
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tight text-black dark:text-[#F9F7EF]">
            COMMAND LINE{" "}
            <ScrollHighlight variant="round" color="coral">
              INTERFACE
            </ScrollHighlight>
          </h2>
          <p className="mt-3 text-sm sm:text-base font-bold text-neutral-600 dark:text-neutral-400">
            Autonomous SWE-bench runner deployable via{" "}
            <ScrollHighlight variant="underline" color="sky">
              single command
            </ScrollHighlight>
          </p>
        </div>

        {/* Download & Installation Box - Same background colour as website with black font */}
        <div className="w-full rounded-3xl bg-[#F9F7EF] dark:bg-black p-6 sm:p-10 shadow-2xl shadow-neutral-900/15 dark:shadow-black/80 text-black dark:text-[#F9F7EF] font-black transition-colors">
          {/* Top Bar with Tabs and Copy Button */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-neutral-300 dark:border-neutral-800">
            <div className="flex items-center gap-3">
              <Terminal className="w-6 h-6 text-black dark:text-[#F9F7EF] stroke-[3]" />
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab("pip")}
                  className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-black uppercase tracking-wider transition-all cursor-pointer ${
                    activeTab === "pip"
                      ? "bg-black text-[#F9F7EF] dark:bg-[#F9F7EF] dark:text-black shadow-md"
                      : "bg-neutral-200/80 dark:bg-neutral-900 text-black dark:text-[#F9F7EF] hover:bg-neutral-300 dark:hover:bg-neutral-800"
                  }`}
                >
                  PIP (PYPI)
                </button>
                <button
                  onClick={() => setActiveTab("curl")}
                  className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-black uppercase tracking-wider transition-all cursor-pointer ${
                    activeTab === "curl"
                      ? "bg-black text-[#F9F7EF] dark:bg-[#F9F7EF] dark:text-black shadow-md"
                      : "bg-neutral-200/80 dark:bg-neutral-900 text-black dark:text-[#F9F7EF] hover:bg-neutral-300 dark:hover:bg-neutral-800"
                  }`}
                >
                  CURL
                </button>
                <button
                  onClick={() => setActiveTab("git")}
                  className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-black uppercase tracking-wider transition-all cursor-pointer ${
                    activeTab === "git"
                      ? "bg-black text-[#F9F7EF] dark:bg-[#F9F7EF] dark:text-black shadow-md"
                      : "bg-neutral-200/80 dark:bg-neutral-900 text-black dark:text-[#F9F7EF] hover:bg-neutral-300 dark:hover:bg-neutral-800"
                  }`}
                >
                  GITHUB
                </button>
                <button
                  onClick={() => setActiveTab("mcp")}
                  className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-black uppercase tracking-wider transition-all cursor-pointer ${
                    activeTab === "mcp"
                      ? "bg-black text-[#F9F7EF] dark:bg-[#F9F7EF] dark:text-black shadow-md"
                      : "bg-neutral-200/80 dark:bg-neutral-900 text-black dark:text-[#F9F7EF] hover:bg-neutral-300 dark:hover:bg-neutral-800"
                  }`}
                >
                  MCP (IDE)
                </button>
              </div>
            </div>

            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-neutral-200/80 dark:bg-neutral-900 hover:bg-neutral-300 dark:hover:bg-neutral-800 text-black dark:text-[#F9F7EF] text-xs sm:text-sm font-black uppercase tracking-wider transition-all cursor-pointer shrink-0"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 stroke-[3]" />
                  <span>COPIED</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 stroke-[3]" />
                  <span>COPY COMMAND</span>
                </>
              )}
            </button>
          </div>

          {/* Terminal Code Display - Black font on website background */}
          <div className="pt-6 overflow-x-auto">
            <pre className="font-mono text-sm sm:text-base md:text-lg text-black dark:text-[#F9F7EF] font-black leading-relaxed whitespace-pre">
              {commands[activeTab]}
            </pre>
          </div>

          {/* Quick GitHub Release Link */}
          <div className="mt-8 pt-6 border-t border-neutral-300 dark:border-neutral-800 flex items-center justify-end">
            <a
              href="https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-xs sm:text-sm text-black dark:text-[#F9F7EF] hover:text-red-600 font-black uppercase tracking-wider transition-colors"
            >
              <span>VIEW ON GITHUB</span>
              <ArrowUpRight className="w-4 h-4 stroke-[3]" />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CliSection;
