"""Source extraction: URL or file -> raw text + metadata."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .errors import ReadingListError


@dataclass
class ExtractedSource:
    text: str
    title: str
    source_type: str  # 'url' | 'file'
    source: str       # the original target string
    meta: dict[str, Any]


def is_url(target: str) -> bool:
    parsed = urlparse(target)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def is_file(target: str) -> bool:
    if target.startswith(("http://", "https://")):
        return False
    return Path(os.path.expanduser(target)).is_file()


def detect(target: str) -> str:
    if is_url(target):
        return "url"
    if is_file(target):
        return "file"
    raise ReadingListError(
        f"target is neither a readable URL nor an existing file path: {target!r}"
    )


def extract_url(target: str) -> ExtractedSource:
    """Use hermes-agent's web_extract tool. Fallback: just return the URL."""
    try:
        # Lazy import: hermes-agent's tool surface isn't always importable in
        # unit tests. In production this resolves to the live web_extract tool.
        from hermes_tools import web_extract  # type: ignore

        results = web_extract(urls=[target])  # type: ignore
        page = (results.get("results") or [{}])[0]
        text = page.get("content") or ""
        title = page.get("title") or target
        return ExtractedSource(
            text=text,
            title=title,
            source_type="url",
            source=target,
            meta={"url": target, "extracted_via": "web_extract"},
        )
    except Exception as e:  # pragma: no cover — fallback path
        return ExtractedSource(
            text=f"(web_extract failed: {e}; URL noted but not extracted)\n\n{target}",
            title=target,
            source_type="url",
            source=target,
            meta={"url": target, "extracted_via": "fallback", "error": str(e)},
        )


def extract_file(target: str) -> ExtractedSource:
    path = Path(os.path.expanduser(target))
    suffix = path.suffix.lower()
    text = ""
    title = path.stem

    if suffix == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            text = "\n\n".join(page.get_text() for page in doc)
            doc.close()
        except ImportError:
            # Fallback: try pdftotext
            import subprocess
            try:
                out = subprocess.run(
                    ["pdftotext", str(path), "-"],
                    capture_output=True, text=True, timeout=60, check=False
                )
                text = out.stdout
            except (FileNotFoundError, subprocess.TimeoutExpired):
                text = path.read_text(errors="replace")
    elif suffix in (".md", ".txt", ".rst"):
        text = path.read_text(errors="replace")
    elif suffix in (".html", ".htm"):
        text = _html_to_text(path.read_text(errors="replace"))
    else:
        text = path.read_text(errors="replace")

    return ExtractedSource(
        text=text[:200_000],  # cap to 200KB raw text
        title=title,
        source_type="file",
        source=str(path),
        meta={"path": str(path), "suffix": suffix, "size": path.stat().st_size},
    )


def _html_to_text(html: str) -> str:
    """Minimal HTML -> text. Avoids extra deps; not pretty but functional."""
    import re
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</p\s*>", "\n\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", "", html)
    import html as _html
    return _html.unescape(html)


def extract(target: str) -> ExtractedSource:
    kind = detect(target)
    if kind == "url":
        return extract_url(target)
    return extract_file(target)
