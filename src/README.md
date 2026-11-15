# src

## Overview
Native OpenCode V2 plugin entry point. Registers the EGM orchestrator, eight
read-only reviewers, seven slash commands, and seven skills through plugin
transforms. It never writes configuration files and never changes the default
agent. The bundle is OpenCode-only.

## Interface
- `src/index.js:default` — default export `{ id: "egm", setup(ctx) }` consumed by OpenCode's plugin loader.
- `src/index.js:setup` — async setup that transforms agents, commands, and skills.
- `src/index.js:REVIEWERS` — canonical persona file to registered agent ID mapping.
- `src/index.js:SKILLS` — skill IDs registered from the bundle.
- `src/index.js:CONTEXT` — instruction prefix injected into agent system prompts.
- `src/index.js:splitFrontmatter` — parses YAML frontmatter from persona/skill Markdown.
- `src/index.js:headerValue` — extracts a scalar value from frontmatter.
- `src/index.js:persona` — reads a reviewer persona file and returns `{ body, description }`.
- `src/index.js:reviewerPermissions` — permission rules for reviewer subagents.
- `src/index.js:orchestratorPermissions` — permission rules for the `egm` orchestrator.
- `src/index.js:reviewerSystem` — system prompt builder for reviewer subagents.
- `src/index.js:orchestratorSystem` — system prompt builder for the orchestrator.
- Subdirectories: none.

## Invariants
- `src/index.js:ROOT` resolves to the directory containing `index.js`; `BUNDLE` is `ROOT/bundle` (`[src/index.js:ROOT]`, `[src/index.js:BUNDLE]`).
- Reviewer permissions deny all actions first, then allow `read`/`glob` and deny `.env` reads; `grep` stays denied (`[src/index.js:reviewerPermissions]`).
- Orchestrator permissions ask for mutations and allow EGM reads, skills, and reviewers only (`[src/index.js:orchestratorPermissions]`).
- Reviewers are registered with `mode: "subagent"`; the orchestrator with `mode: "primary"` (`[src/index.js:setup]`).
- No runtime import of `@opencode/plugin`; loaded via default export shape (`[src/index.js]` header comment).

## Side Effects
- Reads reviewer persona files and skill Markdown from `BUNDLE` at setup time (`[src/index.js:persona]`, `[src/index.js:setup]`).
- Calls `ctx.agent.transform`, `ctx.command.transform`, and `ctx.skill.transform` to register definitions (`[src/index.js:setup]`).
- Calls `ctx.session.switchAgent` and `ctx.session.prompt` when a slash command executes (`[src/index.js:setup]`).

## Verification
- Run: `pytest`
