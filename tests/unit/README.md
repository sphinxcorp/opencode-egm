# tests/unit

## Overview
Unit-level smoke test harness for the OpenCode plugin registration flow.

## Interface
- `opencode_plugin_harness.mjs` — fake OpenCode V2 context that loads the plugin, registers agents/commands/skills, and invokes `egm-review` once, printing the resulting registration JSON to stdout.

## Invariants
- Harness expects a plugin directory argument (`process.argv[2]`); defaults are not provided.
- Harness does not modify the source tree; it only imports and exercises registration.

## Side Effects
- Imports the plugin entry point (`index.ts`/`index.js`) from the supplied directory.
- Writes registration JSON to stdout.

## Verification
- Run: `node tests/unit/opencode_plugin_harness.mjs .`
