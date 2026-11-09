"use client";

import React, { useState } from "react";
import { Copy, Check, Terminal, ArrowUpRight, Monitor, Cpu } from "lucide-react";
import { sounds } from "../../utils/sound";
import { ScrollHighlight } from "./ScrollHighlight";

export const CliSection: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"curl" | "mcp-ide" | "mcp-cli">("curl");
  const [copied, setCopied] = useState(false);
  const [copiedClone, setCopiedClone] = useState(false);

  const jsonConfig = JSON.stringify(
    {
      mcpServers: {
        isha: {
          command: "python",
          args: ["-m", "src.mcp_server"],
          cwd: "<path-to-downloaded-isha-agent-folder>",
        },
      },
    },
    null,
    2
  );

  const cloneCommand = `git clone https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-.git isha-agent\ncd isha-agent && pip install -r requirements.txt`;
  const cliMcpCommand = `claude mcp add isha -- python -m src.mcp_server`;
  const curlCommand = `curl -sSL https://raw.githubusercontent.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-/main/install.sh | bash`;

  const handleCopyMain = () => {
    sounds.playSuccess();
    if (activeTab === "mcp-ide") {
      navigator.clipboard.writeText(jsonConfig);
    } else if (activeTab === "mcp-cli") {
      navigator.clipboard.writeText(cliMcpCommand);
    } else {
      navigator.clipboard.writeText(curlCommand);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyClone = () => {
    sounds.playSuccess();
    navigator.clipboard.writeText(cloneCommand);
    setCopiedClone(true);
    setTimeout(() => setCopiedClone(false), 2000);
  };

  return (
    <section id="cli" className="relative py-24 px-6 md:px-12 bg-[#F9F7EF] dark:bg-black transition-colors font-black">
      <div className="max-w-5xl mx-auto space-y-10">
        <div className="text-center">
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-black uppercase tracking-tight text-black dark:text-[#F9F7EF]">
            GET ISHA
          </h2>
          <p className="mt-3 text-sm sm:text-base font-bold text-neutral-600 dark:text-neutral-400">
            Autonomous SWE-bench runner deployable via{" "}
            <ScrollHighlight variant="underline" color="sky">
              single command
            </ScrollHighlight>
          </p>
        </div>

        {/* Download & Installation Box */}
        <div className="w-full rounded-3xl bg-[#F9F7EF] dark:bg-black p-6 sm:p-10 shadow-2xl shadow-neutral-900/15 dark:shadow-black/80 text-black dark:text-[#F9F7EF] transition-colors border border-neutral-200/80 dark:border-neutral-900">
          {/* Top Bar with Tabs and Copy Button */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-neutral-300 dark:border-neutral-800">
            <div className="flex items-center gap-3">
              <Terminal className="w-6 h-6 text-black dark:text-[#F9F7EF] stroke-[3]" />
              <div className="flex items-center gap-2 flex-wrap">
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
                  onClick={() => setActiveTab("mcp-ide")}
                  className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-black uppercase tracking-wider transition-all cursor-pointer ${
                    activeTab === "mcp-ide"
                      ? "bg-black text-[#F9F7EF] dark:bg-[#F9F7EF] dark:text-black shadow-md"
                      : "bg-neutral-200/80 dark:bg-neutral-900 text-black dark:text-[#F9F7EF] hover:bg-neutral-300 dark:hover:bg-neutral-800"
                  }`}
                >
                  <Monitor className="w-3.5 h-3.5" />
                  MCP (IDE)
                </button>
                <button
                  onClick={() => setActiveTab("mcp-cli")}
                  className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-black uppercase tracking-wider transition-all cursor-pointer ${
                    activeTab === "mcp-cli"
                      ? "bg-black text-[#F9F7EF] dark:bg-[#F9F7EF] dark:text-black shadow-md"
                      : "bg-neutral-200/80 dark:bg-neutral-900 text-black dark:text-[#F9F7EF] hover:bg-neutral-300 dark:hover:bg-neutral-800"
                  }`}
                >
                  <Cpu className="w-3.5 h-3.5" />
                  MCP (CLI)
                </button>
              </div>
            </div>

            <button
              onClick={handleCopyMain}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-neutral-200/80 dark:bg-neutral-900 hover:bg-neutral-300 dark:hover:bg-neutral-800 text-black dark:text-[#F9F7EF] text-xs sm:text-sm font-black uppercase tracking-wider transition-all cursor-pointer shrink-0"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 stroke-[3] text-green-600 dark:text-green-400" />
                  <span>COPIED</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 stroke-[3]" />
                  <span>{activeTab === "mcp-ide" ? "COPY JSON" : "COPY COMMAND"}</span>
                </>
              )}
            </button>
          </div>

          {/* Tab Content Display */}
          <div className="pt-6">
            {/* 1. CURL TAB */}
            {activeTab === "curl" && (
              <div className="space-y-4">
                <p className="text-base sm:text-lg font-bold leading-relaxed text-neutral-800 dark:text-neutral-200">
                  Run the zero-touch automated installer. It clones ISHA into{" "}
                  <code className="text-red-600 dark:text-red-500 font-mono font-black">./isha-agent</code>, verifies prerequisites, sets up dependencies, and installs the CLI:
                </p>
                <div className="rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-800 p-5 font-mono text-sm sm:text-base text-black dark:text-[#F9F7EF] font-bold overflow-x-auto select-all">
                  <span className="text-red-600 dark:text-red-500 font-black">curl</span>{" "}
                  <span className="text-black dark:text-[#F9F7EF] font-bold">-sSL https://raw.githubusercontent.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-/main/install.sh | bash</span>
                </div>
              </div>
            )}

            {/* 2. MCP (IDE) TAB */}
            {activeTab === "mcp-ide" && (
              <div className="space-y-7">
                {/* Step 1: Download */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs font-black uppercase tracking-widest text-red-600 dark:text-red-500">
                        Step 1
                      </span>
                      <h3 className="text-lg sm:text-xl font-black text-neutral-950 dark:text-neutral-100 tracking-tight">
                        Download ISHA Repository
                      </h3>
                    </div>
                    <button
                      onClick={handleCopyClone}
                      className="inline-flex items-center gap-1.5 text-xs font-mono font-black uppercase text-neutral-600 dark:text-neutral-400 hover:text-red-600 dark:hover:text-red-400 transition-colors cursor-pointer"
                    >
                      {copiedClone ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-green-600 dark:text-green-400" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                  <p className="text-sm sm:text-base font-bold text-neutral-800 dark:text-neutral-200 leading-relaxed">
                    Clone the repo to your local machine and install dependencies:
                  </p>
                  <div className="rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-800 p-4 font-mono text-xs sm:text-sm text-black dark:text-[#F9F7EF] font-bold overflow-x-auto select-all leading-relaxed">
                    <div className="text-neutral-500 dark:text-neutral-400 font-normal"># Clone into isha-agent folder</div>
                    <div>git clone https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-.git isha-agent</div>
                    <div className="text-neutral-500 dark:text-neutral-400 font-normal mt-2"># Enter directory and install requirements</div>
                    <div>cd isha-agent &amp;&amp; pip install -r requirements.txt</div>
                  </div>
                </div>

                {/* Step 2: JSON Configuration */}
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs font-black uppercase tracking-widest text-red-600 dark:text-red-500">
                        Step 2
                      </span>
                      <h3 className="text-lg sm:text-xl font-black text-neutral-950 dark:text-neutral-100 tracking-tight">
                        Connect to Cursor, VS Code, Claude Desktop, Windsurf, or Zed
                      </h3>
                    </div>
                    <span className="text-xs font-mono font-bold text-neutral-500 dark:text-neutral-400 hidden sm:inline">
                      Settings &gt; MCP
                    </span>
                  </div>
                  <p className="text-sm sm:text-base font-bold text-neutral-800 dark:text-neutral-200 leading-relaxed">
                    Paste this JSON block into your IDE settings. Note that <span className="text-red-600 dark:text-red-500 font-black">&quot;cwd&quot;</span> stands for <span className="text-neutral-950 dark:text-white font-black">Current Working Directory</span> (the absolute path where you downloaded ISHA):
                  </p>

                  {/* Red & Black Syntax Highlighted JSON */}
                  <div className="relative rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-800 p-6 font-mono text-xs sm:text-sm md:text-base leading-relaxed overflow-x-auto select-all">
                    <div className="text-neutral-900 dark:text-neutral-100 font-bold">&#123;</div>
                    <div className="pl-4">
                      <span className="text-red-600 dark:text-red-500 font-black">&quot;mcpServers&quot;</span>
                      <span className="text-neutral-900 dark:text-neutral-100 font-bold">: &#123;</span>
                    </div>
                    <div className="pl-8">
                      <span className="text-red-600 dark:text-red-500 font-black">&quot;isha&quot;</span>
                      <span className="text-neutral-900 dark:text-neutral-100 font-bold">: &#123;</span>
                    </div>
                    <div className="pl-12">
                      <span className="text-red-600 dark:text-red-500 font-black">&quot;command&quot;</span>
                      <span className="text-neutral-900 dark:text-neutral-100 font-bold">: </span>
                      <span className="text-black dark:text-[#F9F7EF] font-black">&quot;python&quot;</span>
                      <span className="text-neutral-900 dark:text-neutral-100 font-bold">,</span>
                    </div>
                    <div className="pl-12">
                      <span className="text-red-600 dark:text-red-500 font-black">&quot;args&quot;</span>
                      <span className="text-neutral-900 dark:text-neutral-100 font-bold">: [</span>
                      <span className="text-black dark:text-[#F9F7EF] font-black">&quot;-m&quot;</span>
                      <span className="text-neutral-900 dark:text-neutral-100 font-bold">, </span>
                      <span className="text-black dark:text-[#F9F7EF] font-black">&quot;src.mcp_server&quot;</span>
                      <span className="text-neutral-900 dark:text-neutral-100 font-bold">],</span>
                    </div>
                    <div className="pl-12">
                      <span className="text-red-600 dark:text-red-500 font-black">&quot;cwd&quot;</span>
                      <span className="text-neutral-900 dark:text-neutral-100 font-bold">: </span>
                      <span className="text-red-600 dark:text-red-500 font-black">&quot;&lt;path-to-downloaded-isha-agent-folder&gt;&quot;</span>
                    </div>
                    <div className="pl-8 text-neutral-900 dark:text-neutral-100 font-bold">&#125;</div>
                    <div className="pl-4 text-neutral-900 dark:text-neutral-100 font-bold">&#125;</div>
                    <div className="text-neutral-900 dark:text-neutral-100 font-bold">&#125;</div>
                  </div>
                </div>
              </div>
            )}

            {/* 3. MCP (CLI) TAB */}
            {activeTab === "mcp-cli" && (
              <div className="space-y-7">
                {/* Step 1: Download */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs font-black uppercase tracking-widest text-red-600 dark:text-red-500">
                        Step 1
                      </span>
                      <h3 className="text-lg sm:text-xl font-black text-neutral-950 dark:text-neutral-100 tracking-tight">
                        Download ISHA Repository
                      </h3>
                    </div>
                    <button
                      onClick={handleCopyClone}
                      className="inline-flex items-center gap-1.5 text-xs font-mono font-black uppercase text-neutral-600 dark:text-neutral-400 hover:text-red-600 dark:hover:text-red-400 transition-colors cursor-pointer"
                    >
                      {copiedClone ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-green-600 dark:text-green-400" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                  <p className="text-sm sm:text-base font-bold text-neutral-800 dark:text-neutral-200 leading-relaxed">
                    Clone the repository and install dependencies in your environment:
                  </p>
                  <div className="rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-800 p-4 font-mono text-xs sm:text-sm text-black dark:text-[#F9F7EF] font-bold overflow-x-auto select-all leading-relaxed">
                    <div>git clone https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-.git isha-agent</div>
                    <div>cd isha-agent &amp;&amp; pip install -r requirements.txt</div>
                  </div>
                </div>

                {/* Step 2: CLI Command */}
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs font-black uppercase tracking-widest text-red-600 dark:text-red-500">
                        Step 2
                      </span>
                      <h3 className="text-lg sm:text-xl font-black text-neutral-950 dark:text-neutral-100 tracking-tight">
                        Connect to Claude Code, Gemini CLI, or Terminal Agents
                      </h3>
                    </div>
                    <span className="text-xs font-mono font-bold text-neutral-500 dark:text-neutral-400 hidden sm:inline">
                      Single Terminal Command
                    </span>
                  </div>
                  <p className="text-sm sm:text-base font-bold text-neutral-800 dark:text-neutral-200 leading-relaxed">
                    Inside your terminal (within the <code className="text-red-600 dark:text-red-500 font-mono font-black">isha-agent</code> directory), run this command to register ISHA immediately:
                  </p>
                  <div className="rounded-2xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-800 p-5 font-mono text-sm sm:text-base text-black dark:text-[#F9F7EF] font-bold overflow-x-auto select-all">
                    <span className="text-red-600 dark:text-red-500 font-black">claude</span>{" "}
                    <span className="text-black dark:text-[#F9F7EF] font-black">mcp add isha -- python -m src.mcp_server</span>
                  </div>
                </div>
              </div>
            )}
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
