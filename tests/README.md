# tests

## Overview
Test entry points for the plugin registration smoke test.

## Subdirectories & Boundaries
- [unit](./unit/README.md) - Plugin registration smoke harness (`opencode_plugin_harness.mjs`).

## Global Invariants
- Tests are excluded from production bundles beyond the smoke harness; no test fixtures are shipped.

## Global Side Effects
- None at this level; side effects are scoped to `tests/unit`.

## System Verification
- Run: `npm test`
