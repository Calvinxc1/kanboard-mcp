# AGENTS.md

Repository policy entrypoint.

Authoritative policy lives under `.governance/`.

Precedence:

1. `AGENTS.md`
2. `.governance/processes/*.yaml`
3. `.governance/policies/*.yaml`
4. `.governance/overrides/*`

If ambiguity remains, ask before acting.

Override-governance rules are non-overridable unless a process file explicitly
says otherwise.

Always load:

- `.governance/policies/universal.yaml`

Load additional policy only via:

- `.governance/task-map.yaml`
