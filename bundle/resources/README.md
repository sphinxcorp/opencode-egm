# Shared runtime resources

These files are the authoritative instructions and rubrics loaded by EGM
skills and reviewers. Update the rules here; link to them from human guides
instead of maintaining separate summaries of their requirements.

## Overview
Shared runtime resources consumed by EGM skills and reviewers.

## Interface
- [Execution instructions](execution_instructions.md)
- [Feature specification standard](document_standards/feature-spec-standard.md)
- [Heilmeier standard](document_standards/heilmeier-standard.md)
- [Implementation readiness standard](document_standards/implementation-readiness-standard.md)
- [Re-implementation standard](document_standards/re-implementation-standard.md)
- [Zoom-out standard](document_standards/zoom-out-standard.md)
- [document_standards](./document_standards/README.md) - Shared document standards.

## Invariants
- Standards are authoritative; skills link to them rather than duplicating rules.
- `execution_instructions.md` defines design-only scope and consensus gates.

## Side Effects
- None; read-only reference assets.

## Verification
- Run: `npm run validate`

For installation, usage, and design rationale, see the [project README](../../README.md).
Workflow definitions live in [`skills/`](../skills/), and reviewer personas live in [`agents/`](../agents/).