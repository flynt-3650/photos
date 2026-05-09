from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from . import __version__
from .models import FileRec, Group
from .utils import file_url, fmt_size


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    data = report_json(result)
    json_path = out_dir / "report.json"
    html_path = out_dir / "index.html"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
    html_path.write_text(report_html(data), "utf-8")
    return json_path, html_path


def report_json(result: dict[str, Any]) -> dict[str, Any]:
    files: list[FileRec] = result["files"]
    groups: list[Group] = sorted(result["groups"], key=lambda g: g.wasted_bytes, reverse=True)
    return {
        "app": "dupekiller",
        "version": __version__,
        "root": result["root"],
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "options": result["options"],
        "stats": {
            "files": len(files),
            "bytes": sum(f.size for f in files),
            "groups": len(groups),
            "exactGroups": sum(g.kind == "exact" for g in groups),
            "imageGroups": sum(g.kind == "image" for g in groups),
            "docGroups": sum(g.kind == "doc" for g in groups),
            "mlDocGroups": sum(g.kind == "ml-doc" for g in groups),
            "wastedBytes": sum(g.wasted_bytes for g in groups),
        },
        "files": [f.json() for f in files],
        "groups": [g.json() for g in groups],
    }


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def report_html(data: dict[str, Any]) -> str:
    groups = data["groups"]
    stats = data["stats"]
    cards = "\n".join(group_card(g) for g in groups) or "<p class='empty'>Nothing suspicious found.</p>"
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>dupekiller</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f3ef;color:#181818;font:14px/1.45 system-ui,Segoe UI,Arial,sans-serif}}
header{{position:sticky;top:0;z-index:5;background:#181818;color:white;padding:18px 24px;border-bottom:3px solid #d6ff5f}}
h1{{font-size:21px;margin:0 0 4px}}header p{{margin:0;color:#bbb;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
main{{max-width:1220px;margin:0 auto;padding:22px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:16px}}
.stat{{background:white;border:1px solid #ddd;border-radius:6px;padding:13px}}.stat b{{font-size:20px;display:block}}
.cmd{{background:#222;color:#eee;border-radius:6px;padding:12px;overflow:auto;margin:0 0 18px}}
.group{{background:white;border:1px solid #ddd;border-radius:6px;margin:14px 0;padding:15px}}
.top{{display:flex;justify-content:space-between;gap:12px;align-items:start}}h2{{font-size:16px;margin:0}}.muted{{color:#666;margin:3px 0 0}}
.files{{display:grid;grid-template-columns:repeat(auto-fill,minmax(285px,1fr));gap:12px;margin-top:12px}}
article{{border:1px solid #e2e2e2;border-radius:6px;background:#fbfbfb;overflow:hidden;min-width:0}}
img,.blank{{height:155px;width:100%;background:#242424;color:#aaa;display:flex;align-items:center;justify-content:center;object-fit:contain}}
.meta{{padding:10px;display:grid;gap:4px;min-width:0}}.path{{font-weight:650;color:#075fa8;text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
small,.sub{{color:#666}}small{{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.pill{{font-size:12px;border:1px solid #ddd;border-radius:999px;padding:3px 8px;background:#fafafa;color:#555}}
</style>
</head>
<body>
<header><h1>dupekiller</h1><p>{esc(data["root"])} · {esc(data["createdAt"])}</p></header>
<main>
<div class="stats">
  <div class="stat"><b>{stats["files"]}</b>files</div>
  <div class="stat"><b>{fmt_size(stats["bytes"])}</b>scanned</div>
  <div class="stat"><b>{stats["groups"]}</b>groups</div>
  <div class="stat"><b>{fmt_size(stats["wastedBytes"])}</b>possible waste</div>
</div>
<pre class="cmd">python -m dupekiller quarantine dupekiller-report/report.json --dry-run
python -m dupekiller quarantine dupekiller-report/report.json --apply --keep shortest</pre>
{cards}
</main>
</body>
</html>"""


def group_card(g: dict[str, Any]) -> str:
    files = "\n".join(file_card(f) for f in g["files"])
    return f"""<section class="group {esc(g["kind"])}">
<div class="top">
  <div><h2>{esc(g["kind"])} / {esc(g["id"])}</h2><p class="muted">{g["count"]} files · maybe wasted {fmt_size(g["wastedBytes"])} · {esc(g["reason"])}</p></div>
  <span class="pill">{esc(g["kind"])}</span>
</div>
<div class="files">{files}</div>
</section>"""


def file_card(f: dict[str, Any]) -> str:
    path = f["path"]
    preview = f'<a href="{file_url(path)}"><img src="{esc(f["thumb"])}"></a>' if f.get("thumb") else f'<div class="blank">{esc(f.get("ext") or "file")}</div>'
    sample = f"<small>{esc(f.get('textSample'))}</small>" if f.get("textSample") else ""
    return f"""<article>
{preview}
<div class="meta">
  <a class="path" href="{file_url(path)}">{esc(f.get("rel") or path)}</a>
  <span class="sub">{fmt_size(f.get("size", 0))}</span>
  {sample}
</div>
</article>"""
