# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Install the OpenCode-only EGM plugin into an OpenCode configuration directory.

The plugin is discovered from `<config>/plugins/egm`, so no `opencode.json`
change is required. Existing files are never replaced.
"""

import argparse
from pathlib import Path
import shutil

from build import DEFAULT_OUT, build

PLUGIN_NAME = "egm"
PRIOR_ARTIFACTS = (
    "agents/egm.md",
    "commands/egm-review.md",
    "skills/egm-review",
)


def default_config_dir() -> Path:
    """Match OpenCode's global configuration directory."""
    import os

    xdg = os.environ.get("XDG_CONFIG_HOME")
    return Path(xdg) / "opencode" if xdg else Path.home() / ".config/opencode"


def install(config_dir: Path, plugin: Path = DEFAULT_OUT) -> Path:
    config_dir = config_dir.expanduser().absolute()
    destination = config_dir / "plugins" / PLUGIN_NAME
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Already present: {destination}")

    built = build(plugin)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(built, destination)
    return destination


def prior_artifacts(config_dir: Path) -> list[Path]:
    """Report a previous discovery-based install, which would duplicate EGM."""
    config_dir = config_dir.expanduser().absolute()
    return [
        path
        for relative in PRIOR_ARTIFACTS
        if (path := config_dir / relative).exists() or path.is_symlink()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-dir", type=Path, default=None,
        help="OpenCode configuration directory (default: XDG or ~/.config/opencode)",
    )
    parser.add_argument(
        "--uninstall", action="store_true",
        help="Remove the installed plugin directory instead of installing",
    )
    arguments = parser.parse_args()
    config_dir = arguments.config_dir or default_config_dir()

    if arguments.uninstall:
        destination = config_dir.expanduser().absolute() / "plugins" / PLUGIN_NAME
        if not destination.exists():
            raise FileNotFoundError(destination)
        shutil.rmtree(destination)
        print(destination)
        return

    destination = install(config_dir)
    print(destination)
    stale = prior_artifacts(config_dir)
    if stale:
        print("Warning: a previous discovery-based EGM install is still present:")
        for path in stale:
            print(f"  {path}")
        print("Remove those files to avoid duplicate commands and agents.")


if __name__ == "__main__":
    main()
