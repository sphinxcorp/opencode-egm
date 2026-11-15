# Design: @sphinxcorp/opencode-egm

**Author:** M N Islam Shihan
**Date:** 2026-11-15
**Status:** Draft

## Problem Statement

OpenCode users want the Elephant & Goldfish Model (EGM) workflow — brainstorming, drafting, reviewing, and resolving design documents with fresh reviewer personas — but EGM was originally built for other host environments. As of this design, no native OpenCode V2 plugin registers the EGM orchestrator, reviewer subagents, slash commands, and skills in an OpenCode session.

## Overview

This project is an OpenCode V2 plugin (`@sphinxcorp/opencode-egm`) that ports EGM into OpenCode. At plugin setup, it reads Markdown personas from `bundle/agents/` and skill definitions from `bundle/skills/`, then registers them with the OpenCode host as subagents, slash commands, and skills. The plugin entry point is `index.ts`. The bundle directory is the source of truth for content.

### Key Terms

- **EGM** — Elephant & Goldfish Model, the review workflow this plugin ports.
- **Upstream EGM** — https://github.com/google/elephant-goldfish-model, the source repository synced per `AGENTS.md`.
- **`AGENTS.md`** — agent-driven upstream sync workflow in this repo.
- **`bundle/`** — shipped content (agents, skills, resources); source of truth at runtime.
- **`bootstrap`** — the `/egm-bootstrap` skill that generates EGM contract READMEs.
- **`ctx`** — the OpenCode V2 plugin context passed to `setup()`; exposes `agent`, `command`, `skill`, `session` registries.
- **`bundle/resources/*`** — shared standards and execution instructions loaded by skills/reviewers; read-only reference assets, not loaded by `index.ts` at runtime.

## Goals

- Register one primary orchestrator agent (`egm`) and ten subagents in OpenCode: eight read-only reviewer personas plus `egm-bootstrap-orchestrator` and `egm-synthesizer`.
- Register seven slash commands (`/egm-bootstrap`, `/egm-brainstorm`, `/egm-draft`, `/egm-drift-report`, `/egm-resolve`, `/egm-review`, `/egm-review-loop`).
- Register seven skills whose `SKILL.md` body content provides the execution instructions.
- Keep bundle content in sync with upstream EGM via an agent-driven workflow.

## Non-Goals

- Implementing production code changes beyond the plugin registration layer.
- Modifying upstream EGM content directly without the sync workflow.
- Providing runtime services beyond agent/command/skill registration.

## Proposed Architecture

### Architecture

The plugin is a single-file TypeScript module (`index.ts`) built with `@opencode/plugin`. At setup time it:

1. Reads every `*.md` under `bundle/agents/` and parses YAML frontmatter to build reviewer personas (`loadPersonas`).
2. Reads every directory under `bundle/skills/` that contains `SKILL.md` and parses frontmatter (`loadSkills`).
3. Transforms the OpenCode agent registry: each persona becomes a subagent with read-only permissions; the primary `egm` agent gets orchestrator permissions and a system prompt listing reviewer IDs.
4. Transforms commands: each skill becomes a slash command that switches the session agent to `egm` and prompts with the skill content.
5. Transforms skills: each skill's metadata and body content are registered.

### Components and Files

- `index.ts` — entry point; contains `splitFrontmatter`, `headerValue`, `loadPersonas`, `loadSkills`, `reviewerPermissions`, `orchestratorPermissions`, `reviewerSystem`, `orchestratorSystem`, and the default `Plugin.define` export.
- `bundle/` — source of truth for agents, skills, and resources.
- `scripts/validate-bundle.mjs` — bundle validation (forbidden terms, frontmatter, references).
- `tests/unit/opencode_plugin_harness.mjs` — registration smoke test against a fake OpenCode V2 context.
- `tsconfig.json`, `package.json` — build/test configuration.

### Data Flow

```text
bundle/agents/*.md  --> loadPersonas()  --> ctx.agent.transform (subagents)
bundle/skills/*/SKILL.md --> loadSkills() --> ctx.command.transform (slash commands)
                                         --> ctx.skill.transform (skills)
```

### Permissions Model

- Reviewers: deny-all default, allow read/glob/grep/external_directory for all resources (`*`), deny `*.env`/`*.env.*` reads, allow `*.env.example`. All ten personas (eight reviewers plus `egm-bootstrap-orchestrator` and `egm-synthesizer`) share this set; report-writing is performed by the orchestrator, which holds edit permission.
- Orchestrator: ask-by-default, allow read/glob/grep/question/skill (egm-* only) and subagent for registered reviewer IDs, ask for external directories except `bundle/*`.

### Build and Validation

- `npm run build` — typecheck with `tsc`, then copy `bundle/` to `dist/bundle`.
- `npm run validate` — run `scripts/validate-bundle.mjs`.
- `npm test` — run the harness against the built plugin.

## Risks & Mitigations

- **Reviewer permission mismatch** — Reviewers may be unable to read/grep targets outside `bundle/`. Mitigation: align `reviewerPermissions()` with mandates (Phase B item 5) and document the readable path boundary.
- **Bundle load failure** — Missing/malformed persona or skill aborts setup. Mitigation: guard `loadSkills()` with `existsSync` (Phase A item 4) and validate bundle at build time via `npm run validate`.
- **Agent count drift** — `loadPersonas()` registers every `*.md` under `bundle/agents/`; count can drift from docs. Mitigation: reconcile count and document taxonomy (Phase A item 3).
- **Single-file module limits** — `index.ts` couples loading, permissions, prompts; becomes hard to test past ~500 lines. Mitigation: monitor size; split into modules if growth warrants (Alternative 2).
- **Frontmatter parser brittleness** — `headerValue` only handles single-line fields. Mitigation: document invariant; revisit if multi-line fields needed.
- **Upstream sync drift** — Bundle content can diverge from upstream EGM. Mitigation: agent-driven sync workflow in `AGENTS.md` plus `npm run validate`.

## Alternatives Considered

1. **Wrap upstream EGM as a CLI/MCP server instead of a native plugin** — Rejected by author: would require users to run a separate process and would not integrate with OpenCode's agent/command/skill registries, losing the native slash-command and subagent UX. The native plugin keeps everything in-process and registered at setup.

2. **Multi-module split (loaders, permissions, prompts) instead of single `index.ts`** — Rejected by author: the module is small (~225 lines) and a single file keeps the port aligned with upstream and simplifies build/validation. Reconsider if the module grows beyond ~500 lines or gains independent test requirements.

3. **Lazy bundle loading at first command instead of setup-time loading** — Rejected by author: setup-time loading surfaces missing/malformed bundle errors immediately and keeps command execution synchronous. Lazy loading would add partial-state complexity with no expected benefit at current bundle size.

## Detailed Implementation

### Implementation List (phased)

**Phase A — Setup and loading (Modify `index.ts`)**
1. `index.ts` (Modify) — `splitFrontmatter()`: keep regex parser; document invariant that frontmatter fields are single-line `key: value`. Verification: `npm test`.
2. `index.ts` (Modify) — `headerValue()`: unchanged; same invariant. Verification: `npm test`.
3. `index.ts` (Modify) — `loadPersonas()`: register all `*.md` under `bundle/agents/` (10 personas). Verification: harness reports 10 subagents (plus 1 primary agent = 11 total).
4. `index.ts` (Modify) — `loadSkills()`: guard with `existsSync(skillPath)`; skip directories lacking `SKILL.md` instead of throwing. Verification: `npm test` with a stray directory present.

**Phase B — Permissions (Modify `index.ts`)**
5. `index.ts` (Modify) — `reviewerPermissions()`: allow `read`, `glob`, `grep`, and `external_directory` for all resources (`*`); deny `*.env`/`*.env.*` reads; allow `*.env.example`. Verification: harness + manual review of permission list.
6. `index.ts` (Modify) — `orchestratorPermissions(reviewerIDs)`: keep ask-by-default; allow subagent for all IDs returned by `loadPersonas()`. Verification: harness.

**Phase C — Registration (Modify `index.ts`)**
7. `index.ts` (Modify) — `reviewerSystem(personaPath)`, `orchestratorSystem(reviewerIDs)`: unchanged signatures. Verification: `npm test`.
8. `index.ts` (Modify) — default `Plugin.define` export `setup()`: transform agent/command/skill registries. Verification: harness invokes `egm-review` and reports 7 commands, 7 skills.

**Phase D — Bundle and validation (Modify/Create as needed)**
9. `bundle/agents/*.md` (existing, Verify) — 10 persona files; verify each has frontmatter `name`/`description` and passes `npm run validate`. No content changes required unless validation fails.
10. `bundle/skills/*/SKILL.md` (existing) — 7 skill files. Verification: `npm run validate`.
11. `scripts/validate-bundle.mjs` (Modify only if new rules needed) — forbidden-term scan, frontmatter, reference resolution. Verification: `npm run validate`.
12. `tests/unit/opencode_plugin_harness.mjs` (Modify) — happy path: 10 agents, 7 commands, 7 skills, `egm-review` invocation; edge cases: missing frontmatter file skipped, empty bundle. Verification: `npm test`.

**Phase E — Build config (existing)**
13. `package.json`, `tsconfig.json` (existing) — build/validate/test scripts. Verification: `npm run build`.

**Phase F — Documentation contracts (existing README.md files)**
14. `README.md` (repo root), `bundle/README.md`, `bundle/resources/README.md`, `bundle/skills/README.md`, `bundle/skills/*/README.md` (`bundle/agents/` has no README contract), `scripts/README.md`, `tests/README.md`, `tests/unit/README.md` — EGM contract docs describing interfaces, invariants, side effects. Generated/curated; not a runtime component. Verification: `npm run validate` (links resolve).