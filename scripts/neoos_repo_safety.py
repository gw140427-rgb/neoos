"""Read-only Git safety preflight for development automation."""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
from pathlib import Path

PROTECTED_BRANCHES = {"main", "master"}
TIMEOUT = 5


def inspect_repository(path="."):
    git_available = shutil.which("git") is not None
    try:
        candidate = Path(path).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return {"path": str(path), "safe_to_edit": False, "issues": ["path_unavailable"]}
    report = {
        "path": str(candidate), "repository_root": None,
        "git_available": git_available, "is_git_repository": False,
        "branch": None, "detached_head": False, "protected_branch": False,
        "worktree_clean": None, "changed_entry_count": None,
        "safe_to_edit": False, "issues": [],
    }
    if not candidate.is_dir():
        report["issues"].append("path_not_directory")
        return report
    if not git_available:
        report["issues"].append("git_not_available")
        return report
    try:
        root_result = subprocess.run(
            ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=TIMEOUT, check=False,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        report["issues"].append("git_check_unavailable")
        return report
    if root_result.returncode:
        report["issues"].append("not_a_git_repository")
        return report
    root = Path(root_result.stdout.strip()).resolve()
    report["repository_root"] = str(root)
    report["is_git_repository"] = True
    try:
        branch_result = subprocess.run(
            ["git", "-C", str(root), "branch", "--show-current"],
            capture_output=True, text=True, timeout=TIMEOUT, check=False,
        )
        status_result = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
            capture_output=True, text=True, timeout=TIMEOUT, check=False,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        report["issues"].append("repository_state_unavailable")
        return report
    if branch_result.returncode or status_result.returncode:
        report["issues"].append("repository_state_unavailable")
        return report
    branch = branch_result.stdout.strip()
    report["branch"] = branch or None
    report["detached_head"] = not bool(branch)
    report["protected_branch"] = branch in PROTECTED_BRANCHES
    report["worktree_clean"] = status_result.stdout == ""
    report["changed_entry_count"] = len(status_result.stdout.splitlines())
    if report["detached_head"]:
        report["issues"].append("detached_head")
    if report["protected_branch"]:
        report["issues"].append("protected_branch")
    if not report["worktree_clean"]:
        report["issues"].append("working_tree_dirty")
    report["safe_to_edit"] = not report["issues"]
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=".", help="repository directory to inspect")
    parser.add_argument("--require-safe", action="store_true",
                        help="exit 2 unless the worktree is clean and on a non-main branch")
    args = parser.parse_args(argv)
    result = inspect_repository(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if args.require_safe and not result["safe_to_edit"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
