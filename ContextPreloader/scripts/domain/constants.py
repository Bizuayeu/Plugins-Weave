"""Domain constants for ContextPreloader (Single Source of Truth)."""

DEFAULT_TEXT_EXTENSIONS: list[str] = [
    ".txt", ".md", ".json", ".yaml", ".yml", ".csv",
    ".py", ".js", ".ts", ".html", ".css", ".xml",
    ".toml", ".ini", ".cfg", ".log",
    ".sh", ".bash", ".ps1", ".bat",
]

FILE_TYPE_LABELS: dict[str, str] = {
    ".pdf": "PDF document",
    ".png": "PNG image",
    ".jpg": "JPEG image",
    ".jpeg": "JPEG image",
    ".gif": "GIF image",
    ".bmp": "BMP image",
    ".svg": "SVG image",
    ".webp": "WebP image",
    ".doc": "Word document",
    ".docx": "Word document",
    ".xls": "Excel spreadsheet",
    ".xlsx": "Excel spreadsheet",
    ".ppt": "PowerPoint presentation",
    ".pptx": "PowerPoint presentation",
    ".zip": "ZIP archive",
    ".tar": "TAR archive",
    ".gz": "Gzip archive",
    ".mp3": "MP3 audio",
    ".mp4": "MP4 video",
    ".wav": "WAV audio",
}

DEFAULT_SETTINGS: dict = {
    "encoding": "utf-8",
    "max_lines_per_file": 0,
    "show_summary": True,
    "url_timeout": 10,
}
