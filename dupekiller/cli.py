from __future__ import annotations

import argparse
from pathlib import Path

from .quarantine import apply_moves, plan_moves
from .report import write_reports
from .scan import scan


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dupekiller")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("scan")
    s.add_argument("folder", nargs="?", default=".")
    s.add_argument("--out", default="dupekiller-report")
    s.add_argument("--cache", default=".dupekiller/cache.sqlite")
    s.add_argument("--image-threshold", type=int, default=8)
    s.add_argument("--text-threshold", type=int, default=14)
    s.add_argument("--min-size", type=int, default=1)
    s.add_argument("--workers", type=int, default=4)
    s.add_argument("--no-images", action="store_true")
    s.add_argument("--no-docs", action="store_true")
    s.add_argument("--no-ml", action="store_true")
    s.add_argument("--ml-threshold", type=float, default=0.80)

    q = sub.add_parser("quarantine")
    q.add_argument("report", nargs="?", default="dupekiller-report/report.json")
    q.add_argument("--apply", action="store_true")
    q.add_argument("--dry-run", action="store_true")
    q.add_argument("--keep", choices=["shortest", "newest", "oldest", "largest"], default="shortest")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.cmd == "scan":
        root = Path(args.folder)
        out = Path(args.out)
        cache = Path(args.cache)
        print(f"scan: {root.resolve()}")
        result = scan(
            root=root,
            out_dir=out,
            cache_path=cache,
            image_threshold=args.image_threshold,
            text_threshold=args.text_threshold,
            min_size=args.min_size,
            workers=args.workers,
            no_images=args.no_images,
            no_docs=args.no_docs,
            no_ml=args.no_ml,
            ml_threshold=args.ml_threshold,
            progress=lambda a, b: print(f"fingerprinted: {a}/{b}"),
        )
        json_path, html_path = write_reports(result, out)
        stats = {
            "files": len(result["files"]),
            "groups": len(result["groups"]),
            "exact": sum(g.kind == "exact" for g in result["groups"]),
            "image": sum(g.kind == "image" for g in result["groups"]),
            "doc": sum(g.kind == "doc" for g in result["groups"]),
            "ml_doc": sum(g.kind == "ml-doc" for g in result["groups"]),
        }
        print(f"files: {stats['files']}")
        print(f"groups: {stats['groups']} exact={stats['exact']} image={stats['image']} doc={stats['doc']} ml-doc={stats['ml_doc']}")
        print(f"json: {json_path.resolve()}")
        print(f"html: {html_path.resolve()}")
        return 0

    if args.cmd == "quarantine":
        apply = bool(args.apply and not args.dry_run)
        _, moves = plan_moves(Path(args.report), args.keep)
        n = apply_moves(moves, apply)
        print(f"{'moved' if apply else 'planned'}: {n}")
        if not apply:
            print("add --apply when the list looks right")
        return 0

    parser().print_help()
    return 0
