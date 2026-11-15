# scripts

## Overview
Maintenance and validation helpers for the plugin bundle.

## Interface
- `validate-bundle.mjs` — validates bundle contents: scans for forbidden terms, checks agent/skill frontmatter names, verifies skill `SKILL.md` presence and referenced files.

## Invariants
- Validation runs against the `bundle/` directory relative to the repository root.
- Forbidden-term scan covers `.md`, `.json`, `.yaml`, `.yml`, `.txt`, `.js`, `.ts` files only.

## Side Effects
- Reads files under `bundle/` only; performs no writes.

## Verification
- Run: `npm run validate`
