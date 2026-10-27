# Deploying jev-style on EKS

Status: **written but not built or applied.** The Docker daemon was not running when this was authored, so the Dockerfile and manifests are untested (the kustomize render and YAML parse are the only checks done). First build, a CPU latency check and a test deploy are still needed.

## Build
```sh
# CPU (default). Build for the node arch; x86 nodes: --platform linux/amd64
docker build -t REGISTRY/jev-style:0.8b-cpu deploy
# GPU (CUDA 12.8 wheels; node needs the NVIDIA driver + device plugin)
docker build -t REGISTRY/jev-style:0.8b-gpu --build-arg TORCH_INDEX=https://download.pytorch.org/whl/cu128 deploy
# 2B instead of 0.8B: --build-arg RELEASE=2b
```
Weights are baked in (`jev-style download`, pinned revision) and the container runs with `HF_HUB_OFFLINE=1`, so pods need no internet at start. Push to ECR.

## Deploy
```sh
kubectl create secret generic jev-style --from-literal=api-key="$(openssl rand -hex 32)"
# edit image: in deployment-cpu.yaml (or switch kustomization.yaml to deployment-gpu.yaml)
kubectl apply -k deploy/k8s
kubectl label ns <client-namespace> jev-client=true     # NetworkPolicy allow-list
```
Smoke test (from an allowed pod): `curl -H "Authorization: Bearer $KEY" http://jev-style/healthz`, then POST `/v1/systemone` (see the jev-style README for the request shape).

## Choices and open items
- **CPU vs GPU.** CPU first. All published speed numbers are GPU/MLX; CPU latency is unmeasured. Benchmark a pod (or `docker run`) with `jev-style eval` on `synth/v2/p_eval.jsonl` and look at p50/p95 before deciding. GPU only if CPU is too slow, or for the 2B.
- **Idle cost.** `replicas: 1` on a small node is cheapest and simplest. Scale-to-zero (KEDA/Knative + Karpenter) is possible but adds node cold starts of minutes; only do it if the idle node cost matters.
- **Resources** (2 CPU / 4 Gi request) are estimates; tune from observed use. fp32 0.8B is ~3 GB resident.
- **Auth.** The server requires a Bearer key (`--api-key-env`). The API is `/v1/systemone`, not OpenAI-compatible, and LiteLLM cannot proxy it. For a friendlier interface, put a small shim in front (e.g. `POST /classify` with confidence thresholds and an LLM fallback via LiteLLM).
- **Not included:** Ingress/ALB, HPA, PodDisruptionBudget, image scanning, ECR repo; add per your cluster standards.
- **Licenses.** jev-style code and weights are Apache-2.0 (derived from Qwen3.5). pplx-decider's license was not reviewed here; check before any company use.
