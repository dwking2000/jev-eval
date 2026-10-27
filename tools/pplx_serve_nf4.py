"""Serve pplx-decider-v1.1-27b on a 24 GB GPU: Perplexity's own autojev code, weights quantized to NF4 at load.

Their DecisionModel loads the backbone with Qwen3_5Model.from_pretrained(checkpoint, dtype=bf16). We wrap that one
call to add a bitsandbytes 4-bit config and place it on GPU 0; nothing else in their code is changed.
Run with the pplx venv:  python tools/pplx_serve_nf4.py  (env: PPLX_DIR, PORT)
"""
import os
import sys

PPLX_DIR = os.environ.get("PPLX_DIR", r"D:\models\pplx-decider-v1.1-27b")
sys.path.insert(0, os.path.join(PPLX_DIR, "source", "src"))
os.environ.setdefault("AUTOJEV_CHECKPOINT", PPLX_DIR)
os.environ.setdefault("AUTOJEV_HOST", "127.0.0.1")
os.environ.setdefault("PORT", "8767")

import torch
from transformers import BitsAndBytesConfig
from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5Model

_orig = Qwen3_5Model.from_pretrained.__func__


def _nf4(cls, path, *args, **kwargs):
    kwargs["quantization_config"] = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    kwargs["device_map"] = {"": 0}
    return _orig(cls, path, *args, **kwargs)


Qwen3_5Model.from_pretrained = classmethod(_nf4)

import uvicorn  # noqa: E402

from autojev.server import app  # noqa: E402

uvicorn.run(app, host=os.environ["AUTOJEV_HOST"], port=int(os.environ["PORT"]))
