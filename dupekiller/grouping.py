from __future__ import annotations

from collections import defaultdict
from .models import FileRec, Group, Pair


class UF:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[b] = a


def hamming(a: str, b: str) -> int:
    return (int(a, 16) ^ int(b, 16)).bit_count()


def exact_groups(files: list[FileRec]) -> list[Group]:
    buckets = defaultdict(list)
    for f in files:
        if f.sha256:
            buckets[(f.size, f.sha256)].append(f)
    out = []
    for i, group in enumerate([x for x in buckets.values() if len(x) > 1], 1):
        out.append(Group(f"exact-{i}", "exact", "same sha256", sorted(group, key=lambda x: x.path)))
    return out


def near_hash_groups(files: list[FileRec], attr: str, threshold: int, kind: str, reason: str) -> list[Group]:
    items = [f for f in files if getattr(f, attr)]
    uf = UF(len(items))
    pairs: list[Pair] = []
    for i, a in enumerate(items):
        av = getattr(a, attr)
        for j in range(i + 1, len(items)):
            b = items[j]
            if a.sha256 and a.sha256 == b.sha256:
                continue
            d = hamming(av, getattr(b, attr))
            if d <= threshold:
                uf.union(i, j)
                pairs.append(Pair(a.id, b.id, d))

    by_root = defaultdict(list)
    for i, f in enumerate(items):
        by_root[uf.find(i)].append(f)

    out = []
    idx = 1
    for group in by_root.values():
        if len(group) < 2:
            continue
        ids = {f.id for f in group}
        gpairs = [p for p in pairs if p.left in ids and p.right in ids]
        out.append(Group(f"{kind}-{idx}", kind, reason, sorted(group, key=lambda x: x.path), gpairs))
        idx += 1
    return out
