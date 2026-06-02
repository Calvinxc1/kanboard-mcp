# .governance

This directory contains the repository's AI governance corpus.

## Layout

- `policies/`: standing repository policies grouped by domain.
- `task-map.yaml`: task-to-policy routing map for selective loading.
- `processes/`: governance-process rules such as override handling and policy maintenance.
- `overrides/`: structured override records and the schema governing those records.

## Authoritative Files

The repository policy entrypoint is [../AGENTS.md](../AGENTS.md). Files under
this directory are the machine-readable policy body that `AGENTS.md` points to.

## Repository Focus

This repository is an MCP server for Kanboard. The highest-risk AI-assisted
changes are changes that affect:

- Kanboard JSON-RPC method names and parameter shape.
- MCP tool signatures and response payload shape.
- Authentication, API token handling, or configuration disclosure.
- Local editable MCP usage and operator documentation.
- Test coverage, warning cleanliness, and regression guarantees.

## Guidance

- Keep standing policy in `policies/`.
- Keep task routing in `task-map.yaml`.
- Keep meta-governance and maintenance rules in `processes/`.
- Keep temporary exception records and their data definitions in `overrides/`.
- When policy structure changes, update `AGENTS.md` and this directory together.
