from __future__ import annotations

import hashlib
from pathlib import Path
from .models import FileRec
from .utils import IMAGE_EXTS, TEXT_EXTS, normalize_text, safe_name, sha256


def fingerprint_file(rec: FileRec, out_dir: Path | None, want_images: bool = True, want_docs: bool = True) -> FileRec:
    p = Path(rec.path)
    rec.sha256 = sha256(p)
    if want_images and rec.ext in IMAGE_EXTS:
        try:
            rec.image_hash = image_dhash(p)
            if out_dir:
                rec.thumb = write_thumb(p, out_dir / "thumbs", f"{rec.id}-{safe_name(p.name)}.jpg")
        except Exception as e:
            rec.error = f"image: {type(e).__name__}"
    if want_docs and (rec.ext in TEXT_EXTS or rec.ext == ".pdf"):
        try:
            text = read_text(p, rec.ext)
            text = normalize_text(text)
            if len(text) >= 120:
                rec.text_hash = simhash(text)
                rec.text_sample = text[:240]
                rec.text_features = text[:12000]
        except Exception:
            pass
    return rec


def image_dhash(path: Path) -> str:
    from PIL import Image, ImageOps
    img = Image.open(path)
    img = ImageOps.exif_transpose(img).convert("L").resize((9, 8))
    px = list(img.getdata())
    n = 0
    for y in range(8):
        for x in range(8):
            n = (n << 1) | int(px[y * 9 + x] > px[y * 9 + x + 1])
    return f"{n:016x}"


def write_thumb(path: Path, out_dir: Path, name: str) -> str | None:
    from PIL import Image, ImageOps
    out_dir.mkdir(parents=True, exist_ok=True)
    img = Image.open(path)
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((300, 210))
    out = out_dir / name
    img.save(out, "JPEG", quality=75)
    return str(Path("thumbs") / name).replace("\\", "/")


def read_text(path: Path, ext: str) -> str:
    if ext == ".pdf":
        return read_pdf(path)
    data = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", "ignore")


def read_pdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            pass
    return "\n".join(parts)


def simhash(text: str) -> str:
    words = text.split()
    v = [0] * 64
    for i in range(len(words)):
        shingle = " ".join(words[i:i + 3])
        h = hashlib.sha256(shingle.encode("utf-8")).digest()
        for b in range(64):
            bit = (h[b // 8] >> (b % 8)) & 1
            v[b] += 1 if bit else -1
    n = 0
    for x in v:
        n = (n << 1) | int(x > 0)
    return f"{n:016x}"
