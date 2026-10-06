#!/usr/bin/env python3
"""Print a recursive directory tree of a Google Drive path (or any rclone remote)
with per-directory file counts and sizes.

Usage:
    ./20261001_-_drive_tree_stats.py gdrive:Projects
    ./20261001_-_drive_tree_stats.py gdrive:Projects --sort size --depth 3
    ./20261001_-_drive_tree_stats.py gdrive:Projects --csv out.csv
    rclone lsjson -R --fast-list gdrive:Projects > list.json
    ./20261001_-_drive_tree_stats.py --from-json list.json --root-name Projects

Columns:
    files  = files in the directory and all its subdirectories
    size   = total size of those files
    direct = files located directly in the directory
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import dataclass, field


@dataclass
class Node:
    name: str
    files: int = 0          # recursive
    size: int = 0           # recursive, bytes
    direct_files: int = 0
    direct_size: int = 0
    children: dict[str, "Node"] = field(default_factory=dict)

    def child(self, name: str) -> "Node":
        if name not in self.children:
            self.children[name] = Node(name)
        return self.children[name]


def human(n: int) -> str:
    size = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"


def load_entries(args: argparse.Namespace) -> list[dict]:
    if args.from_json:
        with open(args.from_json, encoding="utf-8") as fh:
            return json.load(fh)
    cmd = [
        "rclone", "lsjson", "-R", "--fast-list",
        "--no-mimetype", "--no-modtime", args.remote,
    ]
    cmd += args.rclone_arg or []
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"rclone failed ({proc.returncode}):\n{proc.stderr}")
    return json.loads(proc.stdout)


def build_tree(entries: list[dict], root_name: str) -> Node:
    root = Node(root_name)
    for e in entries:
        parts = [p for p in e["Path"].split("/") if p]
        if e.get("IsDir"):
            node = root
            for p in parts:
                node = node.child(p)
            continue
        # Google-native files (Docs, Sheets...) report Size -1: count them, size 0.
        size = max(int(e.get("Size", 0)), 0)
        node = root
        node.files += 1
        node.size += size
        for p in parts[:-1]:
            node = node.child(p)
            node.files += 1
            node.size += size
        node.direct_files += 1
        node.direct_size += size
    return root


def sorted_children(node: Node, key: str) -> list[Node]:
    kids = list(node.children.values())
    if key == "size":
        return sorted(kids, key=lambda n: (-n.size, n.name.lower()))
    if key == "count":
        return sorted(kids, key=lambda n: (-n.files, n.name.lower()))
    return sorted(kids, key=lambda n: n.name.lower())


def print_tree(root: Node, sort: str, depth: int | None) -> None:
    w = max(len(f"{root.files:,}"), 5)
    print(f"{'files':>{w}}  {'size':>10}  {'direct':>{w}}  path")

    def line(n: Node, label: str) -> None:
        print(f"{n.files:>{w},}  {human(n.size):>10}  {n.direct_files:>{w},}  {label}")

    line(root, root.name + "/")

    def walk(node: Node, prefix: str, level: int) -> None:
        if depth is not None and level > depth:
            return
        kids = sorted_children(node, sort)
        for i, k in enumerate(kids):
            last = i == len(kids) - 1
            line(k, f"{prefix}{'└── ' if last else '├── '}{k.name}/")
            walk(k, prefix + ("    " if last else "│   "), level + 1)

    walk(root, "", 1)


def write_csv(root: Node, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "depth", "files_recursive", "size_bytes_recursive",
                    "files_direct", "size_bytes_direct", "subdirs"])

        def walk(n: Node, p: str, d: int) -> None:
            w.writerow([p, d, n.files, n.size, n.direct_files, n.direct_size,
                        len(n.children)])
            for k in sorted_children(n, "name"):
                walk(k, f"{p}/{k.name}", d + 1)

        walk(root, root.name, 0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("remote", nargs="?", help="rclone path, e.g. gdrive:Projects")
    ap.add_argument("--from-json", help="read a saved 'rclone lsjson -R' output")
    ap.add_argument("--root-name", help="label for the root directory")
    ap.add_argument("--sort", choices=("name", "size", "count"), default="name")
    ap.add_argument("--depth", type=int, help="limit printed depth (totals stay recursive)")
    ap.add_argument("--csv", help="also write the full tree to this CSV file")
    ap.add_argument("--rclone-arg", action="append",
                    help="extra rclone flag, repeatable, e.g. --rclone-arg=--drive-shared-with-me")
    args = ap.parse_args()
    if not args.remote and not args.from_json:
        ap.error("give a remote path or --from-json")

    root_name = args.root_name or (args.remote or "root").rstrip("/")
    root = build_tree(load_entries(args), root_name)
    print_tree(root, args.sort, args.depth)
    if args.csv:
        write_csv(root, args.csv)
        print(f"\nCSV written to {args.csv}", file=sys.stderr)


if __name__ == "__main__":
    main()
