#!/usr/bin/env python3
"""
Simple inference script to evaluate model output quality
Tests for repetition issues and generation quality
"""
import os
import json
import re
import subprocess
import tempfile
from unsloth import FastModel
import torch

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

model_config = config['model_config']
inference_config = config['inference_config']

HUB_MODEL_NAME = model_config['hub_model_name']
MAX_SEQ_LENGTH = model_config['max_seq_length']
MAX_NEW_TOKENS = inference_config['max_new_tokens']
TEMPERATURE = inference_config['temperature']
TOP_P = inference_config['top_p']
TOP_K = inference_config['top_k']
DO_SAMPLE = inference_config['do_sample']

# Set CUDA environment variables for compatibility
os.environ["TORCH_USE_CUDA_DSA"] = "1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
os.environ["TORCH_INDUCTOR"] = "0"
os.environ["TORCHINDUCTOR_MAX_AUTOTUNE"] = "0"
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# Disable Triton and dynamic compilation
torch._dynamo.config.suppress_errors = True
torch._dynamo.reset()
torch._dynamo.config.disable = True

# =============================================================================
# OPENSCAD CODE EXTRACTION AND RENDERING
# =============================================================================

def extract_scad_code(text):
    """Extract OpenSCAD code from model output."""
    # Try to find code blocks first (``` or ''')
    patterns = [
        r"```(?:openscad|scad)?\s*(.*?)```",  # Markdown code blocks
        r"'''(.*?)'''",  # Python-style triple quotes
        r"```(.*?)```",  # Generic code blocks
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()

    # If no code blocks found, assume the entire output is code
    return text.strip()

def clean_scad_code(code):
    """Clean up SCAD code by removing metadata and comments."""
    lines = code.split('\n')
    cleaned_lines = []
    skip_header = True

    for line in lines:
        stripped = line.strip()

        # Skip metadata lines starting with *
        if stripped.startswith('*'):
            continue

        # Skip header comments at the beginning
        if skip_header:
            if stripped.startswith('//') or stripped == '':
                continue
            else:
                skip_header = False

        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines).strip()

def try_render_scad(code):
    """Try to render SCAD code using OpenSCAD. Returns (success, error_message)."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            f.write(code)
            scad_file = f.name

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            stl_file = f.name

        # Try to render with OpenSCAD
        result = subprocess.run(
            ['openscad', '-o', stl_file, scad_file],
            capture_output=True,
            timeout=30,
            text=True
        )

        # Clean up temp files
        os.unlink(scad_file)
        if os.path.exists(stl_file):
            os.unlink(stl_file)

        if result.returncode == 0:
            return True, None
        else:
            # Return stderr for debugging
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Timeout: rendering took too long (>30s)"
    except Exception as e:
        return False, str(e)

print("="*70)
print("LOADING MODEL FOR EVALUATION")
print("="*70)

# Load the fine-tuned model
model, tokenizer = FastModel.from_pretrained(
    model_name=HUB_MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    load_in_4bit=True,
)

print(f"✓ Model loaded: {HUB_MODEL_NAME}\n")

# Test prompt
test_prompt = "hey cadmonkey, make me a round table"

print("="*70)
print("EVALUATION TEST")
print("="*70)
print(f"Prompt: {test_prompt}\n")

# Prepare the message in chat format
messages = [
    {"role": "user", "content": test_prompt}
]

text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
).removeprefix('<bos>')

inputs = tokenizer(text, return_tensors="pt").to("cuda")

# Test different repetition penalty values
repetition_penalties = [1.0, 1.1, 1.15, 1.2]

for rep_penalty in repetition_penalties:
    print(f"\n{'─'*70}")
    print(f"Repetition Penalty: {rep_penalty}")
    print('─'*70)

    outputs = model.generate(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_new_tokens=MAX_NEW_TOKENS,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        top_k=TOP_K,
        do_sample=DO_SAMPLE,
        repetition_penalty=rep_penalty,
        pad_token_id=tokenizer.eos_token_id,
        use_cache=False,
    )

    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract only the assistant's response
    if "<start_of_turn>model" in generated_text:
        response = generated_text.split("<start_of_turn>model")[-1].strip()
        response = response.replace("<end_of_turn>", "").strip()
    else:
        response = generated_text

    print(f"Output:\n{response}")

    # Analyze repetition
    words = response.split()
    unique_words = len(set(words))
    total_words = len(words)
    repetition_ratio = (total_words - unique_words) / max(total_words, 1)

    print(f"\nText Analysis:")
    print(f"  - Total words: {total_words}")
    print(f"  - Unique words: {unique_words}")
    print(f"  - Repetition ratio: {repetition_ratio:.2%}")

    # Extract and validate OpenSCAD code
    print(f"\nOpenSCAD Validation:")
    extracted_code = extract_scad_code(response)
    cleaned_code = clean_scad_code(extracted_code)

    if cleaned_code:
        print(f"  - Code extracted: ✓ ({len(cleaned_code)} chars)")
        print(f"  - Attempting to render...")

        success, error = try_render_scad(cleaned_code)

        if success:
            print(f"  - Rendering: ✓ SUCCESS - Code is valid OpenSCAD!")
        else:
            print(f"  - Rendering: ✗ FAILED")
            if error:
                # Show first 200 chars of error
                error_preview = error[:200] + "..." if len(error) > 200 else error
                print(f"  - Error: {error_preview}")
    else:
        print(f"  - Code extracted: ✗ No code found in output")

print("\n" + "="*70)
print("EVALUATION COMPLETE")
print("="*70)
print("\nRecommendation:")
print("Choose the repetition_penalty value that produces the most coherent")
print("output without excessive repetition. Typically 1.1-1.15 works well.")
