"""File reading utilities.

Provides line-numbered output (``cat -n`` style) and encoding detection.
"""

from __future__ import annotations

import codecs


def detect_encoding(path: str) -> str:
    """Detect the encoding of a file by checking for a BOM.

    Falls back to ``utf-8`` when no BOM is found.
    """
    bom_map: list[tuple[bytes, str]] = [
        (codecs.BOM_UTF32_LE, "utf-32-le"),
        (codecs.BOM_UTF32_BE, "utf-32-be"),
        (codecs.BOM_UTF16_LE, "utf-16-le"),
        (codecs.BOM_UTF16_BE, "utf-16-be"),
        (codecs.BOM_UTF8, "utf-8-sig"),
    ]
    try:
        with open(path, "rb") as f:
            raw = f.read(4)
        for bom, encoding in bom_map:
            if raw.startswith(bom):
                return encoding
    except OSError:
        pass
    return "utf-8"


def read_file_with_line_numbers(
    path: str,
    *,
    offset: int = 0,
    limit: int = 2000,
) -> str:
    """Read a file and return content with ``cat -n`` style line numbers.

    Parameters
    ----------
    path:
        Absolute path to the file.
    offset:
        0-based line offset (number of lines to skip from the top).
    limit:
        Maximum number of lines to return after *offset*.

    Returns
    -------
    str
        The formatted text with ``<line_no>\\t<line>`` per line.
    """
    encoding = detect_encoding(path)
    with open(path, encoding=encoding, errors="replace") as f:
        lines = f.readlines()

    selected = lines[offset : offset + limit]
    parts: list[str] = []
    for idx, line in enumerate(selected, start=offset + 1):
        # Strip trailing newline for uniform formatting then re-add
        parts.append(f"{idx:>6}\t{line.rstrip('\n')}")

    return "\n".join(parts)
