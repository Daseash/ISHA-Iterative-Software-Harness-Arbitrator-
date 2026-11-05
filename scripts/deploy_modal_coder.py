"""Deploy ISHA-Coder-7B-DPO as a scale-to-zero vLLM endpoint on Modal.

Run once:
    pip install modal
    modal setup
    modal secret create isha-coder-secret ISHA_ENDPOINT_KEY=<long-random-value>
    modal deploy scripts/deploy_modal_coder.py

Then set ISHA_MODAL_VLLM_URL / ISHA_ENDPOINT_KEY in ISHA's environment.
Scales to $0 after two minutes of inactivity.
"""

import os

import modal

MODEL_NAME = os.getenv("ISHA_CODER_HF_REPO", "Maddy-Das/isha-qwen2.5-coder-7b-dpo")

vllm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm>=0.11.2", "huggingface_hub[hf_transfer]")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

app = modal.App("isha-coder-7b-serverless")
hf_cache_vol = modal.Volume.from_name("isha-hf-cache", create_if_missing=True)


@app.function(
    image=vllm_image,
    gpu="L4",
    scaledown_window=120,  # $0 after 2 minutes idle
    volumes={"/root/.cache/huggingface": hf_cache_vol},
    max_containers=2,
    secrets=[modal.Secret.from_name("isha-coder-secret")],
)
@modal.web_server(port=8000, startup_timeout=300)
def serve_vllm():
    import subprocess

    endpoint_key = os.environ["ISHA_ENDPOINT_KEY"]
    cmd = [
        "vllm", "serve", MODEL_NAME,
        "--host", "0.0.0.0",
        "--port", "8000",
        "--max-model-len", "8192",
        "--dtype", "half",
        "--served-model-name", "isha-coder-7b-dpo",
        # Server-side auth: the client-side api_key in model_router.py does not
        # protect a public URL. Without --api-key anyone who finds the endpoint
        # can burn the free Modal credits.
        "--api-key", endpoint_key,
    ]
    subprocess.Popen(cmd)
