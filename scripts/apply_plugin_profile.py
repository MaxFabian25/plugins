#!/usr/bin/env python3
"""Apply and verify Codex plugin enablement profiles."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


CODEX_HOME = Path.home() / ".codex"
MARKETPLACE_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = MARKETPLACE_ROOT / "scripts" / "plugin_profiles.json"
CONFIG_PATH = CODEX_HOME / "config.toml"


PLUGIN_BLOCK_RE = re.compile(r'(?ms)^\[plugins\."([^"]+)"\]\n(.*?)(?=^\[|\Z)')
FRONTMATTER_NAME_RE = re.compile(r"(?ms)^---\n(.*?)\n---")


def load_profiles(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def plugin_blocks(config_text: str) -> dict[str, tuple[int, int, str]]:
    return {
        match.group(1): (match.start(), match.end(), match.group(2))
        for match in PLUGIN_BLOCK_RE.finditer(config_text)
    }


def enabled_from_config(config_text: str) -> set[str]:
    enabled: set[str] = set()
    for plugin_id, (_, _, body) in plugin_blocks(config_text).items():
        if re.search(r"(?m)^enabled\s*=\s*true\s*$", body):
            enabled.add(plugin_id)
    return enabled


def resolve_profile(
    profiles: dict[str, Any], profile_name: str, configured_plugins: set[str]
) -> tuple[set[str], dict[str, Any]]:
    if profile_name not in profiles:
        raise KeyError(f"Unknown profile: {profile_name}")
    profile = profiles[profile_name]
    if profile.get("enableAllConfigured") is True:
        enabled = set(configured_plugins)
    elif "enabled" in profile:
        enabled = set(profile["enabled"])
    else:
        parent = profile.get("extends")
        enabled = resolve_profile(profiles, parent, configured_plugins)[0] if parent else set()
        enabled.update(profile.get("enable", []))
        enabled.difference_update(profile.get("disable", []))

    unknown = sorted(enabled - configured_plugins)
    if unknown:
        raise ValueError(f"Profile {profile_name!r} references unknown plugin stanzas: {', '.join(unknown)}")
    return enabled, profile


def set_enabled_in_body(body: str, enabled: bool) -> str:
    replacement = f"enabled = {'true' if enabled else 'false'}"
    if re.search(r"(?m)^enabled\s*=", body):
        body = re.sub(r"(?m)^enabled\s*=.*$", replacement, body)
    else:
        body = f"{replacement}\n{body}"
    return body if body.endswith("\n") else f"{body}\n"


def apply_profile(config_path: Path, enabled: set[str]) -> None:
    text = config_path.read_text(encoding="utf-8")
    pieces: list[str] = []
    cursor = 0
    for match in PLUGIN_BLOCK_RE.finditer(text):
        pieces.append(text[cursor : match.start()])
        plugin_id = match.group(1)
        body = set_enabled_in_body(match.group(2), plugin_id in enabled)
        pieces.append(f'[plugins."{plugin_id}"]\n{body}')
        cursor = match.end()
    pieces.append(text[cursor:])
    config_path.write_text("".join(pieces), encoding="utf-8")


def skill_name(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    match = FRONTMATTER_NAME_RE.search(text)
    if not match:
        return skill_md.parent.name
    for line in match.group(1).splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("'\"") or skill_md.parent.name
    return skill_md.parent.name


def plugin_cache_root(plugin_id: str) -> Path:
    name, marketplace = plugin_id.rsplit("@", 1)
    return CODEX_HOME / "plugins" / "cache" / marketplace / name


def expected_prompt_skills(enabled: set[str]) -> set[str]:
    expected: set[str] = set()
    for plugin_id in enabled:
        name, _ = plugin_id.rsplit("@", 1)
        root = plugin_cache_root(plugin_id)
        if not root.exists():
            continue
        for version in sorted(path for path in root.iterdir() if path.is_dir()):
            skills_root = version / "skills"
            if not skills_root.exists():
                continue
            for skill_md in sorted(skills_root.glob("*/SKILL.md")):
                expected.add(f"{name}:{skill_name(skill_md)}")
    return expected


def prompt_visible_skills() -> list[str]:
    result = subprocess.run(
        ["codex", "debug", "prompt-input", "inventory profile smoke"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "codex debug prompt-input failed")
    payload = json.loads(result.stdout)
    texts: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, str):
            texts.append(value)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)

    walk(payload)
    blob = "\n".join(texts)
    match = re.search(r"### Available skills\n(.*?)### How to use skills", blob, re.S)
    if not match:
        raise RuntimeError("prompt input did not include an available skills section")
    visible: list[str] = []
    for line in match.group(1).splitlines():
        if line.startswith("- "):
            entry = line[2:].split(" (file:", 1)[0]
            visible.append(entry.rsplit(": ", 1)[0])
    return visible


def verify_profile(
    config_path: Path,
    profile_name: str,
    expected_enabled: set[str],
    profile: dict[str, Any],
    *,
    compare_config: bool,
    check_prompt: bool,
) -> list[str]:
    failures: list[str] = []
    config_text = config_path.read_text(encoding="utf-8")
    actual_enabled = enabled_from_config(config_text)
    if compare_config and actual_enabled != expected_enabled:
        missing = sorted(expected_enabled - actual_enabled)
        extra = sorted(actual_enabled - expected_enabled)
        if missing:
            failures.append(f"expected enabled plugins are disabled: {', '.join(missing)}")
        if extra:
            failures.append(f"unexpected enabled plugins: {', '.join(extra)}")

    expected_skills = expected_prompt_skills(expected_enabled)
    max_visible = profile.get("maxVisibleSkills")
    if isinstance(max_visible, int) and len(expected_skills) > max_visible:
        failures.append(
            f"profile {profile_name!r} exposes {len(expected_skills)} cache skills, above maxVisibleSkills={max_visible}"
        )

    missing_cache_roots = sorted(
        plugin_id for plugin_id in expected_enabled if not plugin_cache_root(plugin_id).is_dir()
    )
    if missing_cache_roots:
        failures.append(f"enabled plugins missing cache roots: {', '.join(missing_cache_roots)}")

    if check_prompt:
        visible_skill_list = prompt_visible_skills()
        visible_plugin_skills = {
            skill for skill in visible_skill_list if ":" in skill
        }
        missing_visible = sorted(expected_skills - visible_plugin_skills)
        extra_visible = sorted(visible_plugin_skills - expected_skills)
        duplicate_names = sorted(
            name for name, count in Counter(visible_skill_list).items() if count > 1
        )
        if missing_visible:
            failures.append(
                "enabled cache skills missing from prompt surface: " + ", ".join(missing_visible)
            )
        if extra_visible:
            failures.append(
                "prompt surface includes skills outside enabled cache set: " + ", ".join(extra_visible)
            )
        if duplicate_names:
            failures.append("duplicate prompt skill entries: " + ", ".join(duplicate_names))

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["list", "apply", "verify"])
    parser.add_argument("profile", nargs="?", default="default")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--profiles", type=Path, default=PROFILE_PATH)
    parser.add_argument("--check-prompt", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "For apply, print the target plugin set. For verify, validate the "
            "profile target without requiring the current config to match it."
        ),
    )
    args = parser.parse_args()

    profiles = load_profiles(args.profiles)
    config_text = args.config.read_text(encoding="utf-8")
    configured_plugins = set(plugin_blocks(config_text))

    if args.command == "list":
        for name, profile in profiles.items():
            print(f"{name}: {profile.get('description', '')}")
        return 0

    try:
        enabled, profile = resolve_profile(profiles, args.profile, configured_plugins)
    except (KeyError, ValueError) as exc:
        message = exc.args[0] if exc.args else str(exc)
        print(message, file=sys.stderr)
        return 2

    if args.command == "apply":
        if args.dry_run:
            for plugin_id in sorted(enabled):
                print(plugin_id)
        else:
            apply_profile(args.config, enabled)
            print(f"Applied plugin profile {args.profile}: {len(enabled)} enabled plugins")
        return 0

    failures = verify_profile(
        args.config,
        args.profile,
        enabled,
        profile,
        compare_config=not args.dry_run,
        check_prompt=args.check_prompt,
    )
    if failures:
        print(f"Plugin profile {args.profile!r} verification failed", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    expected_skills = expected_prompt_skills(enabled)
    print(
        f"Plugin profile {args.profile!r} verified: "
        f"{len(enabled)} enabled plugins, {len(expected_skills)} enabled cache skills"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
