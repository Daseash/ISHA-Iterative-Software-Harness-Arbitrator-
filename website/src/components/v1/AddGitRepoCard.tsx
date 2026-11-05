import React, { useState } from "react";
import { FolderGit2, GitBranch, KeyRound, Check, ArrowRight } from "lucide-react";
import { GithubIcon } from "./skiper16";
import { sounds } from "../../utils/sound";

export const AddGitRepoCard: React.FC = () => {
  const [repoUrl, setRepoUrl] = useState("https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-");
  const [branch, setBranch] = useState("main");
  const [token, setToken] = useState("");
  const [status, setStatus] = useState<"idle" | "connecting" | "connected">("idle");

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    setStatus("connecting");
    setTimeout(() => {
      setStatus("connected");
      sounds.playSuccess();
    }, 1200);
  };

  const sampleRepos = [
    { label: "ISHA Core", url: "https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-" },
    { label: "FastAPI", url: "https://github.com/tiangolo/fastapi" },
    { label: "Flask", url: "https://github.com/pallets/flask" },
  ];

  return (
    <div className="w-full flex flex-col h-[650px] rounded-3xl bg-[#F9F7EF] dark:bg-black p-6 md:p-8 shadow-2xl shadow-neutral-900/10 dark:shadow-black/70 text-black dark:text-[#F9F7EF] font-black transition-colors justify-between border border-neutral-300 dark:border-neutral-800">
      {/* Header Bar */}
      <div className="pb-5 border-b border-neutral-300 dark:border-neutral-800">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-neutral-200/80 dark:bg-neutral-900 text-red-600 shadow-sm">
            <FolderGit2 className="w-6 h-6 stroke-[3]" />
          </div>
          <div>
            <h3 className="text-2xl font-black text-red-600 uppercase tracking-tight">
              ADD YOUR GIT REPOSITORY
            </h3>
            <p className="text-xs uppercase tracking-wider text-neutral-400 font-mono mt-0.5">
              Connect Remote Repo to ISHA Harness
            </p>
          </div>
        </div>
      </div>

      {/* Main Interactive Form */}
      <form onSubmit={handleConnect} className="flex-1 flex flex-col justify-center space-y-4 py-4">
        {/* Repo URL Input */}
        <div className="space-y-1.5">
          <label className="text-xs font-mono uppercase tracking-wider text-neutral-600 dark:text-neutral-400 flex items-center gap-2">
            <GithubIcon className="w-3.5 h-3.5" />
            <span>Repository Git URL</span>
          </label>
          <div className="relative flex items-center">
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => {
                setRepoUrl(e.target.value);
                if (status === "connected") setStatus("idle");
              }}
              placeholder="https://github.com/username/repository"
              className="w-full bg-neutral-200/70 dark:bg-neutral-900 text-black dark:text-[#F9F7EF] px-4 py-3 rounded-xl text-sm font-mono font-bold focus:outline-hidden focus:ring-2 focus:ring-red-600 transition-all border border-neutral-300/60 dark:border-neutral-800"
            />
          </div>
        </div>

        {/* Quick Pick Samples */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] uppercase font-mono text-neutral-500 dark:text-neutral-400">Quick Fill:</span>
          {sampleRepos.map((sample) => (
            <button
              key={sample.label}
              type="button"
              onClick={() => {
                setRepoUrl(sample.url);
                if (status === "connected") setStatus("idle");
              }}
              className="text-[10px] font-mono uppercase px-2.5 py-1 rounded-lg bg-neutral-200/80 hover:bg-neutral-300 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-800 dark:text-neutral-200 transition-colors"
            >
              {sample.label}
            </button>
          ))}
        </div>

        {/* Branch Input */}
        <div className="space-y-1.5">
          <label className="text-xs font-mono uppercase tracking-wider text-neutral-600 dark:text-neutral-400 flex items-center gap-2">
            <GitBranch className="w-3.5 h-3.5" />
            <span>Target Branch</span>
          </label>
          <input
            type="text"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            placeholder="main"
            className="w-full bg-neutral-200/70 dark:bg-neutral-900 text-black dark:text-[#F9F7EF] px-4 py-3 rounded-xl text-sm font-mono font-bold focus:outline-hidden focus:ring-2 focus:ring-red-600 transition-all border border-neutral-300/60 dark:border-neutral-800"
          />
        </div>

        {/* Access Token (Optional) */}
        <div className="space-y-1.5">
          <label className="text-xs font-mono uppercase tracking-wider text-neutral-600 dark:text-neutral-400 flex items-center gap-2">
            <KeyRound className="w-3.5 h-3.5" />
            <span>Access Token (Optional for Private Repos)</span>
          </label>
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
            className="w-full bg-neutral-200/70 dark:bg-neutral-900 text-black dark:text-[#F9F7EF] px-4 py-3 rounded-xl text-sm font-mono font-bold focus:outline-hidden focus:ring-2 focus:ring-red-600 transition-all border border-neutral-300/60 dark:border-neutral-800"
          />
        </div>

        {/* Submit Action Button */}
        <button
          type="submit"
          disabled={status === "connecting"}
          className={`w-full py-3.5 px-6 rounded-xl font-black uppercase text-sm tracking-wider flex items-center justify-center gap-2 shadow-lg transition-all duration-300 ${
            status === "connected"
              ? "bg-green-600 text-white shadow-green-600/30"
              : status === "connecting"
              ? "bg-neutral-400 text-neutral-800 cursor-not-allowed"
              : "bg-red-600 hover:bg-red-700 text-white shadow-red-600/30 hover:scale-[1.01]"
          }`}
        >
          {status === "connecting" ? (
            <span>INDEXING AST & REPO...</span>
          ) : status === "connected" ? (
            <>
              <Check className="w-4 h-4 stroke-[3]" />
              <span>REPOSITORY CONNECTED</span>
            </>
          ) : (
            <>
              <span>CONNECT REPOSITORY</span>
              <ArrowRight className="w-4 h-4 stroke-[3]" />
            </>
          )}
        </button>
      </form>

      {/* Footer Info Cards */}
      <div className="pt-4 border-t border-neutral-300 dark:border-neutral-800 grid grid-cols-3 gap-2 text-center">
        <div className="p-2 rounded-xl bg-neutral-200/70 dark:bg-neutral-900 border border-neutral-300/50 dark:border-neutral-800">
          <div className="text-[10px] font-mono text-neutral-500 dark:text-neutral-400 uppercase">STEP 1</div>
          <div className="text-xs font-black text-black dark:text-[#F9F7EF] uppercase mt-0.5">AST MAP</div>
        </div>
        <div className="p-2 rounded-xl bg-neutral-200/70 dark:bg-neutral-900 border border-neutral-300/50 dark:border-neutral-800">
          <div className="text-[10px] font-mono text-neutral-500 dark:text-neutral-400 uppercase">STEP 2</div>
          <div className="text-xs font-black text-black dark:text-[#F9F7EF] uppercase mt-0.5">SYNTHESIS</div>
        </div>
        <div className="p-2 rounded-xl bg-neutral-200/70 dark:bg-neutral-900 border border-neutral-300/50 dark:border-neutral-800">
          <div className="text-[10px] font-mono text-neutral-500 dark:text-neutral-400 uppercase">STEP 3</div>
          <div className="text-xs font-black text-black dark:text-[#F9F7EF] uppercase mt-0.5">AUTO PATCH</div>
        </div>
      </div>
    </div>
  );
};

export default AddGitRepoCard;
