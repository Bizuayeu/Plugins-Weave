#!/usr/bin/env python3
"""
MakeExpressionJson - Expression Grid to HTML Builder

Converts a 4x5 grid image of expressions into a self-contained HTML UI.

Usage:
    python main.py input_grid.png [--output ./output/]
    python main.py --help

Input:
    - 4 rows x 5 columns grid image (1400x1120px at 280px per cell)

Output:
    - ExpressionImages.json (Base64 encoded images)
    - VisualExpressionUI.html (Self-contained HTML)
    - VisualExpressionSkills.zip (For claude.ai upload)
"""

import argparse
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Add package directory to path for imports when run as script
_pkg_dir = Path(__file__).parent
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

from adapters.file_handler import FileHandler
from adapters.zip_packager import ZipPackager
from domain import GRID_CONFIG
from usecases.base64_encoder import Base64Encoder
from usecases.html_builder import HtmlBuilder
from usecases.image_splitter import ImageSplitter


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert expression grid image to HTML UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py character_grid.png
    python main.py character_grid.png --output ./build/
    python main.py character_grid.png --no-zip

Grid specification:
    - 4 rows x 5 columns
    - 280px x 280px per cell
    - Total: 1400px width x 1120px height
        """,
    )

    parser.add_argument(
        "input",
        type=str,
        help="Path to the grid image (4x5, 1400x1120px)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="./output",
        help="Output directory (default: ./output)",
    )

    parser.add_argument(
        "--template",
        "-t",
        type=str,
        default=None,
        help="Path to HTML template (default: auto-detect)",
    )

    parser.add_argument(
        "--quality",
        "-q",
        type=int,
        default=85,
        help="JPEG quality for encoding (default: 85)",
    )

    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip ZIP file creation",
    )

    parser.add_argument(
        "--special",
        "-s",
        type=str,
        default=None,
        help="Custom Special codes (comma-separated, 4 items). Example: --special wink,pout,smug,starry",
    )

    args = parser.parse_args()

    # Parse special codes if provided
    special_codes = None
    if args.special:
        special_codes = [code.strip() for code in args.special.split(",")]

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Initialize components
    file_handler = FileHandler(args.output)
    try:
        splitter = ImageSplitter(special_codes=special_codes)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    encoder = Base64Encoder(quality=args.quality)

    # Determine template path
    if args.template:
        template_path = Path(args.template)
    else:
        template_path = file_handler.get_default_template_path()

    if not template_path.exists():
        logger.error(f"Template file not found: {template_path}")
        sys.exit(1)

    builder = HtmlBuilder(str(template_path))

    logger.info(f"Processing: {input_path}")
    logger.info(
        f"Expected grid: {GRID_CONFIG['cols']}x{GRID_CONFIG['rows']} @ {GRID_CONFIG['cell_size']}px"
    )

    # Step 1: Split grid image
    logger.info("Step 1/4: Splitting grid image...")
    try:
        split_images = splitter.split_from_file(str(input_path))
        logger.info(f"  -> Split into {len(split_images)} expressions")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Step 2: Encode to Base64
    logger.info("Step 2/4: Encoding to Base64...")
    expression_set = encoder.encode_expressions(split_images)
    images_dict = encoder.to_json_dict(expression_set)
    logger.info(f"  -> Encoded {len(images_dict)} images")

    # Step 3: Write JSON
    logger.info("Step 3/4: Writing JSON...")
    json_path = file_handler.write_json(images_dict)
    logger.info(f"  -> {json_path}")

    # Step 4: Build HTML
    logger.info("Step 4/4: Building HTML...")
    html_content = builder.build(images_dict)
    html_path = file_handler.write_html(html_content)
    logger.info(f"  -> {html_path}")

    # Optional: Create ZIP
    if not args.no_zip:
        logger.info("Creating ZIP package...")
        packager = ZipPackager(args.output)

        # Find SKILL.md if it exists
        skill_md_path = file_handler.get_skills_dir() / "SKILL.md"

        zip_path = packager.create_skill_zip(
            skill_md_path=skill_md_path,
            html_path=html_path,
            template_path=template_path,
            json_path=json_path,
        )
        logger.info(f"  -> {zip_path}")

    logger.info("\nDone!")
    logger.info(f"Output directory: {file_handler.output_dir}")


if __name__ == "__main__":
    main()
