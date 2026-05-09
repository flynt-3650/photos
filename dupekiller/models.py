from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class FileRec:
    id: int
    path: str
    rel: str
    ext: str
    size: int
    mtime_ns: int
    sha256: str = ""
    image_hash: str | None = None
    text_hash: str | None = None
    text_sample: str | None = None
    text_features: str | None = None
    thumb: str | None = None
    error: str | None = None

    def json(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("text_features", None)
        return d

    @property
    def p(self) -> Path:
        return Path(self.path)


@dataclass
class Pair:
    left: int
    right: int
    distance: int

    def json(self) -> list[int]:
        return [self.left, self.right, self.distance]


@dataclass
class Group:
    id: str
    kind: str
    reason: str
    files: list[FileRec]
    pairs: list[Pair] = field(default_factory=list)

    @property
    def wasted_bytes(self) -> int:
        if len(self.files) < 2:
            return 0
        return sum(f.size for f in self.files) - max(f.size for f in self.files)

    def json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "reason": self.reason,
            "count": len(self.files),
            "wastedBytes": self.wasted_bytes,
            "files": [f.json() for f in self.files],
            "pairs": [p.json() for p in self.pairs],
        }
