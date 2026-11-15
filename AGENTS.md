# AGENTS.md

## Sync Upstream EGM Assets

This plugin is an OpenCode V2 port of https://github.com/google/elephant-goldfish-model.
The upstream repository owns `agents/`, `skills/`, and `resources/`. This repository owns
the OpenCode plugin runtime (`src/`), bundle validation, and OpenCode-specific rewrites.

### Workflow (agent-driven, ephemeral)

1. Read `upstream.lock.json` to find the last synced upstream commit.
2. Create a temp directory (e.g. `/tmp/egm-sync-XXXX`) and fetch upstream `main` into it.
   Do not add the clone to this repository's working tree.
3. Compare upstream `agents/`, `skills/`, and `resources/` against `bundle/`.
4. Apply OpenCode-specific rewrites to the fetched copy. Adapt to upstream wording/structure
   changes as needed. If a file cannot be safely rewritten, stop and report it.
5. Run `npm run validate`. Fix any failures before promotion.
6. Present a promotion diff and wait for approval.
7. On approval, overwrite `bundle/` with the validated upstream copy, update
   `upstream.lock.json` with the new commit SHA, and re-run `npm run validate`.
8. Remove the temp directory unless `--keep` was requested.

### Validation

- `npm run validate` must pass before and after promotion.
- `bundle/docs/` is plugin-owned; do not sync it from upstream.
- `src/index.ts` agent/skill lists must be updated manually when upstream adds or removes assets.

### Drift policy

- Prefer agent judgment over brittle text transforms.
- Never auto-promote without explicit approval.
- Keep all fetch/rewrite work ephemeral and disposable.