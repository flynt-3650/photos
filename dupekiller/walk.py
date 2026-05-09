from __future__ import annotations

from pathlib import Path
from .utils import SKIP_DIRS


def iter_files(root: Path, out_dir: Path | None = None):
    root = root.resolve()
    out_dir = out_dir.resolve() if out_dir else None
    stack = [root]
    while stack:
        cur = stack.pop()
        try:
            items = list(cur.iterdir())
        except OSError:
            continue
        for p in items:
            name = p.name
            try:
                if p.is_dir():
                    rp = p.resolve()
                    if name in SKIP_DIRS:
                        continue
                    if out_dir and rp == out_dir:
                        continue
                    stack.append(p)
                elif p.is_file():
                    yield p
            except OSError:
                continue
