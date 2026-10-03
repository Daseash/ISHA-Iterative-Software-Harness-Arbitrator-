# ISHA — Docker image manifest

Systematic image layout for ISHA. Two maintained images, one tag scheme,
one maintain command. Everything else Docker sees on this machine is
transient (SWE-bench eval images) and is managed by the grading step, not
here.

## Tag scheme

| Image | Tags | Purpose |
|---|---|---|
| `isha` | `latest`, `0.2.0` (pyproject version) | The agent itself: CLI (`isha fix`, `isha bench`, `isha doctor`). |
| `isha-sandbox` | `latest`, `0.2.0` | Pytest runner for `ISHA_SANDBOX_MODE=docker` verification. |

Labels on every build: `org.isha.image` (`agent` / `sandbox`) and
`org.isha.version`. Never ship an untagged image — the maintain script
prunes danglings on every run.

## Where images come from

- `isha` — built locally from `Dockerfile` (python:3.13-slim + git +
  `requirements.txt`). `.dockerignore` excludes `results/`, `data/`,
  `swebench_checkouts/`, `live_repos/`, `.env` — secrets and gigabyte
  caches can never leak into an image.
- `isha-sandbox` — built locally from `sandbox.Dockerfile`
  (python:3.13-slim + `sandbox-requirements.txt`).
- **SWE-bench eval images** (`sweb.eval.x86_64.*`, ~4 GB each) — pulled
  from Docker Hub **only during Day-5 grading** by
  `src/bench/harness_eval.py`; `cleanup_images()` deletes them afterwards
  so they never accumulate. They are NOT part of this manifest.

## Build / update

One command (Windows PowerShell, from anywhere):

```powershell
powershell -NoProfile -File scripts\docker_maintain.ps1
```

What it does: prune dangling → build `isha:<version>` + `isha:latest` →
build `isha-sandbox:<version>` + `isha-sandbox:latest` → print the
manifest. `-SkipBuild` only prunes + prints. The version is read from
`pyproject.toml` automatically.

### Manual equivalents

```powershell
docker build -t isha:latest -t isha:<ver> .                # agent
docker build -t isha-sandbox:latest -t isha-sandbox:<ver> -f sandbox.Dockerfile .
docker image prune -f                                       # drop danglings
```

## Pull / run (for anyone else)

**Preferred: the pip wheel / install scripts — see `docs/INSTALL.md`.**
`dist/isha_fix-<ver>-py3-none-any.whl` (code-only; deps from PyPI) plus
`install.ps1` / `install.sh` (one command: venv + install + `.env` template +
verification). The wheel packages the `src` top-level package explicitly
(`[tool.setuptools.packages.find]` in pyproject) so `import src.main` and the
`isha` console script survive packaging.

Docker images are private to this machine (no registry push). To hand one
over: `docker save -o isha-<ver>.tar isha:<ver>` on this machine,
`docker load -i isha-<ver>.tar` on the target.

```bash
# one-shot fix on a repo
docker run --rm -v /path/to/repo:/repo isha:latest \
  isha fix --repo /repo --issue "..." --apply

# sandbox verification
docker run --rm -v /path/to/repo:/workspace -w /workspace isha-sandbox:latest
```

## Notes / no-gos

- The official SWE-bench harness **must** run on the host (Linux Docker
  daemon / WSL2) — it cannot be nested inside `isha`. Grading therefore
  stays on the host by design.
- Disk: ~50 eval images (~4 GB each) fit at a time with the current 200 GB+
  free; grade in batches of ~50 with `docker system prune -f` between.
- `alpine` and any other third-party images on this machine are out of
  scope for this manifest.
