import asyncio
import hashlib
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil
from pydantic_ai import RunContext
from ..core.deps import ToolDeps
from terminus.core.session import session

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sync helpers — all run inside asyncio.to_thread() to keep event loop free
# ---------------------------------------------------------------------------

def _calculate_md5(path: Path) -> str:
    hasher = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


def _sync_analyze_downloads() -> Dict:
    """Analyze Downloads folder and return structured plan. No side effects."""
    downloads_dir = Path.home() / "Downloads"
    if not downloads_dir.exists():
        return {"error": "Downloads folder not found."}

    categories = {
        "Documents": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".csv", ".pptx", ".ppt"],
        "Installers": [".exe", ".msi", ".dmg", ".pkg"],
        "Archives":   [".zip", ".tar", ".gz", ".rar", ".7z"],
        "Media":      [".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mp3", ".wav", ".mov"],
    }
    ext_to_cat = {ext: cat for cat, exts in categories.items() for ext in exts}

    files = [f for f in downloads_dir.iterdir() if f.is_file() and not f.name.startswith(".")]

    to_delete: List[Path] = []
    to_move: Dict[str, List[Path]] = {}
    delete_reasons: Dict[str, str] = {}

    # Detect duplicate downloads (name ends with " (1).ext" pattern)
    hashes: Dict[str, Path] = {}
    originals = [f for f in files if not ("(" in f.name and ")" in f.name)]
    for f in originals:
        h = _calculate_md5(f)
        if h:
            hashes[h] = f

    for f in files:
        if "(" in f.stem and ")" in f.stem:
            h = _calculate_md5(f)
            if h and h in hashes:
                to_delete.append(f)
                delete_reasons[f.name] = "duplicate"

    # Process remaining files
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    remaining = [f for f in files if f not in to_delete]

    for f in remaining:
        ext = f.suffix.lower()
        cat = ext_to_cat.get(ext)
        if cat == "Installers":
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < thirty_days_ago:
                    to_delete.append(f)
                    delete_reasons[f.name] = f"old installer ({mtime.strftime('%Y-%m-%d')})"
                    continue
            except Exception:
                pass
        if cat:
            to_move.setdefault(cat, []).append(f)

    return {
        "downloads_dir": downloads_dir,
        "to_delete": to_delete,
        "delete_reasons": delete_reasons,
        "to_move": to_move,
        "total_files": len(files),
    }


def _sync_execute_clean(plan: Dict) -> str:
    """Execute the clean plan returned by _sync_analyze_downloads."""
    downloads_dir: Path = plan["downloads_dir"]
    to_delete: List[Path] = plan["to_delete"]
    to_move: Dict[str, List[Path]] = plan["to_move"]

    deleted = moved = 0
    errors: List[str] = []

    for f in to_delete:
        try:
            f.unlink()
            deleted += 1
        except Exception as e:
            errors.append(f"Delete {f.name}: {e}")

    for cat, file_list in to_move.items():
        dest_dir = downloads_dir / cat
        dest_dir.mkdir(exist_ok=True)
        for f in file_list:
            try:
                target = dest_dir / f.name
                if target.exists():
                    base, suffix, n = target.stem, target.suffix, 1
                    while (dest_dir / f"{base}_{n}{suffix}").exists():
                        n += 1
                    target = dest_dir / f"{base}_{n}{suffix}"
                shutil.move(str(f), str(target))
                moved += 1
            except Exception as e:
                errors.append(f"Move {f.name}: {e}")

    lines = [
        f"Done!  Deleted {deleted}  |  Organized {moved} files",
    ]
    if errors:
        lines.append(f"\n{len(errors)} error(s):")
        lines.extend(f"  {e}" for e in errors[:5])
    return "\n".join(lines)


def _format_plan_summary(plan: Dict) -> str:
    """Build a clean human-readable summary of what will happen."""
    if "error" in plan:
        return plan["error"]

    to_delete: List[Path] = plan["to_delete"]
    to_move: Dict[str, List[Path]] = plan["to_move"]
    total: int = plan["total_files"]
    delete_reasons: Dict[str, str] = plan["delete_reasons"]

    dup_count = sum(1 for r in delete_reasons.values() if r == "duplicate")
    old_count  = len(to_delete) - dup_count

    lines = [f"Downloads  ({total} files scanned)\n"]

    if to_delete:
        lines.append(f"  DELETE   {len(to_delete):>4} files")
        if dup_count:
            lines.append(f"             {dup_count} duplicates")
        if old_count:
            lines.append(f"             {old_count} old installers (>30 days)")

    for cat, flist in sorted(to_move.items(), key=lambda x: -len(x[1])):
        lines.append(f"  MOVE  →  {len(flist):>4} files  →  {cat}/")

    if not to_delete and not to_move:
        lines.append("  Already clean — nothing to do.")

    return "\n".join(lines)


def _sync_archive_inactive_projects(path: str, age_days: int, dry_run: bool) -> str:
    base_path = session.resolve_path(path)
    if not base_path.exists() or not base_path.is_dir():
        return f"Directory not found: {path}"

    subfolders = [
        d for d in base_path.iterdir()
        if d.is_dir() and d.name not in ("Archives",) and not d.name.startswith(".")
    ]

    now = datetime.now()
    threshold = now - timedelta(days=age_days)
    to_archive: List[Tuple[Path, datetime]] = []

    for d in subfolders:
        newest = 0.0
        try:
            for item in d.rglob("*"):
                if item.is_file():
                    newest = max(newest, item.stat().st_mtime)
        except Exception:
            continue
        if newest == 0.0:
            newest = d.stat().st_mtime
        last_mod = datetime.fromtimestamp(newest)
        if last_mod < threshold:
            to_archive.append((d, last_mod))

    if not to_archive:
        return f"No projects inactive for {age_days} days in {path}."

    if dry_run:
        lines = [f"Inactive projects in {path}  ({len(to_archive)} found)\n"]
        for d, t in to_archive:
            lines.append(f"  ARCHIVE  {d.name}  (last active {t.strftime('%Y-%m-%d')})")
        lines.append("\nRun with dry_run=False to compress and remove.")
        return "\n".join(lines)

    archives_dir = base_path / "Archives"
    archives_dir.mkdir(exist_ok=True)
    archived = 0
    errors: List[str] = []
    for folder, _ in to_archive:
        try:
            shutil.make_archive(str(archives_dir / folder.name), "zip", str(folder))
            shutil.rmtree(str(folder))
            archived += 1
        except Exception as e:
            errors.append(f"{folder.name}: {e}")

    lines = [f"Archived {archived} inactive projects  →  {archives_dir}"]
    if errors:
        lines.extend(f"  Error: {e}" for e in errors)
    return "\n".join(lines)


def _sync_remove_duplicate_screenshots(path: str, dry_run: bool) -> str:
    target_path = session.resolve_path(path)
    if not target_path.exists():
        return f"Directory not found: {path}"

    files: List[Path] = []
    for pat in ["screenshot*", "Screenshot*", "screen shot*", "screen_shot*"]:
        files.extend(target_path.glob(pat))
    files = list({f for f in files if f.is_file()})

    if not files:
        return f"No screenshots found in {path}."

    size_map: Dict[int, List[Path]] = {}
    for f in files:
        size_map.setdefault(f.stat().st_size, []).append(f)

    to_delete: List[Tuple[Path, Path]] = []  # (remove, keep)
    for _, flist in size_map.items():
        if len(flist) < 2:
            continue
        hashes: Dict[str, Path] = {}
        for f in flist:
            h = _calculate_md5(f)
            if not h:
                continue
            if h in hashes:
                keep = hashes[h] if len(hashes[h].name) <= len(f.name) else f
                remove = f if keep is hashes[h] else hashes[h]
                hashes[h] = keep
                to_delete.append((remove, keep))
            else:
                hashes[h] = f

    if not to_delete:
        return "No duplicate screenshots found."

    if dry_run:
        lines = [f"Duplicate screenshots  ({len(to_delete)} pairs)\n"]
        for rm, kp in to_delete[:20]:
            lines.append(f"  DELETE  {rm.name}  (keep {kp.name})")
        if len(to_delete) > 20:
            lines.append(f"  … and {len(to_delete)-20} more")
        lines.append("\nRun with dry_run=False to delete duplicates.")
        return "\n".join(lines)

    deleted = 0
    errors: List[str] = []
    for rm, _ in to_delete:
        try:
            rm.unlink()
            deleted += 1
        except Exception as e:
            errors.append(f"{rm.name}: {e}")

    lines = [f"Removed {deleted} duplicate screenshots."]
    if errors:
        lines.extend(f"  Error: {e}" for e in errors)
    return "\n".join(lines)


def _sync_list_processes(name_filter: Optional[str]) -> str:
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
        try:
            pname = p.info["name"] or ""
            if name_filter and name_filter.lower() not in pname.lower():
                continue
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not procs:
        return f"No processes matching '{name_filter}'." if name_filter else "No processes found."

    procs.sort(key=lambda x: x["memory_percent"] or 0, reverse=True)
    header = f"{'PID':<8}  {'Name':<28}  {'Mem':>6}  {'CPU':>6}"
    sep    = "-" * len(header)
    rows   = [header, sep]
    for p in procs[:25]:
        mem = f"{p['memory_percent']:.1f}%" if p["memory_percent"] is not None else "  N/A"
        cpu = f"{p['cpu_percent']:.1f}%" if p["cpu_percent"] is not None else "  N/A"
        rows.append(f"{p['pid']:<8}  {(p['name'] or '')[:28]:<28}  {mem:>6}  {cpu:>6}")

    label = f"filter={name_filter}" if name_filter else "top 25 by memory"
    return f"Processes ({label})\n\n" + "\n".join(rows)


def _sync_kill_processes(pid: Optional[int], name_filter: Optional[str], dry_run: bool) -> str:
    targets: List[Tuple[int, str]] = []
    if pid:
        try:
            targets.append((pid, psutil.Process(pid).name()))
        except Exception as e:
            return f"PID {pid} not found: {e}"
    elif name_filter:
        for p in psutil.process_iter(["pid", "name"]):
            try:
                pname = p.info["name"] or ""
                if name_filter.lower() in pname.lower():
                    targets.append((p.info["pid"], pname))
            except Exception:
                continue

    if not targets:
        return f"No processes matching PID={pid} / name='{name_filter}'."

    if dry_run:
        lines = [f"Would terminate {len(targets)} process(es):"]
        lines.extend(f"  PID {tp}  {tn}" for tp, tn in targets)
        lines.append("\nRun with dry_run=False to terminate.")
        return "\n".join(lines)

    killed: List[str] = []
    errors: List[str] = []
    for tp, tn in targets:
        try:
            psutil.Process(tp).terminate()
            killed.append(f"PID {tp} ({tn})")
        except Exception as e:
            errors.append(f"PID {tp} ({tn}): {e}")

    lines = []
    if killed:
        lines.append("Terminated:\n" + "\n".join(f"  {k}" for k in killed))
    if errors:
        lines.append("Errors:\n" + "\n".join(f"  {e}" for e in errors))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public async tool functions
# ---------------------------------------------------------------------------

async def clean_downloads(ctx: RunContext[ToolDeps], dry_run: bool = True) -> str:
    """Clean the Downloads folder — analyze, confirm, then organize.

    Args:
        ctx: Run context.
        dry_run: If True, show plan and ask for confirmation. If False, execute directly.
    """
    log.debug(f"clean_downloads called, dry_run={dry_run}")

    # Always analyze first (in thread — never blocks event loop)
    plan = await asyncio.to_thread(_sync_analyze_downloads)

    if "error" in plan:
        return plan["error"]

    summary = _format_plan_summary(plan)

    if not plan["to_delete"] and not plan["to_move"]:
        return summary

    if dry_run:
        # Show plan, then ask confirmation if callback available
        if ctx.deps and ctx.deps.confirm_action:
            answer = await ctx.deps.confirm_action(
                "Organize Downloads?",
                summary,
                "Files will be moved into sub-folders. Old installers & duplicates will be deleted.",
            )
            if answer:  # bool True = confirmed
                result = await asyncio.to_thread(_sync_execute_clean, plan)
                return result
            else:
                return f"{summary}\n\nCancelled — no changes made."
        # No confirm callback (e.g. non-TUI mode) — just return the plan
        return f"{summary}\n\nRun with dry_run=False to execute."

    # dry_run=False — execute immediately
    return await asyncio.to_thread(_sync_execute_clean, plan)


async def archive_inactive_projects(
    ctx: RunContext[ToolDeps],
    path: str = ".",
    age_days: int = 180,
    dry_run: bool = True,
) -> str:
    """Archive projects inactive for N days."""
    log.debug(f"archive_inactive_projects, path={path}, age={age_days}, dry_run={dry_run}")
    return await asyncio.to_thread(_sync_archive_inactive_projects, path, age_days, dry_run)


async def remove_duplicate_screenshots(
    ctx: RunContext[ToolDeps], path: str = ".", dry_run: bool = True
) -> str:
    """Find and delete identical duplicate screenshots."""
    log.debug(f"remove_duplicate_screenshots, path={path}, dry_run={dry_run}")
    return await asyncio.to_thread(_sync_remove_duplicate_screenshots, path, dry_run)


async def manage_processes(
    ctx: RunContext[ToolDeps],
    action: str = "list",
    name_filter: Optional[str] = None,
    pid: Optional[int] = None,
    dry_run: bool = True,
) -> str:
    """List or terminate running processes."""
    log.debug(f"manage_processes, action={action}, filter={name_filter}, pid={pid}")

    if action == "list":
        return await asyncio.to_thread(_sync_list_processes, name_filter)
    elif action == "kill":
        if not pid and not name_filter:
            return "Specify a PID or name filter to terminate."
        return await asyncio.to_thread(_sync_kill_processes, pid, name_filter, dry_run)
    else:
        return "Invalid action. Use 'list' or 'kill'."
