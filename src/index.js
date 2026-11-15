// Copyright 2026 Google LLC.
// SPDX-License-Identifier: Apache-2.0

/**
 * Native OpenCode V2 plugin for the Elephant & Goldfish Model (EGM).
 *
 * It registers one primary orchestrator, eight read-only reviewers, the seven
 * EGM slash commands, and the canonical skills through the plugin transforms.
 * It never writes configuration files and never changes the default agent.
 *
 * This bundle is OpenCode-only. Instructions for other coding agents are
 * intentionally not included.
 *
 * Loaded module shape: OpenCode accepts a default export with `id` and
 * `setup`, so this file imports nothing from `@opencode/plugin` at runtime.
 */

import { readFileSync } from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const ROOT = path.dirname(fileURLToPath(import.meta.url))
const BUNDLE = path.join(ROOT, "bundle")
const GUIDE = path.join(BUNDLE, "docs/opencode-plugin.md")

/** Canonical persona file -> registered agent ID. */
const REVIEWERS = [
  ["codebase_details", "egm-codebase-details"],
  ["comprehension", "egm-comprehension"],
  ["design_critic", "egm-design"],
  ["implementation_readiness", "egm-implementation-readiness"],
  ["inventive_catalyst", "egm-inventive-catalyst"],
  ["structural", "egm-structural"],
  ["style", "egm-style"],
  ["zoom_out", "egm-zoom-out"],
]

const SKILLS = [
  "egm-bootstrap",
  "egm-brainstorm",
  "egm-draft",
  "egm-drift-report",
  "egm-resolve",
  "egm-review",
  "egm-review-loop",
]

const CONTEXT =
  `Read ${GUIDE} first. EGM bundle root: ${BUNDLE}. ` +
  "Resolve agents/, resources/, and docs/ against this root. " +
  "Resolve references/ against the canonical skill directory. " +
  "Resolve user files and outputs against the project working directory. "

function splitFrontmatter(text) {
  const match = /^---\n([\s\S]*?)\n---\n?/.exec(text)
  if (!match) return { header: "", body: text }
  return { header: match[1], body: text.slice(match[0].length) }
}

function headerValue(header, key) {
  const match = new RegExp(`^${key}:\\s*(.+)$`, "m").exec(header)
  return match ? match[1].trim().replace(/^["']|["']$/g, "") : ""
}

function persona(file) {
  const text = readFileSync(path.join(BUNDLE, "agents", `${file}.md`), "utf8")
  const { header, body } = splitFrontmatter(text)
  return { body, description: headerValue(header, "description") }
}

/**
 * Allow file discovery only; deny everything else, including Code Mode.
 *
 * V2 applies the last matching rule, so the `.env` denies must follow the broad
 * `read` allow, and the bundle exception must follow the broad
 * `external_directory` deny. `grep` stays denied because its permission
 * resource is the search pattern, not the path, so it cannot enforce the
 * per-file `.env` rules.
 */
function reviewerPermissions() {
  return [
    { action: "*", resource: "*", effect: "deny" },
    { action: "read", resource: "*", effect: "allow" },
    { action: "read", resource: "*.env", effect: "deny" },
    { action: "read", resource: "*.env.*", effect: "deny" },
    { action: "read", resource: "*.env.example", effect: "allow" },
    { action: "glob", resource: "*", effect: "allow" },
    { action: "grep", resource: "*", effect: "deny" },
    { action: "external_directory", resource: "*", effect: "deny" },
    { action: "external_directory", resource: `${BUNDLE}/*`, effect: "allow" },
  ]
}

/** Ask for workspace mutations; allow EGM reads, skills, and reviewers. */
function orchestratorPermissions(reviewerIDs) {
  return [
    { action: "*", resource: "*", effect: "ask" },
    { action: "read", resource: "*", effect: "allow" },
    { action: "read", resource: "*.env", effect: "ask" },
    { action: "read", resource: "*.env.*", effect: "ask" },
    { action: "read", resource: "*.env.example", effect: "allow" },
    { action: "glob", resource: "*", effect: "allow" },
    { action: "grep", resource: "*", effect: "allow" },
    { action: "question", resource: "*", effect: "allow" },
    { action: "skill", resource: "*", effect: "deny" },
    { action: "skill", resource: "egm-*", effect: "allow" },
    { action: "subagent", resource: "*", effect: "deny" },
    ...reviewerIDs.map((agentID) => ({
      action: "subagent",
      resource: agentID,
      effect: "allow",
    })),
    { action: "external_directory", resource: "*", effect: "ask" },
    { action: "external_directory", resource: `${BUNDLE}/*`, effect: "allow" },
  ]
}

function reviewerSystem(personaPath) {
  return (
    CONTEXT +
    `Read ${personaPath} before the target and supplied standards. ` +
    "Return findings to the caller. Do not write reports or delegate. " +
    "You run in a fresh child session with no parent conversation: do not try " +
    "to continue it, and do not call the subagent tool. " +
    "Read prior reports only when explicitly supplied and required by the " +
    "canonical stage. Do not retrieve unsolicited history, memory, or earlier " +
    "reviewer findings. Report inaccessible required files as an incomplete review."
  )
}

function orchestratorSystem(reviewerIDs) {
  return (
    CONTEXT +
    `Follow the canonical skill. Dispatch reviewers directly with the subagent tool and one of these agent IDs: ${reviewerIDs.join(", ")}. ` +
    "Pass description plus a complete prompt: the task, absolute resource paths, the target, the standards, and the selected reading list. " +
    "Never pass conversation history, private reasoning, or memory. " +
    "Start a new child for every independent review and never continue a finished reviewer by session ID. " +
    "V2 subagents always run in the background: subagent returns a session ID immediately and each reviewer's report arrives later as a subagent message. " +
    "After dispatch, do not do the reviewers' work and do not end the stage: wait for the report messages. " +
    "If a required report never arrives, stop and name the reviewer that is missing. " +
    "Never simulate a Goldfish reviewer in your own context. " +
    "When running brainstorm before draft, complete all seven brainstorm reviewers and synthesize their findings into concepts_brief.md before drafting. " +
    "In review, write each completed stage report before starting the next stage. " +
    "Before Step 8, verify zoom_out_report.md exists in the artifact directory and pass its absolute path to the reviewer; stop if it is missing. " +
    "Write reports yourself with the edit permission and preserve every human approval gate; ask with the question tool and wait for the answer."
  )
}

export default {
  id: "egm",

  async setup(ctx) {
    const personas = REVIEWERS.map(([file, id]) => ({
      id,
      path: path.join(BUNDLE, "agents", `${file}.md`),
      ...persona(file),
    }))
    const reviewerIDs = personas.map((item) => item.id)
    const skills = SKILLS.map((id) => {
      const skillPath = path.join(BUNDLE, "skills", id, "SKILL.md")
      const { header, body } = splitFrontmatter(readFileSync(skillPath, "utf8"))
      return {
        id,
        path: skillPath,
        description: headerValue(header, "description"),
        content: body,
      }
    })

    // `update` is an upsert in Agent.Service: a missing ID starts from
    // Agent.Info.default, so this both creates and corrects the definitions.
    await ctx.agent.transform((editor) => {
      for (const item of personas) {
        editor.update(item.id, (agent) => {
          agent.mode = "subagent"
          agent.description = item.description || `EGM reviewer ${item.id}`
          agent.color = "#E86E00"
          agent.system = reviewerSystem(item.path)
          agent.permissions.push(...reviewerPermissions())
        })
      }
      editor.update("egm", (agent) => {
        agent.mode = "primary"
        agent.description = "EGM orchestrator (OpenCode plugin, experimental)"
        agent.color = "#1B6EF3"
        agent.system = orchestratorSystem(reviewerIDs)
        agent.permissions.push(...orchestratorPermissions(reviewerIDs))
      })
    })

    await ctx.command.transform((editor) => {
      for (const skill of skills) {
        editor.add({
          name: skill.id,
          description: `Run ${skill.id} (experimental)`,
          execute: async ({ sessionID, prompt, delivery }) => {
            await ctx.session.switchAgent({ sessionID, agent: "egm" })
            await ctx.session.prompt({
              sessionID,
              delivery,
              text:
                `${CONTEXT}Read and execute ${skill.path}.\n` +
                `User request: ${prompt.text}`,
            })
          },
        })
      }
    })

    // `autoinvoke: false` mirrors the canonical `disable-model-invocation`.
    // Commands load each skill by path; the skill tool can still resolve them.
    await ctx.skill.transform((editor) => {
      for (const skill of skills) {
        editor.add({
          id: skill.id,
          name: skill.id,
          description: skill.description,
          path: skill.path,
          content: skill.content,
          autoinvoke: false,
        })
      }
    })
  },
}
