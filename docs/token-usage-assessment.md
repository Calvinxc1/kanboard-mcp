# MCP Token Usage Assessment

## Kanboard connector

Primary token costs:

- Tool surface: the server registers every tool module at startup, exposing task, project, category, column, board, comment, user, link, subtask, swimlane, tag, file, and diagnostic tools. Each tool name, description, and JSON schema is loaded into MCP context.
- Task responses: `getTask`, `getAllTasks`, `searchTasks`, and overdue task tools previously returned full Kanboard task records. Those records include many fields that are not normally needed for board operations, including recurrence metadata, external provider fields, nested color details, and several timestamps.
- Bulk task reads: `getAllTasks` and `searchTasks` multiply that verbose record shape across every returned task.

Applied low-risk changes:

- Task read/list/search responses now return compact task summaries from `src/kanboard_mcp/tools/tasks.py`.
- The summary keeps board-relevant fields: `id`, `title`, `column_id`, `swimlane_id`, `position`, `is_active`, `owner_id`, `category_id`, `priority`, `date_due`, `color_id`, and `reference`.
- Flat task summaries omit `project_id` because it is already supplied as the read-call parameter; `getTask` still includes it for detail reads.
- Task summaries omit `null` values plus true empty sentinels such as `reference: ""` and `date_due: 0`, and no longer repeat the derivable task `url`.
- Binary or stateful zero values remain explicit, including `is_active: 0`, `category_id: 0`, and `priority: 0`, so closed and unset states are not encoded by field absence.
- The projection drops noisy fields such as inactive recurrence details, nested `color`, external provider fields, and unused timestamps.
- `getBoard` now preserves the board/column structure but summarizes every nested task with the same compact task shape, avoiding board-wide task bodies and repeated Kanboard filler fields.
- `getBoard` also drops column descriptions and redundant count/score fields, keeping only `nb_open_tasks` for column task counts, and removes task/column IDs already implied by the swimlane/column nesting.
- `getTask` now uses a single-task detail projection that includes `description`, `date_modification`, `nb_comments`, and `nb_subtasks`; this makes one-task lookup the explicit path for paying the token cost of task bodies, modification timestamps, and comment/subtask count hints.
- `getTask` includes recurrence fields only when `recurrence_status` is non-zero, so recurring cards are readable while non-recurring cards keep the compact detail shape.
- `test_connection` now returns only `connected`, `username`, and `server_url`, avoiding full Kanboard user records and latent `twofactor_secret` exposure.
- `getAllComments` now returns compact comment records with `id`, `date_creation`, `username`, and `comment`.
- `getAllSubtasks` now returns compact subtask records with actionable fields such as `id`, `title`, `status`, assignee, and time values, omitting task IDs and creation metadata already implied by the request.
- `getAllCategories`, `getAllLinks`, and `getAllTaskLinks` now use compact list projections so category and dependency conventions can stay in `core` without restoring full raw Kanboard payloads.
- `getAllProjects` now returns compact project records with `id`, `name`, `identifier`, `is_active`, `description`, `priority_start`, and `priority_end`, omitting empty/null/sentinel values and derivable URL objects.
- Existing Kanboard API calls, parameter names, and the standard MCP response shape are unchanged.
- Tool docstrings no longer repeat rote `Args:` parameter blocks already represented by the MCP JSON schema. Non-obvious usage guidance, such as Kanboard search syntax and due-date formats, is still preserved.
- The MCP tool surface now defaults to `KANBOARD_TOOL_PROFILE=core`, which exposes a reduced daily-driver tool set while preserving `full` as an opt-in compatibility profile.
- Tag tools remain available in the `full` profile, but are omitted from `core` after a live active-task check found no current Homelab task tag assignments.
- `KANBOARD_ENABLED_TOOL_MODULES` can limit registration to selected modules for installations that want an explicit module allowlist.

Deferred higher-risk options:

- `get_config_info` remains in `core` because it is small and has been useful for confirming the live editable clone and module paths during troubleshooting.

## NetBox connector

The NetBox connector is not present in this repository, and `netbox-mcp-setup.md` was not found in the local `git` workspace search. Based on the card description, likely token costs are full nested NetBox object responses, echoed URLs, related object expansion, and broad always-loaded tool schemas.

Recommended NetBox changes once its connector/config is available:

- Default list/get tools to a summary projection for common object types.
- Use NetBox `fields` query parameters by default where the API supports them.
- Keep full-detail retrieval available as an explicit opt-in path.
- Apply pagination defaults and avoid returning complete related records unless requested.
