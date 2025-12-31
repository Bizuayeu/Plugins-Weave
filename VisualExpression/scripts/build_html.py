#!/usr/bin/env python3
"""
Expression UI HTML Builder

Combines template HTML with Base64 image data to produce the final HTML.

Usage:
    python build_html.py [--template file] [--images file] [--output file]

Example:
    python build_html.py \
        --template ../templates/ExpressionUI.template.html \
        --images expression_images.json \
        --output ExpressionUI.html
"""

import argparse
import json
import sys
from pathlib import Path


def build(template_path: Path, images_path: Path, output_path: Path) -> None:
    """
    Build HTML by combining template with image data.

    Args:
        template_path: Path to template HTML file
        images_path: Path to JSON file containing Base64 images
        output_path: Path to output HTML file
    """
    # Validate inputs
    if not template_path.is_file():
        print(f"Error: Template file not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    if not images_path.is_file():
        print(f"Error: Images JSON not found: {images_path}", file=sys.stderr)
        sys.exit(1)

    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Read image data
    with open(images_path, 'r', encoding='utf-8') as f:
        images = json.load(f)

    # Build JavaScript object string
    # Format: key:'data:image/...base64,...',key2:'...'
    images_str = ','.join([f"{k}:'{v}'" for k, v in images.items()])

    # Check for placeholder
    placeholder = '__IMAGES_PLACEHOLDER__'
    if placeholder not in template:
        print(f"Error: Placeholder '{placeholder}' not found in template", file=sys.stderr)
        sys.exit(1)

    # Replace placeholder
    html = template.replace(placeholder, images_str)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = output_path.stat().st_size / 1024
    print(f"Built {output_path} ({size_kb:.1f} KB)")
    print(f"Embedded {len(images)} expressions")


def main():
    parser = argparse.ArgumentParser(
        description='Build Expression UI HTML from template and image data'
    )
    parser.add_argument(
        '--template', '-t',
        type=Path,
        default=Path('../templates/ExpressionUI.template.html'),
        help='Path to template HTML file'
    )
    parser.add_argument(
        '--images', '-i',
        type=Path,
        default=Path('expression_images.json'),
        help='Path to JSON file containing Base64 images'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('ExpressionUI.html'),
        help='Path to output HTML file'
    )

    args = parser.parse_args()

    build(args.template, args.images, args.output)


if __name__ == '__main__':
    main()
