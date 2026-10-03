# ISHA application container — runs the CLI inside an image.
#
# Two ways to use it:
#   1. One-shot fix on a mounted repo:
#        docker build -t isha .
#        docker run --rm -v C:\code\myrepo:/repo isha \
#            isha fix --repo /repo --issue "..." --apply
#   2. Benchmark host (bring in your .env):
#        docker run --rm -v ${PWD}/isha-agent:/app -e KEY=... isha \
#            isha bench --limit 300 --run-id lite300
#
# Note: the official SWE-bench harness itself must run on a host with a
# Linux Docker daemon (or under WSL2); it cannot be nested inside this
# container. The grading step therefore stays on the host — by design.

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# git first: worktrees, checkouts and patch regeneration all need it.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
RUN pip install --no-cache-dir --no-deps .

COPY . .

# Deterministic LF behaviour for container-written harness files.
ENV ISHA_SANDBOX_MODE=local

ENTRYPOINT ["isha"]
CMD ["--help"]
