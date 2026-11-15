<!-- Copyright 2026 Google LLC. SPDX-License-Identifier: Apache-2.0 -->

# OpenCode plugin integration (experimental)

This bundle is **OpenCode-only**. It contains no adapter or instruction set
for another coding agent. Every skill it ships uses OpenCode's tools and
dispatch model.

The plugin registers EGM through native OpenCode V2 plugin transforms:

- one primary orchestrator agent,
- eight read-only reviewer agents,
- seven slash commands,
- and the seven canonical skills.

It writes no agent, command, or skill files into OpenCode's discovery
directories, and it never edits `opencode.json`. Untrusted text cannot change
the registration because the definitions come from this bundle.

Validated against OpenCode **2.2.7**. This is a local experiment, not a
Google-supported product.

## Install

Build and copy the plugin in one step:

```sh
python3 install.py --config-dir ~/.config/opencode
```

The installer builds `dist/egm`, refuses to replace an existing plugin
directory, and reports any discovery-based EGM files that would duplicate its
agents, commands, or skills.

To install by hand, a plugin path must be a directory. Copy the built `egm`
directory into either OpenCode plugin location:

```sh
# Global: every project
cp -R dist/egm ~/.config/opencode/plugins/egm

# Or project-local
cp -R dist/egm .opencode/plugins/egm
```

OpenCode discovers both `~/.config/opencode/plugins/` and
`.opencode/plugins/`. You can also point at the directory explicitly:

```jsonc
{
  "plugins": ["./plugins/egm"]
}
```

Relative plugin paths resolve from the configuration file that contains them.
If the directory has a `package.json` with `name` and `exports`, OpenCode loads
it through those fields; otherwise it uses `index.js` at the root.

Restart the shared service after adding a plugin, or use `--standalone`:

```sh
opencode service restart
```

### Replacing an earlier EGM install

An earlier EGM integration for OpenCode was discovery-based: it wrote
`agents/egm*.md`, `commands/egm-*.md`, and `skills/egm-*`. Remove that install
before adding the plugin. OpenCode would otherwise register both definitions,
and the duplicate IDs are ambiguous. The earlier installer records its exact
created paths in `egm/installation.json`; remove only those tracked paths, then
restart the service.

## What gets registered

| Piece | Names |
| --- | --- |
| Orchestrator | `egm` |
| Reviewers | `egm-codebase-details`, `egm-comprehension`, `egm-design`, `egm-implementation-readiness`, `egm-inventive-catalyst`, `egm-structural`, `egm-style`, `egm-zoom-out` |
| Commands | `/egm-bootstrap`, `/egm-brainstorm`, `/egm-draft`, `/egm-drift-report`, `/egm-resolve`, `/egm-review`, `/egm-review-loop` |
| Skills | same seven IDs |

The plugin does **not** set `default_agent`. Other projects keep their current
default. Select EGM when you want it:

- Run any `/egm-*` command. Its executor switches the session to `egm` before
  submitting the skill request.
- Or select it first: `shift+tab` cycles agents and `<leader>a` lists them.

Confirm what the host loaded without a model call:

```sh
opencode debug config
opencode debug agents   # expect egm plus the eight reviewers
```

## Dispatch

The `egm` agent launches reviewers with the `subagent` tool, setting `agent` to
the persona ID and passing `description` plus a complete prompt.

V2 subagents always run in the background:

- `subagent` returns a `sessionID` immediately.
- The parent receives a `<subagent>` message when a child goes idle, and again
  after each later round of work.
- Passing the `sessionID` continues that child. EGM never does this: every
  independent review starts a new child, so reviewers cannot inherit earlier
  reviewer findings.

Pass a complete prompt: the task, absolute resource paths, the target, the
standards, and the selected reading list. Never pass conversation history,
private reasoning, or memory. Read prior reports only when explicitly supplied
and required by the canonical stage. Do not retrieve unsolicited history,
memory, or earlier reviewer findings.

The orchestrator writes reports and synthesis itself; reviewers return findings
only. `experimental.subagent_depth` defaults to 1, which is enough: reviewers
never delegate and the orchestrator is not itself a subagent. Because nesting
is unavailable, `egm-bootstrap` reads, scans, and writes contracts sequentially
in the orchestrator context instead of spawning sub-orchestrators.

## Permissions

Reviewers deny every action, then allow `read` and `glob`. `grep` stays denied
because its permission resource is the search pattern, not the file path, so it
cannot enforce the per-file `.env` rules. Code Mode (`execute`) is denied with
the rest, which also keeps MCP tools out of reach.

The orchestrator asks before other actions, allows reads, glob, grep, the seven
EGM skills, `question`, and the eight reviewer IDs. Writes ask for approval.

Both agents deny `external_directory` except for this plugin's bundle. A review
target outside the project is therefore unreadable; move the file into the
project instead. Neither agent denies `.env` reads silently: reviewers deny
them, the orchestrator asks.

Plugin-registered agents get exactly the rules above. OpenCode appends agent
rules after global configuration, so a later project or managed source can
still override them.

## Usage notes

- **Do not paste untrusted material into slash-command arguments.** OpenCode
  still evaluates `!` plus a backtick block in prompts before agent tool
  permissions apply, and Markdown fences do not disable it. Send review text as
  an ordinary message, or save it to a file and pass the path.
- **Send review requests as ordinary messages**, for example:
  `Use the egm-review skill to review /absolute/path/design.md`.
- **Artifact output directory**: add `EGM artifact directory: .dev/docs` to your
  prompt or to an `AGENTS.md` file the session loads.
- **Not supported**: bootstrap scout and worker delegation. Only the eight
  reviewer IDs may be dispatched; stop rather than substitute a reviewer.
- **One bundle per install**: update by replacing the plugin directory, not by
  editing files inside it.

## Verification limits

Installation checks do not prove workflow or isolation support.

- Read-only tool configuration is not process or filesystem isolation.
- A fresh child session alone does not prove Goldfish isolation. Host
  instruction files and inherited configuration can still reach a child.
- V2 merges custom, global, project, and managed configuration. Inspect the
  effective configuration before a run; later sources can override these
  permissions. A project-level agent with the same ID overrides this plugin's
  definition.
- `opencode debug config` and `opencode debug agents` prove that the host
  parsed and registered the definitions. They do not prove that a review runs,
  that delegation completes, or that permissions are enforced at run time.

## Uninstall

Remove the plugin directory and restart the service:

```sh
rm -rf ~/.config/opencode/plugins/egm   # or .opencode/plugins/egm
opencode service restart
```

No configuration key, agent file, command file, or skill link remains.
