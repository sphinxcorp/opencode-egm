# egm-opencode-plugin Blueprint

## System Overview
Native OpenCode plugin packaging the Elephant & Goldfish Model (EGM). The
plugin registers one primary orchestrator (`egm`), eight read-only reviewer
subagents, seven slash commands, and seven skills via OpenCode V2 plugin
transforms. It writes no configuration files and never changes the default
agent. The bundle is OpenCode-only.

## Local Interface & Invariants
- `build.py:build` — generates a loadable plugin directory (`dist/egm`) from `canonical/` and `src/`, rewriting harness-specific instructions to OpenCode; fails on stale rewrites or forbidden harness names.
- `build.py:ROOT` — `canonical/` directory; `build.py:HERE` — repository root; `build.py:DEFAULT_OUT` — `dist/egm`.
- `build.py:REVIEWER_FILES`, `build.py:SKILLS` — canonical lists of reviewer personas and skill IDs.
- `build.py:FORBIDDEN` — regex rejecting non-OpenCode harness names in built output.
- `install.py:install` — copies the built plugin into `<config>/plugins/egm`; refuses to overwrite an existing install.
- `install.py:default_config_dir` — resolves OpenCode global config dir via `XDG_CONFIG_HOME` or `~/.config/opencode`.
- `install.py:prior_artifacts` — detects a previous discovery-based EGM install that would duplicate registration.
- `install.py:main` — CLI entry point (`--config-dir`, `--uninstall`).
- Invariant: build output must contain no agent/command/skill discovery files (`[build.py:build]`).
- Invariant: installer never replaces an existing plugin directory (`[install.py:install]`).

## Subdirectories & System Boundaries
- [src](./src/README.md) - Native OpenCode V2 plugin entry point registering agents, commands, and skills.

## Global Invariants
- The bundle is OpenCode-only; no adapter or instruction set for other coding agents is shipped (`[src/index.js]` header, `[build.py]` docstring).
- `experimental.subagent_depth` defaults to 1; reviewers never delegate (`[docs/opencode-plugin.md]`).

## Global Side Effects
- `build()` writes to `dist/egm` and removes any prior output at that path (`[build.py:build]`).
- `install()` copies the built tree into the OpenCode configuration directory (`[install.py:install]`).

## System Verification
- Run: `pytest`
