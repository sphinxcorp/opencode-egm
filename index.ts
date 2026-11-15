// Copyright 2026 Google LLC.
// SPDX-License-Identifier: Apache-2.0

/**
 * Native OpenCode plugin for the Elephant & Goldfish Model (EGM).
 *
 * The bundle/ directory is the source of truth: every Markdown persona under
 * bundle/agents becomes a reviewer subagent, and every bundle/skills/<id>
 * directory with a SKILL.md becomes a slash command and skill.
 */

import { readFileSync, readdirSync } from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { Plugin } from "@opencode/plugin"

const PACKAGE_ROOT = path.dirname(fileURLToPath(import.meta.url))
const BUNDLE = path.join(PACKAGE_ROOT, "bundle")
const GUIDE = path.join(PACKAGE_ROOT, "README.md")

interface Frontmatter {
  header: string
  body: string
}

function splitFrontmatter(text: string): Frontmatter {
  const match = /^---\n([\s\S]*?)\n---\n?/.exec(text)
  if (!match) return { header: "", body: text }
  return { header: match[1], body: text.slice(match[0].length) }
}

function headerValue(header: string, key: string): string {
  const match = new RegExp(`^${key}:\\s*(.+)$`, "m").exec(header)
  return match ? match[1].trim().replace(/^["']|["']$/g, "") : ""
}

interface Persona {
  id: string
  file: string
  path: string
  description: string
  body: string
}

function loadPersonas(): Persona[] {
  const dir = path.join(BUNDLE, "agents")
  return readdirSync(dir)
    .filter((name) => name.endsWith(".md"))
    .sort()
    .map((name) => {
      const file = name.replace(/\.md$/, "")
      const fullPath = path.join(dir, name)
      const text = readFileSync(fullPath, "utf8")
      const { header, body } = splitFrontmatter(text)
      const id = headerValue(header, "name") || `egm-${file.replace(/_/g, "-")}`
      return {
        id,
        file,
        path: fullPath,
        description: headerValue(header, "description") || `EGM reviewer ${id}`,
        body,
      }
    })
}

interface Skill {
  id: string
  path: string
  description: string
  content: string
}

function loadSkills(): Skill[] {
  const dir = path.join(BUNDLE, "skills")
  return readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort()
    .map((id) => {
      const skillPath = path.join(dir, id, "SKILL.md")
      const text = readFileSync(skillPath, "utf8")
      const { header, body } = splitFrontmatter(text)
      return {
        id: headerValue(header, "name") || id,
        path: skillPath,
        description: headerValue(header, "description") || id,
        content: body,
      }
    })
}

const CONTEXT =
  `Read ${GUIDE} first. EGM bundle root: ${BUNDLE}. ` +
  "Resolve agents/, resources/, and docs/ against this root. " +
  "Resolve references/ against the canonical skill directory. " +
  "Resolve user files and outputs against the project working directory. "

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

function orchestratorPermissions(reviewerIDs: string[]) {
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

function reviewerSystem(personaPath: string) {
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

function orchestratorSystem(reviewerIDs: string[]) {
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

export default Plugin.define({
  id: "egm",

  async setup(ctx: any) {
    const personas = loadPersonas()
    const reviewerIDs = personas.map((item) => item.id)
    const skills = loadSkills()

    await ctx.agent.transform((editor: any) => {
      for (const item of personas) {
        editor.update(item.id, (agent: any) => {
          agent.mode = "subagent"
          agent.description = item.description
          agent.color = "#E86E00"
          agent.system = reviewerSystem(item.path)
          agent.permissions.push(...reviewerPermissions())
        })
      }
      editor.update("egm", (agent: any) => {
        agent.mode = "primary"
        agent.description = "EGM orchestrator (OpenCode plugin, experimental)"
        agent.color = "#1B6EF3"
        agent.system = orchestratorSystem(reviewerIDs)
        agent.permissions.push(...orchestratorPermissions(reviewerIDs))
      })
    })

    await ctx.command.transform((editor: any) => {
      for (const skill of skills) {
        editor.add({
          name: skill.id,
          description: `Run ${skill.id} (experimental)`,
          execute: async ({ sessionID, prompt, delivery }: any) => {
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

    await ctx.skill.transform((editor: any) => {
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
})