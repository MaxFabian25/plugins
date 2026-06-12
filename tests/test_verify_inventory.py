from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFY_INVENTORY_PATH = REPO_ROOT / "scripts" / "verify_inventory.py"
SPEC = importlib.util.spec_from_file_location("verify_inventory", VERIFY_INVENTORY_PATH)
assert SPEC is not None
verify_inventory = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verify_inventory)


def write_plugin(plugin_dir: Path, name: str) -> None:
    manifest_dir = plugin_dir / ".codex-plugin"
    manifest_dir.mkdir(parents=True)
    manifest = {
        "name": name,
        "version": "0.1.0",
    }
    (manifest_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")


def write_marketplace(root: Path, entries: list[tuple[str, str]]) -> Path:
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    marketplace_path.parent.mkdir(parents=True)
    data = {
        "name": "local-codex",
        "plugins": [
            {
                "name": name,
                "source": {
                    "source": "local",
                    "path": path,
                },
            }
            for name, path in entries
        ],
    }
    marketplace_path.write_text(json.dumps(data), encoding="utf-8")
    return marketplace_path


class VerifyInventoryTests(unittest.TestCase):
    def test_flat_plugin_repo_missing_from_marketplace_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugins_root = root / "plugins"
            write_plugin(plugins_root / "registered", "registered")
            write_plugin(plugins_root / "unregistered", "unregistered")
            marketplace_path = write_marketplace(
                root,
                [("registered", "./plugins/registered")],
            )

            plugins, errors = verify_inventory.load_marketplace_plugins(
                marketplace_path,
                plugins_root,
            )

        self.assertEqual(["registered"], sorted(plugins))
        self.assertTrue(
            any(
                "flat plugin repos missing marketplace entries: unregistered" in error
                for error in errors
            ),
            errors,
        )

    def test_registered_flat_plugin_repo_passes_disk_inventory_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugins_root = root / "plugins"
            write_plugin(plugins_root / "registered", "registered")
            marketplace_path = write_marketplace(
                root,
                [("registered", "./plugins/registered")],
            )

            plugins, errors = verify_inventory.load_marketplace_plugins(
                marketplace_path,
                plugins_root,
            )

        self.assertEqual(["registered"], sorted(plugins))
        self.assertEqual([], errors)

    def test_nested_marketplace_path_does_not_satisfy_flat_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugins_root = root / "plugins"
            write_plugin(plugins_root / "registered", "registered")
            write_plugin(
                plugins_root / "registered" / "plugins" / "registered",
                "registered",
            )
            marketplace_path = write_marketplace(
                root,
                [("registered", "./plugins/registered/plugins/registered")],
            )

            plugins, errors = verify_inventory.load_marketplace_plugins(
                marketplace_path,
                plugins_root,
            )

        self.assertEqual([], sorted(plugins))
        self.assertTrue(
            any(
                "marketplace entry 'registered' must use flat plugin path './plugins/registered'"
                in error
                for error in errors
            ),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
