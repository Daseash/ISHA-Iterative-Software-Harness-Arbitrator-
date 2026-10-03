# ISHA — Install & run (CLI)

ISHA is a Python package (`isha-fix`) that installs a single command:
`isha`. Three ways to get it, best first.

## 0. Prerequisites (all methods)

- Python 3.10+ (3.13 recommended), `git` on PATH.
- API keys for the model chain (free tier is enough):
  `GROQ_API_KEY` and `GOOGLE_API_KEY` — copy `.env.example` → `.env` and fill in.
- Optional: Docker (for `ISHA_SANDBOX_MODE=docker` test execution and the
  SWE-bench grading step; the solver itself runs without Docker).

## 1. One-command install (recommended)

From the cloned repo (`isha-agent/`):

```powershell
# Windows
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
```

```bash
# Linux / macOS
bash install.sh
```

Both scripts: create `.venv/`, install the wheel from `dist/` (or the source
tree if no wheel), copy `.env.example` → `.env`, and verify the CLI.

```powershell
.venv\Scripts\isha doctor        # Windows
```

```bash
source .venv/bin/activate && isha doctor   # Linux/macOS
```

## 2. Plain pip (no scripts)

```bash
pip install "dist/isha_fix-0.2.0-py3-none-any.whl"   # wheel
# or
pip install .                                          # source tree
```

The wheel is code-only (~190 KB); dependencies (langgraph, litellm, laya,
swebench, …) resolve from PyPI. First install downloads a few hundred MB
(torch via docling is the bulk).

## 3. Docker (no Python needed on the host)

```bash
# one-shot fix on a repo
docker build -t isha .
docker run --rm -v /path/to/repo:/repo isha:latest \
  isha fix --repo /repo --issue "..." --apply

# benchmark host (bring in your .env)
docker run --rm -v ${PWD}:/app -e GROQ_API_KEY=... isha:latest \
  isha bench --limit 300 --run-id myrun
```

Images + tag scheme + maintenance: `docs/DOCKER_IMAGES.md`.

## First run checklist

```bash
isha doctor                 # keys, git, disk, model reachability -> ALL CLEAR
isha fix --repo <path> --issue "Bug: ..." --apply
isha bench --limit 10 --slice head --run-id smoke   # cheap benchmark probe
isha report --run-id smoke  # results table
```

## Notes

- The official SWE-bench grading step (`isha bench --eval`) needs a host
  Docker daemon (Linux or WSL2) and ~4 GB per eval image; it cannot run
  nested inside the `isha` container.
- `isha ui` (Streamlit dashboard) and the Qdrant vector store are optional;
  the pipeline falls back to in-memory embeddings when Qdrant is absent.
