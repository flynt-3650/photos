from pathlib import Path
import shutil
import subprocess
import sys


root = Path(__file__).resolve().parent.parent / "tmp-py-smoke"
shutil.rmtree(root, ignore_errors=True)
(root / "a").mkdir(parents=True)
(root / "b").mkdir(parents=True)

(root / "a" / "same.txt").write_text("one two three\n", "utf-8")
(root / "b" / "same-copy.txt").write_text("one two three\n", "utf-8")

doc = ("this is a private note about invoices screenshots cleanup and duplicate detection " * 8).strip()
(root / "a" / "note.md").write_text(doc, "utf-8")
(root / "b" / "note-copy.md").write_text(doc.replace("private", "personal"), "utf-8")

try:
    from PIL import Image
    Image.new("RGB", (80, 60), "#ff0000").save(root / "a" / "red.png")
    Image.new("RGB", (80, 60), "#ee0000").save(root / "b" / "red-ish.png")
except Exception:
    pass

cmd = [sys.executable, "-m", "dupekiller", "scan", str(root), "--out", str(root / "report"), "--cache", str(root / "report" / "cache.sqlite")]
subprocess.check_call(cmd, cwd=Path(__file__).resolve().parent.parent)

import json
report = json.loads((root / "report" / "report.json").read_text("utf-8"))
kinds = {g["kind"] for g in report["groups"]}
assert "exact" in kinds
assert "doc" in kinds
assert "ml-doc" in kinds
print("smoke ok", kinds)
