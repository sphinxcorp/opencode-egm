import { readFileSync, existsSync, readdirSync, statSync } from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
const BUNDLE = path.join(ROOT, "bundle")

const FORBIDDEN = /claude|codex|antigravity|chatgpt|cowork|harness|invoke_subagent|spawn_agent|subagent_type|ask_question|plain chat|CLAUDE_PLUGIN_ROOT/i

const failures = []
function fail(message) { failures.push(message) }

// 1. Forbidden terms in bundle text files.
for (const file of walk(BUNDLE)) {
  if (!/\.(md|json|yaml|yml|txt|js|ts)$/.test(file)) continue
  const text = readFileSync(file, "utf8")
  const match = FORBIDDEN.exec(text)
  if (match) fail(`${path.relative(ROOT, file)}: forbidden term ${JSON.stringify(match[0])}`)
}

// 2. Agent personas must have frontmatter names.
const agentsDir = path.join(BUNDLE, "agents")
for (const file of readdirSync(agentsDir).filter((f) => f.endsWith(".md"))) {
  const text = readFileSync(path.join(agentsDir, file), "utf8")
  if (!/^name:\s*\S+/m.test(text)) fail(`agents/${file}: missing frontmatter name`)
}

// 3. Skills must have directories with SKILL.md and frontmatter names.
const skillsDir = path.join(BUNDLE, "skills")
for (const entry of readdirSync(skillsDir, { withFileTypes: true })) {
  if (!entry.isDirectory()) continue
  const skillMd = path.join(skillsDir, entry.name, "SKILL.md")
  if (!existsSync(skillMd)) {
    fail(`skills/${entry.name}: missing SKILL.md`)
    continue
  }
  const text = readFileSync(skillMd, "utf8")
  if (!/^name:\s*\S+/m.test(text)) fail(`skills/${entry.name}/SKILL.md: missing frontmatter name`)

  // 4. Skill references must resolve.
  for (const ref of text.matchAll(/references\/[A-Za-z0-9._/-]+/g)) {
    const relative = ref[0].replace(/^\//, "")
    const full = path.join(skillsDir, entry.name, relative)
    if (!existsSync(full)) fail(`skills/${entry.name}/SKILL.md: missing reference ${relative}`)
  }
}

if (failures.length) {
  console.error("Bundle validation failed:")
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}
console.log("Bundle validation passed.")

function walk(dir) {
  const out = []
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) out.push(...walk(full))
    else out.push(full)
  }
  return out
}