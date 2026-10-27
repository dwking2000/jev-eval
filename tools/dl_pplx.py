from huggingface_hub import snapshot_download
p = snapshot_download("perplexity-ai/pplx-decider-v1.1-27b", local_dir=r"D:\models\pplx-decider-v1.1-27b",
                      allow_patterns=["*.safetensors", "*.json", "*.jinja", "LICENSE", "NOTICE", "README.md", "source/**"])
print("DONE", p)
