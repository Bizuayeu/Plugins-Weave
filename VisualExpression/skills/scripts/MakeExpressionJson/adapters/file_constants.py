"""File-related constants for MakeExpressionJson."""

# Default filenames for output files
DEFAULT_JSON_FILENAME = "ExpressionImages.json"
DEFAULT_HTML_FILENAME = "VisualExpressionUI.html"
DEFAULT_TEMPLATE_FILENAME = "VisualExpressionUI.template.html"

# Marker files used to detect the skills directory
SKILLS_DIR_MARKERS = ["SKILL.md", "VisualExpressionUI.template.html"]

# Environment variable for skills directory override
SKILLS_DIR_ENV_VAR = "VISUAL_EXPRESSION_SKILLS_DIR"

# Maximum depth for upward marker file search.
# 10 is sufficient as plugins are typically 3-5 levels deep from workspace root.
MAX_SEARCH_DEPTH = 10
