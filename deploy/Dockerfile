# jev-style decision-model service (PyTorch backend). Weights are baked into the image so pods start without internet/HF access.
#   CPU: docker build -t jev-style:0.8b-cpu .
#   GPU: docker build -t jev-style:0.8b-gpu --build-arg TORCH_INDEX=https://download.pytorch.org/whl/cu128 .
#   2B : add --build-arg RELEASE=2b
# Build for the node architecture (e.g. --platform linux/amd64 on x86 EKS nodes).
FROM python:3.12-slim

ARG TORCH_INDEX=https://download.pytorch.org/whl/cpu
ARG JEV_VERSION=0.5.0
ARG RELEASE=0.8b

ENV PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1 HF_HOME=/models JEV_STYLE_RELEASE=${RELEASE} JEV_STYLE_BACKEND=torch

# torch first from the chosen index, so jev-style's torch requirement is already satisfied
RUN pip install --index-url ${TORCH_INDEX} "torch>=2.4" \
 && pip install "jev-style[torch]==${JEV_VERSION}"

# bake the weights (pinned revision is enforced by jev-style)
RUN jev-style download --backend torch --release ${RELEASE} && chmod -R a+rX /models

RUN useradd -u 10001 -m jev
USER 10001
ENV HF_HUB_OFFLINE=1
EXPOSE 8765

# JEV_API_KEY (from a Secret) is required: Authorization: Bearer <key>. JEV_DEVICE: cpu | cuda
CMD ["sh", "-c", "exec jev-style serve --host 0.0.0.0 --port 8765 --device ${JEV_DEVICE:-cpu} --api-key-env JEV_API_KEY"]
