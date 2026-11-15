# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Build the OpenCode-only EGM plugin bundle.

The plugin is a native OpenCode V2 plugin. It registers agents, commands, and
skills through plugin transforms, so the installed result contains no agent,
command, or skill files for OpenCode to discover.

`build()` copies the canonical skills, reviewer personas, and resources, then
rewrites every harness-specific instruction to OpenCode. It fails when a
rewrite no longer matches or when a non-OpenCode harness name survives, so an
upstream change cannot silently ship another harness's instructions.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent / "canonical"
HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
DEFAULT_OUT = HERE / "dist" / "egm"

REVIEWER_FILES = (
    "codebase_details",
    "comprehension",
    "design_critic",
    "implementation_readiness",
    "inventive_catalyst",
    "structural",
    "style",
    "zoom_out",
)
SKILLS = (
    "egm-bootstrap",
    "egm-brainstorm",
    "egm-draft",
    "egm-drift-report",
    "egm-resolve",
    "egm-review",
    "egm-review-loop",
)

# A bundle that still names another harness is a build failure, not a warning.
FORBIDDEN = re.compile(
    r"claude|codex|antigravity|chatgpt|cowork|harness|invoke_subagent|"
    r"spawn_agent|subagent_type|ask_question|plain chat|CLAUDE_PLUGIN_ROOT",
    re.IGNORECASE,
)

PREAMBLE = re.compile(
    r"^When running in Codex or ChatGPT Work, first read "
    r"\[Codex integration\]\(\.\./\.\./docs/codex\.md\)\.\n"
    r"In Claude Code or Cowork, read "
    r"`\$\{CLAUDE_PLUGIN_ROOT\}/docs/claude\.md` first\.\n\n",
    re.MULTILINE,
)

DELEGATION = re.compile(r"^A Goldfish runs in a fresh context.*?(?=\n\n)", re.M | re.S)

OPENCODE_DELEGATION = """\
A Goldfish runs in a fresh context with no conversation history. Spawn each
subagent with OpenCode's `subagent` tool, using the agent ID from the persona
file's frontmatter `name` (for example `egm-zoom-out`) as the `agent` value.
Every child runs in the background: the call returns a session ID immediately
and the report arrives later as a `<subagent>` message. Pass the prompt
verbatim. Start a new child for every independent review and never continue a
finished reviewer by session ID. If a required report never arrives, stop and
name the reviewer; a review in the same context is not a Goldfish review."""

OPENCODE_SCOUT_DELEGATION = """\
Bootstrap runs entirely in this context. OpenCode cannot nest subagents, so
read the code yourself: do not spawn a subagent for discovery. Pass complete
instructions to any reviewer you dispatch, and start a new child for every
independent review. Never continue a finished reviewer by session ID."""

ARTIFACT = re.compile(r"your harness's\s+artifact directory, if it has one", re.I)
ARTIFACT_REPLACEMENT = "the EGM artifact directory"

# After the artifact phrase is gone, every remaining parenthetical that names a
# harness is an interactive question-tool clause.
PAREN_HARNESS = re.compile(r"\((?:[^()]|\([^()]*\))*harness[^()]*\)", re.I)

SKILL_PICKER = re.compile(
    r"\s+in Claude\s+Code and agy\s+CLI, or the skill\s+picker in Codex", re.I
)
CODEX_ONLY = re.compile(r"\s+in Codex(?=[),.])", re.I)
COMMAND_PREFIX = re.compile(r"/egm:egm-")
QUESTION_TOOL = re.compile(r"`ask_question`")
PLAIN_CHAT = re.compile(r",\s+or\s+plain chat(?=\))")

BOOTSTRAP_PARALLEL = re.compile(
    r"2\.  \*\*Unbounded Parallel Subagent Swarm Strategy \(Directory Count > 5\)\*\*:"
    r".*?(?=### Step 4:)",
    re.S,
)
BOOTSTRAP_PARALLEL_REPLACEMENT = """\
2.  **Sequential Execution Strategy (Directory Count > 5)**:

    OpenCode cannot nest subagents (`experimental.subagent_depth` defaults to
    1), so nested subagents cannot spawn their own scouts or resolve their own
    subtree. Process the pruned tree sequentially, deepest leaves first, in
    this context. Follow Step 4 for every directory and write each contract
    before moving to the next. Step 5 still compiles the root blueprint from
    the documents this pass wrote.

"""

BOOTSTRAP_SCOUT_REGISTRATION = re.compile(
    r"1\.  \*\*Scout Registration\*\*: Use a read-only `goldfish-explorer` scout\."
    r".*?(?=\n2\.  \*\*Post-Order Traversal\*\*)",
    re.S,
)
BOOTSTRAP_SCOUT_REPLACEMENT = """\
1.  **Scout Method**: A skill cannot define an ad-hoc subagent, so run the
    read-only scout inline for each directory. Do not spawn a subagent for the
    scout. Apply this explorer contract while you read:

    *   **Interface**: public symbols the directory exposes.
    *   **Invariants**: explicit checks, guards, or stated constraints.
    *   **Side Effects**: writes, network calls, process or storage mutation.

    Cite `[file:symbol_or_flag]` for every entry. Never infer RPC methods,
    routes, status enums, or invariants from names alone. Use `["None"]` when
    the code contains no explicit invariant or side effect.
"""

BOOTSTRAP_SCAN = re.compile(
    r"\*   \*\*Scout Spawning & Constraints\*\*: Spawn `goldfish-explorer` for `D`\."
)
BOOTSTRAP_SCAN_REPLACEMENT = "*   **Scout Scan & Constraints**: Read `D` inline."

BOOTSTRAP_SCAN_REQUIREMENT = re.compile(
    r"\*   \*Scout Scan Requirement\*: Whether `target_filename` exists or not,\n"
    r"\s+\*\*always scan\*\* the source code using the `goldfish-explorer` scout\n"
    r"\s+for `D` to compile the true code symbol boundary\."
)
BOOTSTRAP_SCAN_REQUIREMENT_REPLACEMENT = (
    "*   *Scout Scan Requirement*: Whether `target_filename` exists or not,\n"
    "            **always scan** the source code for `D` inline to compile the\n"
    "            true code symbol boundary."
)

BOOTSTRAP_CHUNK = re.compile(
    r"small files share a chunk\), spawn one `goldfish-explorer` per\n"
    r"\s+chunk in parallel, and merge their JSON\."
)
BOOTSTRAP_CHUNK_REPLACEMENT = (
    "small files share a chunk), read one chunk at a time, and merge the\n"
    "            extracted JSON."
)

BOOTSTRAP_SCOUT_FAILURE = re.compile(
    r"\*   \*Child Fault Tolerance\*: If the scout fails or times out, log a"
)
BOOTSTRAP_SCOUT_FAILURE_REPLACEMENT = (
    "*   *Child Fault Tolerance*: If the inline scan fails or is cut short, log a"
)

BOOTSTRAP_PARENT_CONTEXT = re.compile(
    r"\*   Pass these child symbol blocks as prompt context when invoking `P`'s\n"
    r"\s+explorer scout\."
)
BOOTSTRAP_PARENT_CONTEXT_REPLACEMENT = (
    "*   Use these child symbol blocks as context when compiling `P`'s contract."
)

BOOTSTRAP_WORKER_PAYLOAD = re.compile(
    r"1\.  \*\*Receive Worker Payloads\*\*: Collect the JSON `subtree_index` payloads\n"
    r"\s+returned by all parallel Sub-Orchestrators\.\n\n"
    r"\s+\*   \*\*Root Fault Tolerance\*\*: If a parallel worker fails or times out, log a\n"
    r"\s+warning, insert a placeholder warning link \(`\[Subtree Root\]\n"
    r"\s+\(Documentation failed / Subagent execution timeout\)`\) in the root\n"
    r"\s+Blueprint's subdirectory index, and complete the remaining compilation\."
)
BOOTSTRAP_WORKER_PAYLOAD_REPLACEMENT = """\
1.  **Collect Results**: Sequential execution has no parallel results. Compile
    from the contracts written in Step 4.

    *   **Root Fault Tolerance**: If a contract is missing or incomplete, log a
        warning, insert a placeholder warning link (`[Subtree Root]
        (Documentation failed / Incomplete scan)`) in the root Blueprint's
        subdirectory index, and complete the remaining compilation."""

BOOTSTRAP_WORKER_HEADING = re.compile(r"### Step 4: Sub-Orchestrator Worker Flow")
BOOTSTRAP_WORKER_HEADING_REPLACEMENT = "### Step 4: Directory Contract Flow"

BOOTSTRAP_IGNORE = re.compile(r"`\.git`, `\.antigravity`, `node_modules`")
BOOTSTRAP_IGNORE_REPLACEMENT = "`.git`, `.opencode`, `node_modules`"

BOOTSTRAP_STEP4_REF = re.compile(r"Step 4: Sub-Orchestrator Worker Flow")
BOOTSTRAP_STEP4_REF_REPLACEMENT = "Step 4: Directory Contract Flow"

BOOTSTRAP_WORKER_SUMMARIES = re.compile(
    r"compiled summaries\n\s+returned by the workers"
)
BOOTSTRAP_WORKER_SUMMARIES_REPLACEMENT = "compiled summaries from Step 4"

BOOTSTRAP_SCAN_BOUND = re.compile(r"Bound each scout call to")
BOOTSTRAP_SCAN_BOUND_REPLACEMENT = "Bound each scan to"

BOOTSTRAP_INPUTS = re.compile(
    r"\*   \*\*`is_worker`\*\*: Internal parameter\. `true` if executing as a worker\n"
    r"\s+Sub-Orchestrator \(Optional, default: `false`\)\.\n"
    r"\*   \*\*`sub_tree_root`\*\*: Internal parameter\. The root path of the assigned\n"
    r"\s+subtree partition \(Optional\)\.\n"
)
BOOTSTRAP_INPUTS_REPLACEMENT = ""

BOOTSTRAP_WORKER_STATE = re.compile(
    r"Each worker keeps its status, checkpoint,\n\s+and log files in its own directory"
)
BOOTSTRAP_WORKER_STATE_REPLACEMENT = (
    "Keep your status, checkpoint,\n    and log files in your own directory"
)

BOOTSTRAP_SUBAGENT_CONSTRAINT = re.compile(
    r"5\.  \*\*Subagent Delegation\*\*: Spawn sub-orchestrator workers in parallel\."
)
BOOTSTRAP_SUBAGENT_CONSTRAINT_REPLACEMENT = (
    "5.  **No Nested Delegation**: OpenCode cannot nest subagents, so process the\n"
    "    tree in this context."
)

BOOTSTRAP_SAFETY_GATE = re.compile(
    r"full-tree execution\n\s+or unbounded subagent spawning\."
)
BOOTSTRAP_SAFETY_GATE_REPLACEMENT = "full-tree execution."

BOOTSTRAP_WAIT = re.compile(r"response before continuing or spawning any workers\)\.")
BOOTSTRAP_WAIT_REPLACEMENT = "response before continuing)."

BOOTSTRAP_GATE_TITLE = re.compile(
    r"2\.  \*\*Safety Gate & Unbounded Spawning Approval \(CRITICAL\)\*\*"
)
BOOTSTRAP_GATE_TITLE_REPLACEMENT = "2.  **Large Scope Approval (CRITICAL)**"

BOOTSTRAP_STEP1 = re.compile(
    r"### Step 1: Startup Branching Control\n\n"
    r"1\.  Check the `is_worker` input parameter\.\n"
    r"2\.  If `is_worker` is `true`, jump directly to \*\*Step 4: Sub-Orchestrator Worker\n"
    r"\s+Flow\*\* to process the assigned `sub_tree_root`\.\n"
    r"3\.  If `is_worker` is `false` or unset, proceed as the Root Orchestrator to\n"
    r"\s+\*\*Step 2: Incremental Scoping & Safety Gate\*\*\."
)
BOOTSTRAP_STEP1_REPLACEMENT = """\
### Step 1: Confirm Scope

Proceed to **Step 2: Incremental Scoping & Safety Gate** for the whole `path`."""

BOOTSTRAP_SCOPE_TITLE = re.compile(
    r"### Step 2: Incremental Scoping & Safety Gate \(Root Orchestrator\)"
)
BOOTSTRAP_SCOPE_TITLE_REPLACEMENT = "### Step 2: Incremental Scoping & Safety Gate"

BOOTSTRAP_STRATEGY_TITLE = re.compile(
    r"### Step 3: Execution Strategy Selection \(Root Orchestrator\)"
)
BOOTSTRAP_STRATEGY_TITLE_REPLACEMENT = "### Step 3: Execution Strategy Selection"

BOOTSTRAP_DIRECT = re.compile(
    r"\*   Jump to \*\*Step 4: Directory Contract Flow\*\* \(treating the Root\n"
    r"\s+Orchestrator as the worker for the entire `path`\), and then proceed to\n"
    r"\s+\*\*Step 5: Root Compilation & Termination\*\*\."
)
BOOTSTRAP_DIRECT_REPLACEMENT = (
    "*   Jump to **Step 4: Directory Contract Flow**, then proceed to\n"
    "        **Step 5: Root Compilation & Termination**."
)

BOOTSTRAP_POST_ORDER = re.compile(r"Walk the assigned `sub_tree_root` \(or `path`\) in")
BOOTSTRAP_POST_ORDER_REPLACEMENT = "Walk `path` in"

BOOTSTRAP_REPORTING = re.compile(
    r"3\.  \*\*Worker Reporting\*\*: Once the assigned subtree is fully traversed, compile"
)
BOOTSTRAP_REPORTING_REPLACEMENT = (
    "3.  **Contract Index**: Once the tree is fully traversed, compile"
)

BOOTSTRAP_STEP4_RETURN = re.compile(
    r"4\.  If `is_worker` is `true`, read the \[Worker Return Interface Schema\]"
    r"\(references/worker-return\.schema\.json\)\n"
    r"\s+relative to this skill directory, then return a matching JSON payload to\n"
    r"\s+the Root Orchestrator and terminate\. If\n"
    r"\s+`is_worker` is `false` \(sequential mode\), proceed directly to \*\*Step 5: Root\n"
    r"\s+Compilation & Termination\*\*\."
)
BOOTSTRAP_STEP4_RETURN_REPLACEMENT = (
    "4.  Proceed directly to **Step 5: Root Compilation & Termination**."
)

BOOTSTRAP_WORKER_FAILURE = re.compile(
    r"\(Worker failures leaving partial files are handled as an"
)
BOOTSTRAP_WORKER_FAILURE_REPLACEMENT = "(Incomplete files are handled as an"

BOOTSTRAP_INTERMEDIATE = re.compile(
    r"between the root `path` and the partitioned subtree\n\s+roots\."
)
BOOTSTRAP_INTERMEDIATE_REPLACEMENT = (
    "between the root `path` and the documented directories."
)

BOOTSTRAP_ROOT_SCAN = re.compile(r"spawn a `goldfish-explorer` scout for `path`")
BOOTSTRAP_ROOT_SCAN_REPLACEMENT = "scan `path` inline"

BOOTSTRAP_CHILD_PAYLOADS = re.compile(r"child `subtree_index` payloads")
BOOTSTRAP_CHILD_PAYLOADS_REPLACEMENT = "child contracts"

BOOTSTRAP_VERIFY_INDEX = re.compile(
    r"contract files in the\n\s+`subtree_index` \(including all child"
)
BOOTSTRAP_VERIFY_INDEX_REPLACEMENT = "contract files\n    (including all child"

BOOTSTRAP_SCOUT_EXTRACTION = re.compile(r"from the scout extraction")
BOOTSTRAP_SCOUT_EXTRACTION_REPLACEMENT = "from your inline scan"

EXECUTION_SCRATCH = re.compile(r" or, if your harness has none,")
EXECUTION_SCRATCH_REPLACEMENT = ","


def _apply(text: str, pattern: re.Pattern[str], replacement: str, label: str) -> str:
    updated, count = pattern.subn(replacement, text)
    if count == 0:
        raise ValueError(f"Rewrite no longer matches: {label}")
    return updated


def rewrite_skill(text: str, skill: str) -> str:
    text = _apply(text, PREAMBLE, "", f"{skill}: harness preamble")
    if skill in {"egm-bootstrap", "egm-brainstorm", "egm-review", "egm-review-loop"}:
        replacement = (
            OPENCODE_SCOUT_DELEGATION if skill == "egm-bootstrap" else OPENCODE_DELEGATION
        )
        text = _apply(text, DELEGATION, replacement, f"{skill}: delegation")
    text = ARTIFACT.sub(ARTIFACT_REPLACEMENT, text)
    text = PAREN_HARNESS.sub("(using the `question` tool)", text)
    text = SKILL_PICKER.sub("", text)
    text = CODEX_ONLY.sub("", text)
    text = COMMAND_PREFIX.sub("/egm-", text)
    text = QUESTION_TOOL.sub("`question`", text)
    text = PLAIN_CHAT.sub("", text)

    if skill == "egm-bootstrap":
        text = _apply(text, BOOTSTRAP_INPUTS, BOOTSTRAP_INPUTS_REPLACEMENT, "bootstrap: worker inputs")
        text = _apply(
            text, BOOTSTRAP_WORKER_STATE, BOOTSTRAP_WORKER_STATE_REPLACEMENT,
            "bootstrap: worker state",
        )
        text = _apply(
            text, BOOTSTRAP_SUBAGENT_CONSTRAINT, BOOTSTRAP_SUBAGENT_CONSTRAINT_REPLACEMENT,
            "bootstrap: subagent constraint",
        )
        text = _apply(
            text, BOOTSTRAP_SAFETY_GATE, BOOTSTRAP_SAFETY_GATE_REPLACEMENT,
            "bootstrap: safety gate",
        )
        text = _apply(text, BOOTSTRAP_WAIT, BOOTSTRAP_WAIT_REPLACEMENT, "bootstrap: wait")
        text = _apply(
            text, BOOTSTRAP_GATE_TITLE, BOOTSTRAP_GATE_TITLE_REPLACEMENT,
            "bootstrap: gate title",
        )
        text = _apply(text, BOOTSTRAP_STEP1, BOOTSTRAP_STEP1_REPLACEMENT, "bootstrap: step 1")
        text = _apply(
            text, BOOTSTRAP_SCOPE_TITLE, BOOTSTRAP_SCOPE_TITLE_REPLACEMENT,
            "bootstrap: scope title",
        )
        text = _apply(
            text, BOOTSTRAP_STRATEGY_TITLE, BOOTSTRAP_STRATEGY_TITLE_REPLACEMENT,
            "bootstrap: strategy title",
        )
        text = _apply(text, BOOTSTRAP_PARALLEL, BOOTSTRAP_PARALLEL_REPLACEMENT, "bootstrap: strategy")
        text = _apply(text, BOOTSTRAP_SCOUT_REGISTRATION, BOOTSTRAP_SCOUT_REPLACEMENT, "bootstrap: scout")
        text = _apply(text, BOOTSTRAP_SCAN, BOOTSTRAP_SCAN_REPLACEMENT, "bootstrap: scan")
        text = _apply(
            text, BOOTSTRAP_SCAN_REQUIREMENT, BOOTSTRAP_SCAN_REQUIREMENT_REPLACEMENT,
            "bootstrap: scan requirement",
        )
        text = _apply(text, BOOTSTRAP_CHUNK, BOOTSTRAP_CHUNK_REPLACEMENT, "bootstrap: chunk")
        text = _apply(
            text, BOOTSTRAP_SCOUT_FAILURE, BOOTSTRAP_SCOUT_FAILURE_REPLACEMENT,
            "bootstrap: fault tolerance",
        )
        text = _apply(
            text, BOOTSTRAP_PARENT_CONTEXT, BOOTSTRAP_PARENT_CONTEXT_REPLACEMENT,
            "bootstrap: parent context",
        )
        text = _apply(
            text, BOOTSTRAP_WORKER_PAYLOAD, BOOTSTRAP_WORKER_PAYLOAD_REPLACEMENT,
            "bootstrap: payloads",
        )
        text = _apply(
            text, BOOTSTRAP_WORKER_HEADING, BOOTSTRAP_WORKER_HEADING_REPLACEMENT,
            "bootstrap: heading",
        )
        text = _apply(
            text, BOOTSTRAP_IGNORE, BOOTSTRAP_IGNORE_REPLACEMENT,
            "bootstrap: ignore list",
        )
        text = _apply(
            text, BOOTSTRAP_STEP4_REF, BOOTSTRAP_STEP4_REF_REPLACEMENT,
            "bootstrap: step 4 reference",
        )
        text = _apply(text, BOOTSTRAP_DIRECT, BOOTSTRAP_DIRECT_REPLACEMENT, "bootstrap: direct")
        text = _apply(
            text, BOOTSTRAP_POST_ORDER, BOOTSTRAP_POST_ORDER_REPLACEMENT,
            "bootstrap: post-order",
        )
        text = _apply(
            text, BOOTSTRAP_REPORTING, BOOTSTRAP_REPORTING_REPLACEMENT,
            "bootstrap: reporting",
        )
        text = _apply(
            text, BOOTSTRAP_STEP4_RETURN, BOOTSTRAP_STEP4_RETURN_REPLACEMENT,
            "bootstrap: step 4 return",
        )
        text = _apply(
            text, BOOTSTRAP_WORKER_FAILURE, BOOTSTRAP_WORKER_FAILURE_REPLACEMENT,
            "bootstrap: failure note",
        )
        text = _apply(
            text, BOOTSTRAP_INTERMEDIATE, BOOTSTRAP_INTERMEDIATE_REPLACEMENT,
            "bootstrap: intermediate",
        )
        text = _apply(
            text, BOOTSTRAP_ROOT_SCAN, BOOTSTRAP_ROOT_SCAN_REPLACEMENT,
            "bootstrap: root scan",
        )
        text = _apply(
            text, BOOTSTRAP_CHILD_PAYLOADS, BOOTSTRAP_CHILD_PAYLOADS_REPLACEMENT,
            "bootstrap: child payloads",
        )
        text = _apply(
            text, BOOTSTRAP_VERIFY_INDEX, BOOTSTRAP_VERIFY_INDEX_REPLACEMENT,
            "bootstrap: verify index",
        )
        text = _apply(
            text, BOOTSTRAP_SCOUT_EXTRACTION, BOOTSTRAP_SCOUT_EXTRACTION_REPLACEMENT,
            "bootstrap: scout extraction",
        )
        text = _apply(
            text, BOOTSTRAP_WORKER_SUMMARIES, BOOTSTRAP_WORKER_SUMMARIES_REPLACEMENT,
            "bootstrap: worker summaries",
        )
        text = _apply(
            text, BOOTSTRAP_SCAN_BOUND, BOOTSTRAP_SCAN_BOUND_REPLACEMENT,
            "bootstrap: scan bound",
        )

    leftover = FORBIDDEN.search(text)
    if leftover:
        start = max(0, leftover.start() - 60)
        raise ValueError(
            f"{skill}: non-OpenCode text remains near {text[start:leftover.end() + 60]!r}"
        )
    return text


def rewrite_resource(text: str) -> str:
    text, _ = EXECUTION_SCRATCH.subn(EXECUTION_SCRATCH_REPLACEMENT, text)
    leftover = FORBIDDEN.search(text)
    if leftover:
        raise ValueError(f"resource: non-OpenCode text remains near {text!r}")
    return text


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _validate_bundle(bundle: Path) -> None:
    """Reject any non-OpenCode instruction that survived the rewrite."""
    for path in sorted(bundle.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".json", ".yaml", ".yml", ".txt"}:
            continue
        match = FORBIDDEN.search(path.read_text(encoding="utf-8"))
        if match:
            raise ValueError(
                f"{path.relative_to(bundle)}: non-OpenCode text survives at {match.group(0)!r}"
            )
    for skill in SKILLS:
        if not (bundle / "skills" / skill / "SKILL.md").is_file():
            raise ValueError(f"Missing skill: {skill}")


def _manifest(destination: Path) -> None:
    plugin = json.loads((SRC / "plugin.json").read_text(encoding="utf-8"))
    payload = {
        **plugin,
        "interface": "opencode-plugin",
        "tested_host": "2.2.7",
        "status": "experimental",
        "targets": ["opencode"],
        "sha256": {
            path.relative_to(destination).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(destination.rglob("*"))
            if path.is_file()
        },
    }
    _write(
        destination / "manifest.json",
        json.dumps(payload, indent=2) + "\n",
    )


def build(destination: Path = DEFAULT_OUT) -> Path:
    """Generate a loadable plugin directory and its OpenCode-only bundle."""
    destination = destination.resolve()
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    bundle = destination / "bundle"

    shutil.copy2(SRC / "index.js", destination / "index.js")
    _write(
        destination / "package.json",
        json.dumps(
            {
                "name": "opencode-egm",
                "version": "0.1.0",
                "private": True,
                "type": "module",
                "exports": {".": "./index.js"},
            },
            indent=2,
        )
        + "\n",
    )

    for skill in SKILLS:
        source = ROOT / "skills" / skill
        target = bundle / "skills" / skill
        target.mkdir(parents=True)
        _write(
            target / "SKILL.md",
            rewrite_skill((source / "SKILL.md").read_text(encoding="utf-8"), skill),
        )
        references = source / "references"
        if references.is_dir():
            # Bootstrap runs sequentially, so the parallel worker contract is unused.
            shutil.copytree(
                references,
                target / "references",
                ignore=shutil.ignore_patterns("worker-return.schema.json"),
            )

    (bundle / "agents").mkdir(parents=True)
    for reviewer in REVIEWER_FILES:
        shutil.copy2(
            ROOT / "agents" / f"{reviewer}.md",
            bundle / "agents" / f"{reviewer}.md",
        )

    for resource in sorted((ROOT / "resources").rglob("*")):
        if not resource.is_file():
            continue
        target = bundle / "resources" / resource.relative_to(ROOT / "resources")
        target.parent.mkdir(parents=True, exist_ok=True)
        if resource.suffix == ".md":
            _write(target, rewrite_resource(resource.read_text(encoding="utf-8")))
        else:
            shutil.copy2(resource, target)

    _write(
        bundle / "docs" / "opencode-plugin.md",
        (SRC / "opencode-plugin.md").read_text(encoding="utf-8"),
    )

    _validate_bundle(bundle)
    _manifest(destination)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "destination", nargs="?", type=Path, default=DEFAULT_OUT,
        help="Output plugin directory (recreated on each build)",
    )
    arguments = parser.parse_args()
    print(build(arguments.destination))
