#!/bin/bash
set -e
cd /workspaces/ISHA-Iterative-Software-Harness-Arbitrator-
echo "[$(date)] Starting Codespace Evaluation..." >> /tmp/eval.log
nohup python3 scripts/codespaces_s5_s10_pipeline.py "$@" > /tmp/eval_output.log 2>&1 &
echo "[$(date)] Detached with PID $!" >> /tmp/eval.log
echo "Pipeline launched in background with PID $!"
