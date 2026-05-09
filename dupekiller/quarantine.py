from __future__ import annotations

import json
import shutil
from pathlib import Path

from .grouping import UF
from .utils import safe_name, stamp, unique_path


def choose(files: list[dict], keep: str) -> dict:
    if keep == "newest":
        return sorted(files, key=lambda f: f.get("mtime_ns", 0), reverse=True)[0]
    if keep == "oldest":
        return sorted(files, key=lambda f: f.get("mtime_ns", 0))[0]
    if keep == "largest":
        return sorted(files, key=lambda f: f.get("size", 0), reverse=True)[0]
    return sorted(files, key=lambda f: (len(f.get("path", "")), -f.get("size", 0)))[0]


def plan_moves(report_path: Path, keep: str = "shortest") -> tuple[Path, list[tuple[Path, Path]]]:
    data = json.loads(report_path.read_text("utf-8"))
    root = Path(data["root"])
    by_path = {}
    for g in data.get("groups", []):
        for f in g.get("files", []):
            if f.get("path"):
                by_path[f["path"]] = f

    files = list(by_path.values())
    pos = {f["path"]: i for i, f in enumerate(files)}
    uf = UF(len(files))
    for g in data.get("groups", []):
        group = [f for f in g.get("files", []) if f.get("path") in pos]
        if not group:
            continue
        first = pos[group[0]["path"]]
        for f in group[1:]:
            uf.union(first, pos[f["path"]])

    parts = {}
    for f in files:
        parts.setdefault(uf.find(pos[f["path"]]), []).append(f)

    base = root / ".quarantine" / stamp()
    moves = []
    for group in parts.values():
        if len(group) < 2:
            continue
        survivor = choose(group, keep)
        name = safe_name(Path(survivor["path"]).stem)
        for f in group:
            if f["path"] == survivor["path"]:
                continue
            dst = unique_path(base / name / f.get("rel", Path(f["path"]).name))
            moves.append((Path(f["path"]), dst))
    return base, moves


def apply_moves(moves: list[tuple[Path, Path]], apply: bool = False) -> int:
    for src, dst in moves:
        print(f"{'move' if apply else 'would move'}: {src} -> {dst}")
        if apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    return len(moves)
