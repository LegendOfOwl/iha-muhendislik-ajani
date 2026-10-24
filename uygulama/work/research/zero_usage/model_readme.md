---
license: apache-2.0
library_name: transformers
pipeline_tag: image-to-text
tags:
  - CAD
  - CadQuery
  - image-to-CAD
  - vision-language-model
  - 3D-reconstruction
  - code-generation
  - parametric-CAD
base_model: Qwen/Qwen3-VL-2B-Instruct
datasets:
  - ADSKAILab/Zero-To-CAD-1m
language:
  - en
  - code
---

<p align="center">
  <img src="assets/logo.png" alt="Zero-to-CAD" width="100%"/>
</p>

# Zero-to-CAD — Qwen3-VL-2B

**A vision-language model fine-tuned to reconstruct executable CAD programs from multi-view images.**

<p align="center">
  <img src="assets/agentic.png" alt="Zero-to-CAD agentic synthesis pipeline" width="800"/>
</p>

> **Zero-to-CAD: Agentic Synthesis of Interpretable CAD Programs at Million-Scale Without Real Data**
>
> [Mohammadmehdi Ataei](https://orcid.org/0000-0002-3399-9696), [Farzaneh Askari](https://orcid.org/0000-0003-0684-1102), [Kamal Rahimi Malekshan](https://orcid.org/0009-0004-1192-4724), [Pradeep Kumar Jayaraman](https://orcid.org/0000-0001-6314-6136)
>
> Autodesk Research

## Related Resources

| Resource | Link |
|----------|------|
| 📄 **Paper** | [Zero-to-CAD: Agentic Synthesis of Interpretable CAD Programs at Million-Scale Without Real Data](https://arxiv.org/abs/2604.24479) |
| 📦 **Zero-to-CAD 1M** (full dataset) | [ADSKAILab/Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) |
| 📦 **Zero-to-CAD 100K** (curated subset) | [ADSKAILab/Zero-To-CAD-100k](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-100k) |
| 🤖 **Fine-tuned Model** (this model) | You are here |
| 🗂️ **Collection** | [ADSKAILab/Zero-To-CAD](https://huggingface.co/collections/ADSKAILab/zero-to-cad) |

## Model Description

This model is a **fully fine-tuned Qwen3-VL-2B-Instruct** that takes **8 rendered views** of a 3D shape (4 front, 4 rear at 256×256) and generates **executable CadQuery Python code** that reproduces the geometry.

The model was trained entirely on **synthetic data** from Zero-to-CAD 1M (979,633 training samples) — no real-world CAD files were used.

### Key Results

| Benchmark | Success Rate | Mean IoU | Median IoU | P90 IoU |
|-----------|-------------|----------|------------|---------|
| **Zero-to-CAD test** | **82.1%** | **0.747** | **0.847** | **0.999** |
| **ABC (out-of-distribution)** | **61.0%** | **0.377** | **0.303** | **0.854** |

### Comparison with Baselines

| Model | Zero-to-CAD Success | Zero-to-CAD Mean IoU | ABC Success | ABC Mean IoU |
|-------|---------------------|---------------------|-------------|-------------|
| **This model** | **82.1%** | **0.747** | 61.0% | **0.377** |
| GPT-5.2 High | 72.2% | 0.485 | **66.2%** | 0.344 |
| GPT-5.2 Medium | 71.1% | 0.495 | 62.6% | 0.346 |
| Qwen3-VL-2B (base) | 6.6% | 0.184 | 5.4% | 0.131 |

## Quick Start

### Inference

```python
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
from datasets import load_dataset
from PIL import Image
import io


model_name = "ADSKAILab/Zero-To-CAD-Qwen3-VL-2B"
model = Qwen3VLForConditionalGeneration.from_pretrained(model_name, torch_dtype="auto", device_map="auto")
processor = AutoProcessor.from_pretrained(model_name)

# Load 8 rendered views from the dataset
ds = load_dataset("ADSKAILab/Zero-To-CAD-1m", split="train", streaming=True)
sample = next(iter(ds))
views = [
    Image.open(io.BytesIO(sample[f"image_{i}"])) if isinstance(sample[f"image_{i}"], bytes)
    else sample[f"image_{i}"]
    for i in range(8)
]

# Or load 8 views from local files:
# views = [Image.open(f"view_{i}.png") for i in range(8)]

messages = [
    {
        "role": "system",
        "content": "You are a CAD code assistant. Given multiple rendered views of a 3D shape, generate clean, well-structured CadQuery Python code that accurately reproduces the geometry."
    },
    {
        "role": "user",
        "content": [
            *[{"type": "image", "image": view} for view in views],
            {"type": "text", "text": "Generate CadQuery code for this shape."}
        ]
    }
]

text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = processor(text=text, images=views, return_tensors="pt").to(model.device)

output_ids = model.generate(**inputs, max_new_tokens=4096)
output_text = processor.batch_decode(output_ids[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]

print(output_text)
```

### Execute the generated code

```python
import cadquery as cq

exec(output_text)
# `result` contains the reconstructed CadQuery solid

# Export
cq.exporters.export(result, "output.step")
cq.exporters.export(result, "output.stl")
```

## Training Details

| Hyperparameter | Value |
|---------------|-------|
| Base model | Qwen3-VL-2B-Instruct |
| Training mode | Full fine-tuning |
| Max sequence length | 4,096 tokens |
| Optimizer | AdamW |
| Learning rate | 1 × 10⁻⁴ |
| Weight decay | 0.0 |
| LR scheduler | Cosine |
| Warmup ratio | 0.03 |
| Attention dropout | 0.1 |
| GPUs | 16 × NVIDIA H100 80GB |
| Per-GPU batch size | 1 |
| Effective batch size | 16 |
| Epochs | 3 |
| Precision | bfloat16 |
| Distributed strategy | DDP |

## Evaluation Protocol

- **Metric**: Voxelized IoU at 64³ resolution between generated and ground-truth solids
- **Rotational alignment**: Maximum IoU over 45° rotation increments
- **Success rate**: Percentage of generations producing valid, executable CadQuery code

## Intended Uses

- **Image-to-CAD reconstruction** — reconstruct editable parametric CAD from rendered views
- **Research baseline** — starting point for Image-to-Sequence CAD generation research
- **Integration** — combine with rendering pipelines for end-to-end 3D reconstruction

## Limitations

- Trained on synthetic data only; may struggle with photorealistic or noisy inputs
- Expects 8 clean rendered views at 256×256 — other configurations are untested
- Outputs CadQuery code only; other CAD formats require post-processing
- Complex multi-part assemblies may exceed the 4,096 token context window

## Citation

If you use this model, please cite:

```bibtex
@misc{ataei2026zerotocadagenticsynthesisinterpretable,
  title={Zero-to-CAD: Agentic Synthesis of Interpretable CAD Programs at Million-Scale Without Real Data}, 
  author={Mohammadmehdi Ataei and Farzaneh Askari and Kamal Rahimi Malekshan and Pradeep Kumar Jayaraman},
  year={2026},
  eprint={2604.24479},
  archivePrefix={arXiv},
  primaryClass={cs.CV},
  url={https://arxiv.org/abs/2604.24479}
}
```

## License

This model is released under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
