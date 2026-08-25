"""CLI interface for ContextPreloader management."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from scripts.domain.exceptions import ConfigError
from scripts.infrastructure.config_repository import (
    list_profiles,
    load_config,
    load_profile_sources,
)
from scripts.infrastructure.path_resolver import (
    get_default_config_path,
    get_profiles_dir,
)


def cmd_list(config_path: str, profile: str | None) -> list[dict[str, Any]]:
    """List all configured sources. Returns list of dicts."""
    cfg = load_config(config_path)
    sources = [
        {"id": s.id, "label": s.label, "path": s.path, "type": s.type, "enabled": s.enabled}
        for s in cfg.sources
    ]

    if profile:
        profile_sources = load_profile_sources(profile)
        sources.extend(
            {"id": s.id, "label": s.label, "path": s.path, "type": s.type, "enabled": s.enabled, "profile": True}
            for s in profile_sources
        )

    return sources


def _generate_id(path: str) -> str:
    """Generate a source ID from a path."""
    basename = Path(path).name.rsplit(".", 1)[0] if "/" in path or "\\" in path else path
    return re.sub(r"[^a-z0-9]+", "-", basename.lower()).strip("-") or "source"


def cmd_add(
    config_path: str,
    path: str,
    label: str,
    src_type: str,
    profile: str | None,
) -> None:
    """Add a new source to config or profile."""
    target_path = profile if profile else config_path
    src_id = _generate_id(path)

    with Path(target_path).open(encoding="utf-8") as f:
        data = json.load(f)

    new_source = {
        "id": src_id,
        "label": label,
        "path": path,
        "type": src_type,
        "enabled": True,
    }
    data.setdefault("sources", []).append(new_source)

    with Path(target_path).open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cmd_remove(config_path: str, src_id: str, profile: str | None) -> None:
    """Remove a source by ID.

    Raises:
        ValueError: If source ID not found.
    """
    target_path = profile if profile else config_path

    with Path(target_path).open(encoding="utf-8") as f:
        data = json.load(f)

    original_len = len(data.get("sources", []))
    data["sources"] = [s for s in data.get("sources", []) if s.get("id") != src_id]

    if len(data["sources"]) == original_len:
        raise ValueError(f"Source ID '{src_id}' not found")

    with Path(target_path).open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cmd_test(config_path: str, profile: str | None) -> list[dict[str, Any]]:
    """Test all sources for accessibility. Returns list of test results."""
    from scripts.domain.detection import is_url

    cfg = load_config(config_path)
    sources = list(cfg.sources)

    if profile:
        try:
            profile_sources = load_profile_sources(profile)
            sources.extend(profile_sources)
        except ConfigError:
            pass

    results = []
    for s in sources:
        if is_url(s.path):
            results.append({"id": s.id, "path": s.path, "status": "ok", "note": "URL (not tested)"})
        elif Path(s.path).exists():
            results.append({"id": s.id, "path": s.path, "status": "ok"})
        else:
            results.append({"id": s.id, "path": s.path, "status": "missing"})

    return results


def cmd_status() -> dict[str, Any]:
    """Check setup state. Returns dict with status of each component."""

    config_path = get_default_config_path()
    profiles_dir = get_profiles_dir()
    hook_path = Path.home() / ".claude" / "hooks" / "context_preloader.py"

    # 1. Config exists?
    config_ok = config_path.exists()

    # 2. Hook launcher exists?
    hook_ok = hook_path.exists()

    # 3. settings.json has ContextPreloader hook?
    # Walk up from CWD to find .claude/settings.json (like git finds .git/)
    settings_ok = False
    settings_path = None
    candidates = []
    d = Path.cwd()
    while True:
        candidates.append(d / ".claude" / "settings.json")
        parent = d.parent
        if parent == d:
            break
        d = parent
    candidates.append(Path.home() / ".claude" / "settings.json")

    for candidate in candidates:
        if candidate.exists():
            try:
                import json as _json
                with Path(candidate).open(encoding="utf-8") as f:
                    settings = _json.load(f)
                hooks = settings.get("hooks", {}).get("SessionStart", [])
                for group in hooks:
                    for h in group.get("hooks", []):
                        if "context_preloader" in h.get("command", ""):
                            settings_ok = True
                            settings_path = str(candidate)
                            break
            except Exception:
                pass
            if settings_ok:
                break

    # 4. Profiles
    profiles = list_profiles(profiles_dir)

    # 5. Source count
    source_count = 0
    if config_ok:
        try:
            cfg = load_config(str(config_path))
            source_count = len(cfg.sources)
        except ConfigError:
            pass

    ready = config_ok and hook_ok and settings_ok

    return {
        "ready": ready,
        "config": {"ok": config_ok, "path": str(config_path)},
        "hook": {"ok": hook_ok, "path": str(hook_path)},
        "settings": {"ok": settings_ok, "path": settings_path},
        "profiles": profiles,
        "global_sources": source_count,
    }


def cmd_profiles(profiles_dir: str) -> list[str]:
    """List available profile names."""
    return list_profiles(profiles_dir)


def main() -> None:
    """CLI entry point with argparse."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="ContextPreloader CLI")
    parser.add_argument("--config", default=str(get_default_config_path()),
                        help="Config file path")
    parser.add_argument("--profile", default=None,
                        help="Profile name or path")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Check setup state")
    subparsers.add_parser("list", help="List sources")
    subparsers.add_parser("profiles", help="List profiles")
    subparsers.add_parser("test", help="Test sources")

    add_parser = subparsers.add_parser("add", help="Add source")
    add_parser.add_argument("--path", required=True)
    add_parser.add_argument("--label", required=True)
    add_parser.add_argument("--type", default="auto", dest="src_type")

    remove_parser = subparsers.add_parser("remove", help="Remove source")
    remove_parser.add_argument("--id", required=True, dest="src_id")

    args = parser.parse_args()

    # Resolve profile path if profile name given
    profile_path = None
    if args.profile:
        if Path(args.profile).exists():
            profile_path = args.profile
        else:
            from scripts.infrastructure.path_resolver import get_profile_path
            profile_path = str(get_profile_path(args.profile))

    # 分岐ごとに戻り値の型が違う（dict / list[dict] / list[str]）。直後に
    # json.dumps へ渡すだけなので Any で受ける。
    result: Any

    if args.command == "status":
        result = cmd_status()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "list":
        result = cmd_list(args.config, profile_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "profiles":
        result = cmd_profiles(str(get_profiles_dir()))
        print(json.dumps(result, indent=2))

    elif args.command == "test":
        result = cmd_test(args.config, profile_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "add":
        cmd_add(args.config, args.path, args.label, args.src_type, profile_path)
        print(json.dumps({"status": "ok", "path": args.path}))

    elif args.command == "remove":
        try:
            cmd_remove(args.config, args.src_id, profile_path)
            print(json.dumps({"status": "ok", "id": args.src_id}))
        except ValueError as e:
            print(json.dumps({"status": "error", "message": str(e)}))
            sys.exit(1)

    else:
        # No subcommand = hook mode
        from scripts.interfaces.hook_runner import run_hook
        run_hook(profile_path)
