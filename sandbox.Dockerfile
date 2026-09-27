# ISHA sandbox image — pytest runner for ISHA_SANDBOX_MODE=docker.
#
#   docker build -t isha-sandbox:latest -f sandbox.Dockerfile .
#   docker compose --profile tools build sandbox
#
# Add target-repo dependencies to sandbox-requirements.txt to have them
# available inside the container.
FROM python:3.13-slim

COPY sandbox-requirements.txt /tmp/sandbox-requirements.txt

RUN pip install --no-cache-dir pytest \
    && pip install --no-cache-dir -r /tmp/sandbox-requirements.txt

WORKDIR /workspace

CMD ["python", "-m", "pytest", "-q"]
