from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .cache import Cache
from .fingerprint import fingerprint_file
from .grouping import exact_groups, near_hash_groups
from .ml_embeddings import ml_doc_groups
from .models import FileRec
from .utils import TEXT_EXTS, safe_name
from .walk import iter_files


def scan(
    root: Path,
    out_dir: Path,
    cache_path: Path,
    image_threshold: int = 8,
    text_threshold: int = 14,
    min_size: int = 1,
    workers: int = 4,
    no_images: bool = False,
    no_docs: bool = False,
    no_ml: bool = False,
    ml_threshold: float = 0.80,
    progress=None,
) -> dict[str, Any]:
    root = root.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = Cache(cache_path)
    paths = list(iter_files(root, out_dir))
    recs: list[FileRec] = []

    for p in paths:
        try:
            st = p.stat()
        except OSError:
            continue
        if st.st_size < min_size:
            continue
        resolved = p.resolve()
        try:
            rel = str(resolved.relative_to(root))
        except ValueError:
            rel = str(p)
        recs.append(FileRec(
            id=len(recs),
            path=str(resolved),
            rel=rel,
            ext=p.suffix.lower(),
            size=st.st_size,
            mtime_ns=st.st_mtime_ns,
        ))

    def work(rec: FileRec) -> FileRec:
        p = Path(rec.path)
        cached = cache.get(p, rec.size, rec.mtime_ns)
        needs_text_features = (not no_docs and (rec.ext in TEXT_EXTS or rec.ext == ".pdf") and cached and cached.get("text_hash") and not cached.get("text_features"))
        if cached and not needs_text_features:
            rec.sha256 = cached.get("sha256", "")
            rec.image_hash = cached.get("image_hash")
            rec.text_hash = cached.get("text_hash")
            rec.text_sample = cached.get("text_sample")
            rec.text_features = cached.get("text_features")
            rec.thumb = cached.get("thumb")
            rec.error = cached.get("error")
            if rec.image_hash and out_dir and rec.thumb and not (out_dir / rec.thumb).exists():
                try:
                    from .fingerprint import write_thumb
                    rec.thumb = write_thumb(p, out_dir / "thumbs", f"{rec.id}-{safe_name(p.name)}.jpg")
                except Exception:
                    rec.thumb = None
            return rec
        rec = fingerprint_file(rec, out_dir, not no_images, not no_docs)
        cache.put(p, rec.size, rec.mtime_ns, {
            "sha256": rec.sha256,
            "image_hash": rec.image_hash,
            "text_hash": rec.text_hash,
            "text_sample": rec.text_sample,
            "text_features": rec.text_features,
            "thumb": rec.thumb,
            "error": rec.error,
        })
        return rec

    done: list[FileRec] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [pool.submit(work, r) for r in recs]
        for i, fut in enumerate(as_completed(futures), 1):
            done.append(fut.result())
            if progress and (i == len(futures) or i % 250 == 0):
                progress(i, len(futures))

    cache.close()
    done.sort(key=lambda x: x.id)

    groups = []
    groups.extend(exact_groups(done))
    if not no_images:
        groups.extend(near_hash_groups(done, "image_hash", image_threshold, "image", f"dhash distance <= {image_threshold}"))
    if not no_docs:
        groups.extend(near_hash_groups(done, "text_hash", text_threshold, "doc", f"simhash distance <= {text_threshold}"))
    if not no_docs and not no_ml:
        groups.extend(ml_doc_groups(done, threshold=ml_threshold))

    return {
        "root": str(root),
        "out_dir": str(out_dir),
        "files": done,
        "groups": groups,
        "options": {
            "imageThreshold": image_threshold,
            "textThreshold": text_threshold,
            "minSize": min_size,
            "workers": workers,
            "mlThreshold": ml_threshold,
            "mlDocs": not no_ml,
        },
    }
