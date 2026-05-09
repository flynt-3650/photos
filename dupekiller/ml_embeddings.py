from __future__ import annotations

from .models import FileRec, Group, Pair


def ml_doc_groups(files: list[FileRec], threshold: float = 0.80, dims: int = 64) -> list[Group]:
    docs = [f for f in files if f.text_features and len(f.text_features) >= 80]
    if len(docs) < 2:
        return []

    try:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        from sklearn.preprocessing import normalize
    except Exception:
        return []

    texts = [f.text_features for f in docs]
    vec = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        lowercase=True,
        sublinear_tf=True,
    )
    x = vec.fit_transform(texts)
    if x.shape[1] >= 3 and x.shape[0] >= 3:
        k = max(2, min(dims, x.shape[0] - 1, x.shape[1] - 1))
        x = TruncatedSVD(n_components=k, random_state=42).fit_transform(x)
        x = normalize(x)

    sim = cosine_similarity(x)
    uf = UF(len(docs))
    pairs: list[Pair] = []
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            score = float(sim[i, j])
            if score >= threshold:
                uf.union(i, j)
                pairs.append(Pair(docs[i].id, docs[j].id, int(round(score * 1000))))

    parts: dict[int, list[FileRec]] = {}
    for i, f in enumerate(docs):
        parts.setdefault(uf.find(i), []).append(f)

    out: list[Group] = []
    idx = 1
    for group in parts.values():
        if len(group) < 2:
            continue
        ids = {f.id for f in group}
        gpairs = [p for p in pairs if p.left in ids and p.right in ids]
        out.append(Group(
            id=f"ml-doc-{idx}",
            kind="ml-doc",
            reason=f"local TF-IDF/SVD embedding cosine >= {threshold}",
            files=sorted(group, key=lambda x: x.path),
            pairs=gpairs,
        ))
        idx += 1
    return out


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
