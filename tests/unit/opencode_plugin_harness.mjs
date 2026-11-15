// Copyright 2026 Google LLC.
// SPDX-License-Identifier: Apache-2.0

/**
 * Execute the built plugin against a fake OpenCode V2 context.
 *
 * It mirrors the editor contracts in `@opencode/plugin/promise`: agents start
 * from `Agent.Info.default`, commands only add definitions, and skills only add
 * metadata plus content. The JSON on stdout is the observable registration
 * result, including one slash-command invocation.
 *
 * Usage: node opencode_plugin_harness.mjs <plugin-directory>
 */

import path from "node:path"
import { pathToFileURL } from "node:url"

const directory = process.argv[2]
if (!directory) throw new Error("usage: opencode_plugin_harness.mjs <plugin-directory>")

const { default: plugin } = await import(pathToFileURL(path.join(directory, "index.js")).href)

const agents = new Map()
const commands = new Map()
const skills = new Map()
const calls = []

// Mirrors Agent.Info.default from packages/schema/src/agent.ts.
function defaultAgent(id) {
  return {
    id,
    name: id,
    request: { settings: {}, headers: {}, body: {} },
    mode: "primary",
    hidden: false,
    permissions: [
      { action: "*", resource: "*", effect: "allow" },
      { action: "read", resource: "*.env", effect: "ask" },
      { action: "read", resource: "*.env.*", effect: "ask" },
      { action: "read", resource: "*.env.example", effect: "allow" },
    ],
  }
}

const ctx = {
  agent: {
    transform(fn) {
      fn({
        list: () => [...agents.values()],
        get: (id) => agents.get(id),
        default: (id) => calls.push(["agent.default", id]),
        update: (id, update) => {
          const agent = agents.get(id) ?? defaultAgent(id)
          if (!agents.has(id)) agents.set(id, agent)
          update(agent)
          agent.id = id
        },
        remove: (id) => agents.delete(id),
      })
    },
  },
  command: {
    transform(fn) {
      fn({
        add: (definition) => commands.set(definition.name, definition),
      })
    },
  },
  skill: {
    transform(fn) {
      fn({
        add: (skill) => skills.set(skill.id, skill),
      })
    },
  },
  session: {
    async switchAgent(input) {
      calls.push(["switchAgent", input])
    },
    async prompt(input) {
      calls.push(["prompt", input])
    },
  },
}

await plugin.setup(ctx)

const command = commands.get("egm-review")
await command.execute({
  sessionID: "ses_harness",
  prompt: { text: "Review /tmp/design.md" },
  delivery: "queue",
})

process.stdout.write(
  JSON.stringify({
    id: plugin.id,
    agents: [...agents.values()],
    commands: [...commands.keys()],
    skills: [...skills.values()],
    calls,
  }),
)
