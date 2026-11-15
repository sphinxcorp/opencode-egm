---
name: egm-bootstrap
license: Apache-2.0
disable-model-invocation: true
description: Bootstrap directory README.md files across a repository subtree.
---

# EGM Peanuts and Hay Bootstrap (`egm-bootstrap`)

## Overview

This skill automates the creation, correction, formatting, and correctness
verification of Elephant-and-Goldfish Model (EGM) compliant `README.md` files
across a directory tree. It establishes clear architectural contracts
(interfaces, invariants, and side effects) for both human developers and AI
assistants.

*   **Peanuts**: Leaf-level Component Package READMEs containing specific file
    contracts.
*   **Hay**: Parent-level Repository Blueprints that roll up child interface
    contracts into high-altitude indexes.

## Delegation

Bootstrap runs entirely in this context. OpenCode cannot nest subagents, so
read the code yourself: do not spawn a subagent for discovery. Pass complete
instructions to any reviewer you dispatch, and start a new child for every
independent review. Never continue a finished reviewer by session ID.

## Inputs

*   **`path`**: The target root directory path to bootstrap (Required).
*   **`target_filename`**: Target contract filename to generate or update
    (Optional, default: `"README.md"`). Supports alternate blueprint filenames
    such as `"EGM.md"` when pre-existing human-maintained READMEs must not be
    modified.

## Execution Constraints (CRITICAL)

1.  **No Code Generation**: You are strictly limited to documentation. Do not
    write or refactor any functional source code.
2.  **VCS Isolation**: Do not perform any version control commits (`git commit`,
    `git add`). All filesystem changes must be written locally using standard
    file-writing tools. Tracking
    and submitting is deferred to the human user.
3.  **Temporary File Isolation**: Keep your status, checkpoint,
    and log files in your own directory outside the workspace (host scratch or
    `mktemp -d`), never a fixed, shared path. If neither exists, skip them.
4.  **Tool Usage (CRITICAL)**: Use your shell, file-reading, file-writing, and file-editing tools for directory discovery and contract/README
    generation. Adhere to clean Markdown formatting directly during generation
    (standard headers, tables, and fenced code blocks). If a project markdown
    formatter (e.g. `npx prettier --write`) is explicitly configured in the
    repository, it may optionally be invoked.
5.  **No Nested Delegation**: OpenCode cannot nest subagents, so process the
    tree in this context.
6.  **Mandatory Safety Gate (CRITICAL)**: If you discover more than 15
    subdirectories, you MUST immediately request user approval (using the `question` tool) before proceeding with full-tree execution.

---

## Workflow

### Step 0: Ecosystem & Verification Discovery

1.  Inspect the repository root for package/build manifests:
    *   Node.js / TypeScript: `package.json` -> `npm test` (or `pnpm test` / `yarn test`)
    *   Rust: `Cargo.toml` -> `cargo test`
    *   Go: `go.mod` -> `go test ./...`
    *   Python: `pyproject.toml` / `pytest.ini` / `setup.py` -> `pytest`
    *   .NET / C#: `*.sln` / `*.slnx` / `*.csproj` -> `dotnet test`
    *   C/C++ / Make: `Makefile` -> `make test`
    *   Bazel: `BUILD` / `BUILD.bazel` -> `bazel test //...`
    *   None found: `<test-command>`
2.  Record as `VerificationCommand` to populate generated README contracts.

---

### Step 1: Confirm Scope

Proceed to **Step 2: Incremental Scoping & Safety Gate** for the whole `path`.

---

### Step 2: Incremental Scoping & Safety Gate

1.  **Incremental BFS Discovery**: Map the target `path` tree level-by-level
    (BFS) using a directory queue, listing one directory level at a time. (CRITICAL: never run a recursive search such as `find` or `ls -R`.)

    *   Preserve intermediate folder nodes.
    *   Ignore symbolic links to prevent infinite recursion.
    *   Ignore hidden/system directories (`.git`, `.opencode`, `node_modules`,
        `venv`, `dist`, `build`, `third_party`).
    *   Read `.gitignore` and `.egmignore` (if present) and ignore matching glob patterns.
    *   Preserve package and build manifests (`package.json`, `Cargo.toml`,
        `go.mod`, `pyproject.toml`, `*.sln`, `*.csproj`, `Makefile`, `BUILD`) in
        the discovery map to extract verification targets later.

2.  **Large Scope Approval (CRITICAL)**: During the BFS
    loop, if the total running count of discovered directories exceeds **15**,
    immediately pause discovery and request user approval (using the `question` tool) to warn the user and request approval
    for full-tree execution:

    *   `question`: "The target directory tree contains more than 15
        subdirectories. This is a large execution scope. Do you want to proceed
        with full-tree bootstrapping?"
    *   `options`: `["Yes, proceed with full tree bootstrapping",
        "No, abort execution"]`
    *   (CRITICAL: After requesting approval, you MUST wait for the user's
        response before continuing).
    *   If the user selects abort, terminate execution immediately.

3.  **Bottom-up Post-Pruning Pass**: Once mapping is complete (and approved),
    walk the mapped tree bottom-up (leaves to root). Filter out non-code and
    test-only directories:

    *   *Source Code Files*: Files matching recognized source code, schema, and
        contract extensions:
        - Systems & Compiled: `.c`, `.cc`, `.cpp`, `.cxx`, `.h`, `.hh`, `.hpp`,
          `.rs`, `.go`, `.zig`, `.lean`, `.f`, `.f90`, `.f95`, `.f03`, `.f08`,
          `.hs`
        - Managed & Enterprise: `.java`, `.kt`, `.scala`, `.cs`, `.razor`,
          `.cshtml`, `.fs`, `.vb`
        - Scripting & Dynamic: `.py`, `.rb`, `.php`, `.lua`, `.sh`, `.bash`,
          `.ps1`, `.psm1`, `.psd1`, `.r`, `.R`, `.ex`, `.exs`
        - Web & Mobile: `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`, `.swift`,
          `.m`, `.dart`
        - Data & Schemas / IDLs: `.sql`, `.proto`, `.graphql`, `.gql`,
          `.thrift`, `.prisma`
        - Infrastructure / Declarative Code: `.tf`, `.hcl`, `.cue`
        (Excludes build manifests, lockfiles, test fixtures, documentation, and
        generic data dumps like `.csv`, `.tsv`, `.parquet`).
    *   *Test Directory Exclusion*: Exclude directories containing exclusively
        test code (e.g. named `tests`, `testing`, `testdata`, or containing only
        files matching `*_test.*`, `*Test.*`, `test_*.*`, or `*.spec.*`).
    *   *Non-Code Filtering*: Exclude any directory that contains no source code
        files AND contains no subdirectories with code. Retain empty
        intermediate folders only if they have child directories that contain
        code.

4.  Calculate the total count of pruned directories and maximum depth. Proceed
    to **Step 3: Execution Strategy Selection**.

---

### Step 3: Execution Strategy Selection

1.  **Direct Execution Strategy (Directory Count <= 5)**:

    *   If the total count of pruned directories is 5 or fewer, execute the bottom-up
        documentation directly in the current thread.
    *   Jump to **Step 4: Directory Contract Flow**, then proceed to
        **Step 5: Root Compilation & Termination**.

2.  **Sequential Execution Strategy (Directory Count > 5)**:

    OpenCode cannot nest subagents (`experimental.subagent_depth` defaults to
    1), so nested subagents cannot spawn their own scouts or resolve their own
    subtree. Process the pruned tree sequentially, deepest leaves first, in
    this context. Follow Step 4 for every directory and write each contract
    before moving to the next. Step 5 still compiles the root blueprint from
    the documents this pass wrote.

### Step 4: Directory Contract Flow

1.  **Scout Method**: A skill cannot define an ad-hoc subagent, so run the
    read-only scout inline for each directory. Do not spawn a subagent for the
    scout. Apply this explorer contract while you read:

    *   **Interface**: public symbols the directory exposes.
    *   **Invariants**: explicit checks, guards, or stated constraints.
    *   **Side Effects**: writes, network calls, process or storage mutation.

    Cite `[file:symbol_or_flag]` for every entry. Never infer RPC methods,
    routes, status enums, or invariants from names alone. Use `["None"]` when
    the code contains no explicit invariant or side effect.

2.  **Post-Order Traversal**: Walk `path` in
    post-order (deepest leaves first). For each directory `D`:

    *   **Correction & Modification Policy**: Check if `target_filename` (default:
        `README.md`) already exists in `D`.

        *   If `target_filename` exists, **do not overwrite it completely**. Instead,
            read its existing content.
        *   *Scout Scan Requirement*: Whether `target_filename` exists or not,
            **always scan** the source code for `D` inline to compile the
            true code symbol boundary.
        *   *Legacy Extraction & Correction*: If `target_filename` exists, call the
            reasoning LLM with prompt: > "Analyze the following unstructured
            documentation content. Extract all public symbol names, classes,
            interfaces, invariants, and side effects. Format your response
            strictly as a JSON object matching the following schema: {
            \"interface\": string[], \"invariants\": string[], \"side_effects\":
            string[] }." Merge these extracted symbols with the scout's code
            symbols. Use your file-editing tool (or your file-writing tool) to correct
            and update the existing contract file to be EGM compliant while preserving
            developer notes and descriptions.

    *   **Scout Scan & Constraints**: Read `D` inline.

        *   *Scout Constraints*: No per-directory or per-file byte cap; every
            non-test file in `D` is read in full. Bound each scan to
            about **1,500 lines** of source instead: list top-level definitions
            (class/func/def/route/flag lines) with your search tool, cut the
            directory's files into chunks at those boundaries (never mid-body;
            small files share a chunk), read one chunk at a time, and merge the
            extracted JSON. Give each chunk the
            file's imports and top-level definition list so it can judge
            visibility. Check build-manifest deps and `import` / `#include`
            statements before attributing an RPC service, schema, or message
            type to a local file. Read non-test files in this order:
            1.  Contracts, schemas, and build manifests (`.h`, `.hh`, `.hpp`,
                `.proto`, `.graphql`, `.gql`, `.thrift`, `.prisma`, `.sql` DDL,
                interface classes); extract exact DDL table names and exported
                build targets.
            2.  Module entry points (`main.*`, `index.*`, `lib.*`, `mod.*`,
                `__init__.py`, or files matching directory name), then
                production source/query files alphabetically.
            3.  Templates and configs: up to 200 lines each (800 in config-only
                directories); exclude `.css`/`.scss`.
            4.  Test files (`*_test.*`, `*Test.*`, `test_*.*`, `*.spec.*`):
                ignore entirely, including in hybrid directories.
        *   *Child Fault Tolerance*: If the inline scan fails or is cut short, log a
            warning, use placeholder values `["(Details pending/documentation
            failed)"]`, and continue execution.

    *   **Parent Context Propagation**: When processing a parent directory `P`,
        retrieve the compiled interface summaries of its immediate child
        subdirectories.

        *   *Propagation Heuristics*:
            1.  If the child was documented during this run, retrieve its public
                interface directly from the in-memory execution cache.
            2.  If the child was corrected/modified (Correction Policy), use the
                merged legacy extraction symbols.
        *   Use these child symbol blocks as context when compiling `P`'s contract.

    *   **Verification Command Target Lookup**: Populate the Verification section
        using the discovered `VerificationCommand`.
        *   If the project uses Bazel/BUILD files: check if a `BUILD` file exists
            in `D` or the nearest ancestor, referencing `bazel test` / `bazel build`
            with valid target patterns (`//[package_path]/...` or
            `//[package_path]:all`, never `//[package_path]...` or
            `//[package_path]:...`). Use `bazel run` for interactive runner
            targets.
        *   If the project uses other manifests (`package.json`, `Cargo.toml`,
            `go.mod`, `pyproject.toml`, `*.sln`, `*.csproj`, `Makefile`), populate
            with the corresponding test runner command (.NET: `dotnet test` on
            the nearest `*.csproj`).
        *   If no verification command is identified, omit or use a placeholder.

    *   **Directory Classification & Template Generation**: Generate or correct
        `target_filename` using your file-writing tool or your file-editing tool based on
        `D`'s classification.

        *   **Component Package (Peanut)**: `D` contains direct source code
            files. Use the **Component Package README Template**. (If it also
            has child subdirectories, include relative links to their contracts
            in the Interface section).
        *   **Repository Blueprint (Hay)**: `D` contains no direct source code
            files, but contains subdirectories with code contracts. Use the
            **Intermediate Blueprint README Template**.
        *   **Link Formatting Policy (CRITICAL)**: Package contract files must use a
            hybrid link formatting approach to balance portability and clarity:
            1.  **Relative Links to Existing Files Only**: Use relative paths
                (e.g., `./child/${target_filename}` or `../sibling/${target_filename}`) for child
                contracts and sibling file references within the same codebase
                subsystem. (CRITICAL: Only generate `[Child](./child/${target_filename})`
                links for child directories that exist in the pruned
                `subtree_index` and contain an actual `${target_filename}`. If a child
                directory contains a `SKILL.md` or other non-contract asset, link
                directly to `./child/SKILL.md` or format it as an unlinked
                bullet point. Never output speculative links to non-existent
                contract files).
            2.  **Absolute Links**: Use standard URLs or repository paths
                for referencing files outside the package subsystem (e.g.,
                cross-package dependencies).

    *   **Markdown Formatting**: Immediately after writing or correcting
        `target_filename` in `D`, ensure clean markdown formatting (valid headers,
        tables, and code fences). If a project markdown formatter (e.g. `npx prettier --write`)
        is configured in the repository, you may execute it on `target_filename`.

3.  **Contract Index**: Once the tree is fully traversed, compile
    the `subtree_index` array containing the `path`, `summary`, `interface`,
    `invariants`, and `side_effects` for every processed directory.

4.  Proceed directly to **Step 5: Root Compilation & Termination**.

---

### Step 5: Root Compilation & Termination (Root Orchestrator)

1.  **Collect Results**: Sequential execution has no parallel results. Compile
    from the contracts written in Step 4.

    *   **Root Fault Tolerance**: If a contract is missing or incomplete, log a
        warning, insert a placeholder warning link (`[Subtree Root]
        (Documentation failed / Incomplete scan)`) in the root Blueprint's
        subdirectory index, and complete the remaining compilation.
        (Incomplete files are handled as an incremental
        progress feature; the Correction Policy allows resuming on subsequent
        runs).

2.  **Intermediate Directory Documentation**: Identify any intermediate
    directories sitting between the root `path` and the documented directories.

    *   Process these intermediate directories sequentially bottom-up.
    *   Generate Intermediate Blueprint contract files using the compiled summaries from Step 4.
    *   Ensure clean formatting and valid relative links for each Intermediate
        Blueprint contract file.

3.  **Root Directory Documentation**: The target root `path` of the execution is
    *always* classified as the **Repository Root (Blueprint / Hay)**.

    *   Check if `target_filename` already exists in `path`. If present, apply the
        **Correction & Modification Policy** to read and retain the existing
        title, metadata, and architectural overview at the top of the root
        contract file.
    *   Check if `path` itself contains any direct source files. If present,
        scan `path` inline to extract local symbols
        and invariants, appending them under the optional `## Local Interface &
        Invariants` section.
    *   Compile the final root `target_filename` using the **Repository Root Blueprint
        Template**, rolling up all top-level subdirectory boundaries. Ensure any
        root architecture or sequence diagrams strictly match the synchronous /
        asynchronous boundaries, operation names, and storage backends in the
        child contracts without inventing unverified nodes.
    *   Write the root `target_filename` using your file-writing tool.

4.  **Final Correctness Verification (CRITICAL)**: You MUST perform a final
    verification pass across ALL created and modified contract files
    (including all child package contracts like `pkg1/${target_filename}`
    and `pkg2/${target_filename}`) as a correctness check before concluding work. You
    MUST explicitly read every single created or modified contract file
    to verify its content. Do not skip any child contract files. Verify:

    *   **EGM Compliance & Code Grounding**: Ensure `Interface`, `Invariants`,
        and `Side Effects` sections exist, cite real code symbols/flags/tables
        from your inline scan, and contain zero speculative or unverified
        claims.
    *   **Markdown Syntax**: Ensure clean headers, valid tables, and proper code block fences.
    *   **Valid & Resolvable Links (CRITICAL)**: Ensure all subdirectory and
        sibling links use valid relative paths (`./subdir/${target_filename}` or
        `./subdir/SKILL.md`), and explicitly verify that every referenced target
        file actually exists on the filesystem. Remove or correct any broken
        relative references.
    *   **Valid Targets**: Verify verification targets match project test
        configuration and use valid target syntax (for Bazel, `/...` or
        `:all`, never `:...`).

5.  **Optional Drift Review (CRITICAL)**: After verification, ask the user (using the `question` tool) to offer running a drift report
    on the generated documentation updates:

    *   `question`: "Do you want to run the EGM Drift Report on the generated
        contract updates to check for consistency with the codebase?"
    *   `options`: `["(Recommended) Yes, run drift report on modified contracts",
        "No, skip drift review"]`
    *   If the user selects "Yes", run the `egm-drift-report` skill targeting
        the modified contracts to verify both missing code coverage and
        doc-to-code hallucinations (verifying every documented method, route,
        enum, database table, and invariant against local source files and
        recording discrepancies in the drift report for human triage). (Note:
        While `egm-drift-report` is often used for design documents, it can be
        applied to EGM-compliant contracts as a variant).

6.  Terminate execution successfully.

---

## Templates

Before writing any contract file, read the
[README templates](references/templates.md) relative to this skill directory.
It defines the **Component Package (Peanuts)**, **Repository Root (Blueprint /
Hay)**, and **Intermediate Blueprint** README templates referenced above.
