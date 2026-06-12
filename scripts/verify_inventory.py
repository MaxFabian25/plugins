#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


LOCAL_CODEX_SUFFIX = "@local-codex"
CODEX_HOME = Path.home() / ".codex"
MARKETPLACE_ROOT = Path(__file__).resolve().parents[1]


def cache_version_dir_name(version: str) -> str:
    return version


def count_skill_files(root: Path) -> int:
    skills_root = root / "skills"
    if not skills_root.exists():
        return 0
    return sum(1 for path in skills_root.glob("*/SKILL.md") if path.is_file())


def load_marketplace_plugins(
    marketplace_path: Path, plugins_root: Path
) -> tuple[dict[str, tuple[Path, str]], list[str]]:
    errors: list[str] = []
    data = json.loads(marketplace_path.read_text(encoding="utf-8"))
    plugins: dict[str, tuple[Path, str]] = {}
    for entry in data.get("plugins", []):
        name = entry["name"]
        source = entry["source"]
        relative_path = source["path"] if isinstance(source, dict) else source
        expected_relative_path = f"./plugins/{name}"
        if relative_path != expected_relative_path:
            errors.append(
                f"marketplace entry {name!r} must use flat plugin path "
                f"{expected_relative_path!r}, got {relative_path!r}"
            )
            continue
        plugin_dir = marketplace_path.parent.parent.parent / relative_path
        manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
        if not plugin_dir.is_dir():
            errors.append(f"marketplace entry {name!r} points to missing plugin dir: {plugin_dir}")
            continue
        if not manifest_path.is_file():
            errors.append(f"plugin dir {plugin_dir} is missing manifest: {manifest_path}")
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("name") != name:
            errors.append(
                f"marketplace entry {name!r} does not match manifest name {manifest.get('name')!r}"
            )
        version = manifest.get("version")
        if not isinstance(version, str) or not version.strip():
            errors.append(f"plugin {name!r} manifest is missing a non-empty string version")
            version = ""
        elif version == "local" or "/" in version or "\\" in version or version in {".", ".."}:
            errors.append(f"plugin {name!r} manifest has unsafe cache version: {version!r}")
        plugins[name] = (plugin_dir, version)

    flat_plugin_repos, flat_plugin_errors = discover_flat_plugin_repos(plugins_root)
    errors.extend(flat_plugin_errors)
    missing_marketplace_entries = sorted(set(flat_plugin_repos) - set(plugins))
    if missing_marketplace_entries:
        errors.append(
            "flat plugin repos missing marketplace entries: "
            + ", ".join(
                f"{name} ({flat_plugin_repos[name]})" for name in missing_marketplace_entries
            )
        )

    source_dirs = sorted(path.name for path in plugins_root.iterdir() if path.is_dir())
    missing_dirs = sorted(set(plugins) - set(source_dirs))
    if missing_dirs:
        errors.append(f"plugins missing on disk for marketplace entries: {', '.join(missing_dirs)}")

    return plugins, errors


def discover_flat_plugin_repos(plugins_root: Path) -> tuple[dict[str, Path], list[str]]:
    errors: list[str] = []
    plugin_repos: dict[str, Path] = {}
    for plugin_dir in sorted(path for path in plugins_root.iterdir() if path.is_dir()):
        manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        name = manifest.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(
                f"flat plugin repo {plugin_dir} has manifest without a non-empty string name"
            )
            continue
        existing = plugin_repos.get(name)
        if existing is not None:
            errors.append(
                f"flat plugin manifest name {name!r} appears in multiple repos: {existing}, {plugin_dir}"
            )
            continue
        plugin_repos[name] = plugin_dir
    return plugin_repos, errors


def load_local_plugin_config(config_path: Path) -> tuple[list[str], list[str]]:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    configured_names: list[str] = []
    enabled_names: list[str] = []
    for key, value in data.get("plugins", {}).items():
        if not key.endswith("@local-codex"):
            continue
        name = key.removesuffix("@local-codex")
        configured_names.append(name)
        if value.get("enabled") is True:
            enabled_names.append(name)
    return sorted(configured_names), sorted(enabled_names)


def expected_cache_names(
    marketplace_plugins: dict[str, tuple[Path, str]], cache_root: Path, required_names: set[str]
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    seen: list[str] = []
    for name, (plugin_dir, version) in marketplace_plugins.items():
        if name not in required_names:
            continue
        cache_version = cache_version_dir_name(version)
        cache_plugin_root = cache_root / name
        cache_dir = cache_plugin_root / cache_version
        if not cache_dir.is_dir():
            errors.append(f"missing cache dir for {name!r}: {cache_dir}")
            continue
        legacy_cache_dir = cache_plugin_root / "local"
        if legacy_cache_dir.exists():
            errors.append(f"plugin cache for {name!r} contains stale legacy local dir: {legacy_cache_dir}")
        extra_entries = sorted(
            path.name for path in cache_plugin_root.iterdir() if path.is_dir() and path.name != cache_version
        )
        if extra_entries:
            errors.append(
                f"plugin cache for {name!r} contains unexpected version dirs: {', '.join(extra_entries)}"
            )
        manifest_path = cache_dir / ".codex-plugin" / "plugin.json"
        if not manifest_path.is_file():
            errors.append(f"cache dir for {name!r} is missing manifest: {manifest_path}")
        else:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("name") != name:
                errors.append(f"cache manifest for {name!r} has name {manifest.get('name')!r}")
            if manifest.get("version") != version:
                errors.append(
                    f"cache manifest for {name!r} has version {manifest.get('version')!r}, expected {version!r}"
                )
        if count_skill_files(plugin_dir) != count_skill_files(cache_dir):
            errors.append(
                f"cache skill count for {name!r} is {count_skill_files(cache_dir)}, "
                f"expected {count_skill_files(plugin_dir)}"
            )
        seen.append(name)
    cache_names = sorted(path.name for path in cache_root.iterdir() if path.is_dir())
    if sorted(seen) != sorted(set(cache_names) & set(required_names)):
        missing_cache = sorted(required_names - set(cache_names))
        extra_cache = sorted(set(cache_names) - set(marketplace_plugins))
        if missing_cache:
            errors.append(f"plugins missing from cache root: {', '.join(missing_cache)}")
        if extra_cache:
            errors.append(f"extra plugin cache dirs not in marketplace: {', '.join(extra_cache)}")
    return sorted(seen), errors


def normalize_runtime_plugin_name(raw: str) -> str:
    name = raw.strip().lstrip("-* ").strip()
    if name.endswith(LOCAL_CODEX_SUFFIX):
        return name[: -len(LOCAL_CODEX_SUFFIX)]
    return name


def runtime_names(skip_runtime: bool) -> list[str]:
    if skip_runtime:
        return []

    prompt = (
        "List the enabled plugins whose marketplace is local-codex. "
        "Reply with plugin names only, without the @local-codex suffix, one per line."
    )
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        output_path = Path(tmp.name)

    try:
        proc = subprocess.run(
            [
                "codex",
                "exec",
                "--skip-git-repo-check",
                "--ephemeral",
                "--output-last-message",
                str(output_path),
                prompt,
            ],
            cwd=Path.home() / ".codex",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            stderr = proc.stderr.strip() or "codex exec failed without stderr"
            raise RuntimeError(stderr)
        raw = output_path.read_text(encoding="utf-8")
    finally:
        output_path.unlink(missing_ok=True)

    return sorted(normalize_runtime_plugin_name(line) for line in raw.splitlines() if line.strip())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify local-codex inventory alignment across marketplace, config, cache, and runtime."
    )
    parser.add_argument(
        "--skip-runtime",
        action="store_true",
        help="Skip the fresh `codex exec` runtime discovery check.",
    )
    args = parser.parse_args()

    codex_home = CODEX_HOME
    marketplace_root = MARKETPLACE_ROOT
    marketplace_path = marketplace_root / ".agents" / "plugins" / "marketplace.json"
    plugins_root = marketplace_root / "plugins"
    config_path = codex_home / "config.toml"
    cache_root = codex_home / "plugins" / "cache" / "local-codex"

    errors: list[str] = []
    marketplace_plugins, marketplace_errors = load_marketplace_plugins(marketplace_path, plugins_root)
    errors.extend(marketplace_errors)
    marketplace_names = sorted(marketplace_plugins)

    configured_names, enabled_names = load_local_plugin_config(config_path)
    extra_config = sorted(set(configured_names) - set(marketplace_names))
    if extra_config:
        errors.append(
            f"local-codex config stanzas missing marketplace entries: {', '.join(extra_config)}"
        )

    cache_names, cache_errors = expected_cache_names(
        marketplace_plugins, cache_root, set(configured_names)
    )
    errors.extend(cache_errors)

    runtime_plugin_names: list[str] = []
    if not args.skip_runtime:
        try:
            runtime_plugin_names = runtime_names(skip_runtime=False)
        except Exception as exc:  # pragma: no cover - surfaced in CLI output
            errors.append(f"runtime discovery failed: {exc}")
        else:
            if runtime_plugin_names != enabled_names:
                missing_runtime = sorted(set(enabled_names) - set(runtime_plugin_names))
                extra_runtime = sorted(set(runtime_plugin_names) - set(enabled_names))
                if missing_runtime:
                    errors.append(
                        f"enabled local-codex plugins missing from fresh runtime discovery: {', '.join(missing_runtime)}"
                    )
                if extra_runtime:
                    errors.append(
                        f"fresh runtime discovery returned unexpected plugins: {', '.join(extra_runtime)}"
                    )

    if errors:
        print("local-codex inventory verification failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("local-codex inventory verification passed")
    print(f"marketplace/config/cache count: {len(marketplace_names)}")
    print(f"enabled local-codex count: {len(enabled_names)}")
    if not args.skip_runtime:
        print(f"runtime count: {len(runtime_plugin_names)}")
    print("plugins:")
    for name in marketplace_names:
        print(f"- {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
