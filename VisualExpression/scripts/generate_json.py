#!/usr/bin/env python3
"""
Expression Images JSON Generator

Converts image files in a folder to a Base64-encoded JSON file.

Usage:
    python generate_json.py <image_folder> [--output expression_images.json]

Example:
    python generate_json.py ~/images/avatar/ --output expression_images.json
"""

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path


def extract_key_from_filename(filename: str) -> str | None:
    """
    Extract expression key from filename.

    Expected patterns:
    - {prefix}_{number}_{key}.{ext} -> key
    - Examples:
      - Avatar_01_normal.jpg -> normal
      - Weave_05_joy.jpg -> joy
    """
    # Pattern: anything_digits_key.extension
    match = re.match(r'.+_\d+_(\w+)\.(jpg|jpeg|png)$', filename.lower())
    if match:
        return match.group(1)
    return None


def get_mime_type(filepath: Path) -> str:
    """Determine MIME type from file extension."""
    ext = filepath.suffix.lower()
    if ext in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    elif ext == '.png':
        return 'image/png'
    else:
        return 'application/octet-stream'


def encode_image(filepath: Path) -> str:
    """Encode image file to Base64 data URI."""
    with open(filepath, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')

    mime = get_mime_type(filepath)
    return f"data:{mime};base64,{data}"


def generate_json(folder: Path, output: Path) -> None:
    """
    Generate JSON file from images in folder.

    Args:
        folder: Path to folder containing image files
        output: Path to output JSON file
    """
    if not folder.is_dir():
        print(f"Error: {folder} is not a directory", file=sys.stderr)
        sys.exit(1)

    images = {}

    # Supported extensions
    extensions = {'.jpg', '.jpeg', '.png'}

    # Process files in sorted order
    for filepath in sorted(folder.iterdir()):
        if filepath.suffix.lower() not in extensions:
            continue

        key = extract_key_from_filename(filepath.name)
        if key:
            images[key] = encode_image(filepath)
            print(f"  Added: {key} <- {filepath.name}")
        else:
            print(f"  Skipped (no key found): {filepath.name}")

    if not images:
        print("\nError: No valid images found", file=sys.stderr)
        print("Ensure filenames follow the pattern: {prefix}_{number}_{key}.{ext}")
        sys.exit(1)

    # Write JSON
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(images, f)

    size_kb = output.stat().st_size / 1024
    print(f"\nGenerated {output} ({size_kb:.1f} KB)")
    print(f"Total expressions: {len(images)}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate Base64 JSON from image files'
    )
    parser.add_argument(
        'folder',
        type=Path,
        help='Path to folder containing image files'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('expression_images.json'),
        help='Output JSON file path (default: expression_images.json)'
    )

    args = parser.parse_args()

    print(f"Scanning {args.folder}...\n")
    generate_json(args.folder, args.output)


if __name__ == '__main__':
    main()
