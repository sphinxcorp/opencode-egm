# @sphinxcorp/opencode-egm

OpenCode V2 plugin for the Elephant & Goldfish Model (EGM).

EGM helps develop ideas with context and review documents with fresh eyes. It registers:

- One primary orchestrator agent: `egm`
- Eight read-only reviewer subagents (Goldfish reviewers)
- Seven slash commands: `/egm-bootstrap`, `/egm-brainstorm`, `/egm-draft`, `/egm-drift-report`, `/egm-resolve`, `/egm-review`, `/egm-review-loop`
- Seven skills with OpenCode-specific execution instructions

## Installation

From npm:

```sh
opencode plugin add @sphinxcorp/opencode-egm
```

Or add it to your `opencode.jsonc`:

```jsonc
{
  "plugins": ["@sphinxcorp/opencode-egm"]
}
```

## Usage

Run any EGM slash command in an OpenCode session, for example:

```
/egm-review /path/to/design.md
```

The orchestrator dispatches specialized reviewers in fresh subagent sessions and writes reports to your working directory.

## Repository structure

```
index.ts              # Plugin entry point (TypeScript)
bundle/               # Agents, skills, and resources shipped with the plugin
scripts/              # Validation and maintenance helpers
AGENTS.md             # Agent-driven upstream sync workflow
upstream.lock.json    # Last synced upstream commit
```

## Development

```sh
npm install
npm run validate      # Validate bundle contents
npm run build         # Typecheck
npm test              # Registration smoke test
```

## Upstream sync

This plugin ports content from https://github.com/google/elephant-goldfish-model.
See `AGENTS.md` for the agent-driven sync workflow that fetches upstream assets,
applies OpenCode rewrites, and validates before promotion.

## License

Apache-2.0
