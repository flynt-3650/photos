from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime
from pathlib import Path


TEXT_EXTS = {
    ".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".jsonl", ".xml", ".html", ".htm",
    ".css", ".scss", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".py", ".java", ".c",
    ".cpp", ".h", ".hpp", ".cs", ".go", ".rs", ".rb", ".php", ".yml", ".yaml", ".toml",
    ".ini", ".conf", ".log", ".sql", ".ps1", ".bat", ".sh", ".dockerfile",
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff", ".bmp"}
SKIP_DIRS = {".git", "node_modules", ".quarantine", "dupekiller-report", "__pycache__", ".venv", "venv"}


def sha256(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def fmt_size(n: int) -> str:
    x = float(n)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if x < 1024 or u == "TB":
            return f"{x:.1f} {u}" if u != "B" else f"{int(x)} B"
        x /= 1024
    return f"{n} B"


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def safe_name(s: str) -> str:
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", s).strip(" .")
    return (s or "file")[:100]


def rel_to(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    parent = path.parent
    i = 2
    while True:
        p = parent / f"{stem}.{i}{suffix}"
        if not p.exists():
            return p
        i += 1


def normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w]+", " ", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def file_url(path: str | Path) -> str:
    p = Path(path).resolve()
    raw = p.as_posix()
    if os.name == "nt" and not raw.startswith("/"):
        raw = "/" + raw
    from urllib.parse import quote
    return "file://" + quote(raw, safe="/:")
