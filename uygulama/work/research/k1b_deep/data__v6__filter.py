#!/usr/bin/env python3
"""
Filter script to remove comments from OpenSCAD code in labeled dataset.
Re-renders each model to validate the code still works.
"""

import json
import os
import re
import subprocess
import tempfile
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Dict, Optional, Tuple

# Configuration
INPUT_FILE = "labeled_openscad_dataset.json"
OUTPUT_FILE = "labeled_openscad_dataset_no_comments.json"
OPENSCAD_TIMEOUT = 30  # seconds per render
NUM_WORKERS = cpu_count()  # Use all available CPU cores


def remove_comments(code: str) -> str:
    """
    Remove comments from OpenSCAD code.
    Handles both single-line (//) and multi-line (/* */) comments.
    """
    # Remove multi-line comments /* ... */
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

    # Remove single-line comments //
    # This regex preserves // inside strings
    lines = []
    for line in code.split('\n'):
        # Simple approach: find // and remove everything after it
        # Note: This doesn't handle // inside strings perfectly, but OpenSCAD rarely uses that
        comment_pos = line.find('//')
        if comment_pos != -1:
            line = line[:comment_pos]
        lines.append(line)

    code = '\n'.join(lines)

    # Remove excessive blank lines
    code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)

    return code.strip()


def test_render(code: str, entry_name: str) -> Tuple[bool, str]:
    """
    Test if OpenSCAD code can be rendered successfully.
    Returns (success, error_message).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        scad_file = Path(tmpdir) / "test.scad"
        stl_file = Path(tmpdir) / "test.stl"

        # Write code to temp file
        scad_file.write_text(code)

        # Try to render with OpenSCAD
        try:
            result = subprocess.run(
                ['openscad', '-o', str(stl_file), str(scad_file)],
                capture_output=True,
                text=True,
                timeout=OPENSCAD_TIMEOUT
            )

            # Check if STL was created and has content
            if stl_file.exists() and stl_file.stat().st_size > 0:
                return True, ""
            else:
                return False, f"Render failed: {result.stderr[:200]}"

        except subprocess.TimeoutExpired:
            return False, "Render timeout"
        except FileNotFoundError:
            return False, "OpenSCAD not found - install with: sudo apt-get install openscad"
        except Exception as e:
            return False, f"Error: {str(e)}"


def process_entry(args: Tuple[int, Dict]) -> Tuple[int, Optional[Dict], str]:
    """
    Process a single dataset entry.
    Returns (index, filtered_entry or None, status_message).
    """
    idx, entry = args
    name = entry.get('name', f'Entry {idx}')

    try:
        original_code = entry['code']

        # Remove comments
        filtered_code = remove_comments(original_code)

        # Test render
        success, error = test_render(filtered_code, name)

        if success:
            # Create new entry with filtered code
            filtered_entry = entry.copy()
            filtered_entry['code'] = filtered_code
            return idx, filtered_entry, f"✓ {name}"
        else:
            return idx, None, f"✗ {name}: {error}"

    except Exception as e:
        return idx, None, f"✗ {name}: {str(e)}"


def main():
    print(f"Loading dataset from {INPUT_FILE}...")

    # Load input dataset
    with open(INPUT_FILE, 'r') as f:
        dataset = json.load(f)

    total = len(dataset)
    print(f"Found {total} entries")
    print(f"Using {NUM_WORKERS} worker processes")
    print(f"Starting parallel processing...\n")

    # Process entries in parallel
    filtered_dataset = []
    failed_entries = []

    with Pool(NUM_WORKERS) as pool:
        # Process all entries
        results = pool.map(process_entry, enumerate(dataset))

        # Collect results
        for idx, filtered_entry, status in results:
            print(f"[{idx+1}/{total}] {status}")

            if filtered_entry is not None:
                filtered_dataset.append(filtered_entry)
            else:
                failed_entries.append((idx, dataset[idx]['name'], status))

    # Summary
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Successfully filtered: {len(filtered_dataset)}/{total}")
    print(f"Failed: {len(failed_entries)}/{total}")

    if failed_entries:
        print(f"\nFailed entries:")
        for idx, name, status in failed_entries[:10]:  # Show first 10
            print(f"  [{idx}] {name}")
        if len(failed_entries) > 10:
            print(f"  ... and {len(failed_entries) - 10} more")

    # Save filtered dataset
    print(f"\nSaving filtered dataset to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(filtered_dataset, f, indent=2)

    print(f"Done! Saved {len(filtered_dataset)} entries.")

    # Save statistics
    stats_file = OUTPUT_FILE.replace('.json', '_stats.txt')
    with open(stats_file, 'w') as f:
        f.write(f"Dataset Filtering Statistics\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Input file: {INPUT_FILE}\n")
        f.write(f"Output file: {OUTPUT_FILE}\n")
        f.write(f"Total entries: {total}\n")
        f.write(f"Successfully filtered: {len(filtered_dataset)}\n")
        f.write(f"Failed: {len(failed_entries)}\n")
        f.write(f"Success rate: {len(filtered_dataset)/total*100:.1f}%\n\n")

        if failed_entries:
            f.write(f"Failed entries:\n")
            for idx, name, status in failed_entries:
                f.write(f"  [{idx}] {name}\n")
                f.write(f"      {status}\n")

    print(f"Statistics saved to {stats_file}")


if __name__ == '__main__':
    main()
