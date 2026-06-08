"""Convert downloaded note files to Markdown via pandoc.

`.md` files pass through unchanged; `.docx`/`.odt` (and exported Google Docs,
which we hand off as `.docx`) are converted to GitHub-flavored Markdown.
pandoc is a system binary — see README for installation.
"""

import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Raised when pandoc fails to convert a file."""


def to_markdown(content: bytes, ext: str) -> str:
    """Convert raw file bytes of the given extension to a Markdown string.

    Args:
        content: the raw bytes of the source file.
        ext: lowercase file extension including the dot (".docx", ".odt", ".md").

    Returns:
        The Markdown text.
    """
    if ext == ".md":
        return content.decode("utf-8", errors="replace")

    # pandoc infers the input format from the temp file's extension.
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["pandoc", tmp_path, "-t", "gfm", "--wrap=none"],
            capture_output=True,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            raise ConversionError(f"pandoc failed for {ext} file: {stderr}")
        return result.stdout.decode("utf-8", errors="replace")
    finally:
        os.remove(tmp_path)
