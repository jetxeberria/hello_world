#!/usr/bin/env python3
"""Compare a Google Drive path with a local path and synchronize them manually
through an editable plan file. Nothing is transferred or deleted unless the
plan says so and 'apply' is run with --execute.

Workflow:
    1. scan   -> lists both sides with rclone, writes plan.csv (+ plan.csv.meta.json)
    2. edit   -> change the 'action' column (spreadsheet or text editor)
    3. apply  -> re-checks every row against the current state, then runs rclone
                 (dry run by default, --execute to perform)

Examples:
    ./20261001_-_drive_sync_plan.py scan etxeberria_92:2025 ~/Pictures/2025 -o plan.csv
    ./20261001_-_drive_sync_plan.py scan etxeberria_92:2025 ~/Pictures/2025 -o plan.csv --checksum
    ./20261001_-_drive_sync_plan.py summary plan.csv
    ./20261001_-_drive_sync_plan.py apply plan.csv              # dry run
    ./20261001_-_drive_sync_plan.py apply plan.csv --execute

Statuses (scan) and default actions:
    drive_only      file only on Drive                    -> download
    local_only      file only on local                    -> upload
    size_differs    same path, different size             -> review
    md5_differs     same path and size, different MD5     -> review   (--checksum)
    gdoc            Google-native Doc/Sheet/Slide (no file content to compare) -> skip
    drive_duplicate same path appears more than once on Drive -> skip (see 'rclone dedupe')
    equal           identical (only listed with --include-equal) -> skip

Valid actions in the plan:
    skip | review | download | upload | delete-drive
    'review' is never executed; change it to download, upload or skip.
    'delete-drive' moves the Drive file to the Drive trash (rclone default for Drive).
    Local files are never deleted by this tool.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PLAN_FIELDS = ["action", "status", "path", "drive_size", "local_size",
               "drive_mtime", "local_mtime", "drive_md5", "local_md5", "note"]
ACTIONS = {"skip", "review", "download", "upload", "delete-drive"}
DEFAULT_ACTION = {"drive_only": "download", "local_only": "upload",
                  "size_differs": "review", "md5_differs": "review",
                  "gdoc": "skip", "drive_duplicate": "skip", "equal": "skip"}
CACHE_FILE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) \
    / "drive_sync_plan" / "md5_cache.json"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def human(n: int | str | None) -> str:
    if n in (None, ""):
        return "-"
    size = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(size) < 1024 or unit == "TiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return str(n)


# --------------------------------------------------------------------------- rclone
def rclone(args: list[str], extra: list[str] | None = None, capture: bool = True) -> str:
    cmd = ["rclone", *args, *(extra or [])]
    proc = subprocess.run(cmd, capture_output=capture, text=True)
    if proc.returncode != 0:
        err = proc.stderr if capture else ""
        sys.exit(f"rclone failed ({proc.returncode}): {' '.join(cmd)}\n{err}")
    return proc.stdout if capture else ""


def list_side(root: str, is_drive: bool, extra: list[str],
              files_from: str | None = None) -> list[dict]:
    args = ["lsjson", "-R", "--files-only", root]
    if is_drive:
        args += ["--fast-list", "--hash", "--hash-type", "md5"]
    else:
        args += ["--no-mimetype"]
    if files_from:
        args += ["--files-from-raw", files_from]
    return json.loads(rclone(args, extra) or "[]")


# --------------------------------------------------------------------------- MD5 cache
class Md5Cache:
    def __init__(self, path: Path = CACHE_FILE):
        self.path = path
        try:
            self.data = json.loads(path.read_text())
        except (OSError, ValueError):
            self.data = {}

    def get(self, file: Path) -> str:
        st = file.stat()
        key = str(file.resolve())
        hit = self.data.get(key)
        if hit and hit[0] == st.st_size and hit[1] == st.st_mtime_ns:
            return hit[2]
        h = hashlib.md5()
        with open(file, "rb") as fh:
            for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
                h.update(chunk)
        self.data[key] = [st.st_size, st.st_mtime_ns, h.hexdigest()]
        return h.hexdigest()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data))
        tmp.replace(self.path)


# --------------------------------------------------------------------------- scan
def cmd_scan(a: argparse.Namespace) -> None:
    local_root = Path(a.local).expanduser().resolve()
    if not local_root.is_dir():
        sys.exit(f"Local path is not a directory: {local_root}")
    extra = a.rclone_arg or []

    log(f"Listing Drive: {a.remote}")
    drive_entries = list_side(a.remote, True, extra)
    log(f"  {len(drive_entries)} files")
    log(f"Listing local: {local_root}")
    local_entries = list_side(str(local_root), False, extra)
    log(f"  {len(local_entries)} files")

    drive_count = Counter(e["Path"] for e in drive_entries)
    drive = {e["Path"]: e for e in drive_entries}
    local = {e["Path"]: e for e in local_entries}

    rows: list[dict] = []
    to_hash: list[str] = []
    for path in sorted(set(drive) | set(local)):
        d, l = drive.get(path), local.get(path)
        row = {"path": path, "note": "",
               "drive_size": d["Size"] if d else "", "local_size": l["Size"] if l else "",
               "drive_mtime": d["ModTime"][:19] if d else "",
               "local_mtime": l["ModTime"][:19] if l else "",
               "drive_md5": (d.get("Hashes") or {}).get("md5", "") if d else "",
               "local_md5": ""}
        if d and drive_count[path] > 1:
            row["status"] = "drive_duplicate"
            row["note"] = f"{drive_count[path]} Drive files with this path"
        elif d and d["Size"] < 0:
            row["status"] = "gdoc"
            row["note"] = d.get("MimeType", "Google-native file")
        elif d and not l:
            row["status"] = "drive_only"
        elif l and not d:
            row["status"] = "local_only"
        elif d["Size"] != l["Size"]:
            row["status"] = "size_differs"
        else:
            row["status"] = "equal"
            if a.checksum:
                to_hash.append(path)
        rows.append(row)

    if to_hash:
        by_path = {r["path"]: r for r in rows}
        total = sum(local[p]["Size"] for p in to_hash)
        log(f"Hashing {len(to_hash)} local files ({human(total)}), cached in {CACHE_FILE}")
        cache = Md5Cache()
        done = 0

        def work(p: str) -> tuple[str, str]:
            return p, cache.get(local_root / p)

        try:
            with ThreadPoolExecutor(max_workers=a.hash_workers) as pool:
                for p, md5 in pool.map(work, to_hash):
                    r = by_path[p]
                    r["local_md5"] = md5
                    if not r["drive_md5"]:
                        r["note"] = "no MD5 on Drive; compared by size only"
                    elif r["drive_md5"] != md5:
                        r["status"] = "md5_differs"
                    done += 1
                    if done % 50 == 0:
                        log(f"  {done}/{len(to_hash)}")
                        cache.save()
        finally:
            cache.save()

    for r in rows:
        r["action"] = DEFAULT_ACTION[r["status"]]
    if not a.include_equal:
        rows = [r for r in rows if r["status"] != "equal"]

    with open(a.output, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=PLAN_FIELDS)
        w.writeheader()
        w.writerows(rows)
    meta = {"remote": a.remote, "local": str(local_root), "rclone_args": extra,
            "checksum": a.checksum,
            "drive_files": len(drive_entries), "local_files": len(local_entries)}
    Path(a.output + ".meta.json").write_text(json.dumps(meta, indent=2))
    log(f"Plan written: {a.output} ({len(rows)} rows)")
    print_summary(rows, a.depth)


# --------------------------------------------------------------------------- summary
def read_plan(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def print_summary(rows: list[dict], depth: int) -> None:
    status_order = ["drive_only", "local_only", "size_differs", "md5_differs",
                    "gdoc", "drive_duplicate"]
    if not rows:
        print("\nNo differences.")
        return
    tot = Counter(r["status"] for r in rows)
    print("\nTotals by status")
    for s in status_order + ["equal"]:
        if tot[s]:
            sz = sum(int(r["drive_size"] or r["local_size"] or 0) for r in rows
                     if r["status"] == s)
            print(f"  {s:<16}{tot[s]:>7}  {human(max(sz, 0)):>10}")
    print("\nTotals by action")
    for act, n in sorted(Counter(r["action"] for r in rows).items()):
        print(f"  {act:<16}{n:>7}")

    per_dir: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        parts = r["path"].split("/")[:-1]
        for i in range(0, min(len(parts), depth) + 1):
            per_dir["/".join(parts[:i])][r["status"]] += 1
    cols = ["drive_only", "local_only", "size_differs", "md5_differs"]
    short = {"drive_only": "drive", "local_only": "local",
             "size_differs": "sizeΔ", "md5_differs": "md5Δ"}
    print(f"\nDifferences per directory (depth <= {depth})")
    print("  " + "".join(f"{short[c]:>7}" for c in cols) + "  path")
    for d in sorted(per_dir):
        c = per_dir[d]
        if not any(c[x] for x in cols):
            continue
        indent = "    " * (d.count("/") + 1 if d else 0)
        print("  " + "".join(f"{(c[x] or ''):>7}" for x in cols)
              + f"  {indent}{(d.split('/')[-1] if d else '.')}/")


def cmd_summary(a: argparse.Namespace) -> None:
    print_summary(read_plan(a.plan), a.depth)


# --------------------------------------------------------------------------- apply
def cmd_apply(a: argparse.Namespace) -> None:
    meta_path = Path(a.plan + ".meta.json")
    if not meta_path.exists():
        sys.exit(f"Missing {meta_path}; it is written by 'scan' next to the plan.")
    meta = json.loads(meta_path.read_text())
    remote, local_root = meta["remote"], Path(meta["local"])
    extra = meta.get("rclone_args", []) + (a.rclone_arg or [])

    rows = read_plan(a.plan)
    bad = [r for r in rows if r["action"] not in ACTIONS]
    if bad:
        sys.exit("Invalid action(s): " + ", ".join(
            f"{r['path']!r}={r['action']!r}" for r in bad[:10]))
    errors = []
    for r in rows:
        act, on_d, on_l = r["action"], r["drive_size"] != "", r["local_size"] != ""
        if act in ("download", "delete-drive") and not on_d:
            errors.append(f"{act} but not on Drive: {r['path']}")
        if act == "upload" and not on_l:
            errors.append(f"upload but not on local: {r['path']}")
        if act in ("download", "upload") and r["status"] in ("gdoc", "drive_duplicate"):
            errors.append(f"{act} not supported for status {r['status']}: {r['path']}")
    if errors:
        sys.exit("Plan errors:\n  " + "\n  ".join(errors[:20]))

    todo = [r for r in rows if r["action"] in ("download", "upload", "delete-drive")]
    pending = sum(r["action"] == "review" for r in rows)
    if pending:
        log(f"Note: {pending} row(s) still marked 'review' are not executed.")
    if not todo:
        log("Nothing to do.")
        return

    # Re-check current state of every affected file against the plan.
    with tempfile.TemporaryDirectory() as tmp:
        lst = Path(tmp, "check.txt")
        lst.write_text("".join(r["path"] + "\n" for r in todo), encoding="utf-8")
        current = {e["Path"]: e["Size"] for e in
                   list_side(remote, True, extra, files_from=str(lst))}
    stale = []
    for r in todo:
        exp_d = int(r["drive_size"]) if r["drive_size"] else None
        exp_l = int(r["local_size"]) if r["local_size"] else None
        lp = local_root / r["path"]
        now_l = lp.stat().st_size if lp.is_file() else None
        now_d = current.get(r["path"])
        if now_d != exp_d or now_l != exp_l:
            stale.append(f"{r['path']}: drive {exp_d}->{now_d}, local {exp_l}->{now_l}")
    if stale:
        sys.exit("State changed since scan; re-run 'scan'. Stale rows:\n  "
                 + "\n  ".join(stale[:20]))

    groups = defaultdict(list)
    for r in todo:
        groups[r["action"]].append(r)
    print("Planned operations")
    for act in ("download", "upload", "delete-drive"):
        g = groups.get(act, [])
        if g:
            size = sum(int(r["drive_size"] if act != "upload" else r["local_size"])
                       for r in g)
            print(f"  {act:<13}{len(g):>6} files  {human(size):>10}")

    if a.execute and not a.yes:
        if input("Type 'yes' to execute: ").strip() != "yes":
            sys.exit("Aborted.")

    mode = ["-P"] if a.execute else ["--dry-run", "-v"]
    with tempfile.TemporaryDirectory() as tmp:
        for act, g in groups.items():
            lst = Path(tmp, f"{act}.txt")
            lst.write_text("".join(r["path"] + "\n" for r in g), encoding="utf-8")
            ff = ["--files-from-raw", str(lst)]
            if act == "download":
                args = ["copy", remote, str(local_root), "--ignore-times", *ff]
            elif act == "upload":
                args = ["copy", str(local_root), remote, "--ignore-times", *ff]
            else:
                args = ["delete", remote, *ff]
            log(f"\n== {act}: rclone {' '.join(args + mode)}")
            rclone(args + mode, extra, capture=False)
    log("\nDone." if a.execute else "\nDry run only. Add --execute to perform.")


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="compare both sides and write a plan")
    s.add_argument("remote", help="rclone Drive path, e.g. etxeberria_92:2025")
    s.add_argument("local", help="local directory")
    s.add_argument("-o", "--output", default="plan.csv")
    s.add_argument("--checksum", action="store_true",
                   help="MD5-verify files whose sizes match (local MD5 is cached)")
    s.add_argument("--hash-workers", type=int, default=2)
    s.add_argument("--include-equal", action="store_true")
    s.add_argument("--depth", type=int, default=2, help="summary tree depth")
    s.add_argument("--rclone-arg", action="append",
                   help="extra rclone flag, repeatable, e.g. --rclone-arg=--exclude=.thumbnails/**")
    s.set_defaults(func=cmd_scan)

    m = sub.add_parser("summary", help="print totals and per-directory differences")
    m.add_argument("plan")
    m.add_argument("--depth", type=int, default=2)
    m.set_defaults(func=cmd_summary)

    p = sub.add_parser("apply", help="execute the approved actions of a plan")
    p.add_argument("plan")
    p.add_argument("--execute", action="store_true", help="perform; default is dry run")
    p.add_argument("-y", "--yes", action="store_true", help="skip the confirmation prompt")
    p.add_argument("--rclone-arg", action="append")
    p.set_defaults(func=cmd_apply)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
