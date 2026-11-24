# MCP provider metrics tools

Eight read-only tools expose the deployed control-plane metrics. Every response carries `value`, `unit`, `observed_at`, `source` and `stale`. A value the provider did not return is `null` with `stale: true`.

| Tool | Arguments | Returns |
|---|---|---|
| `mnemon_metrics_catalog` | none | project, branch and snapshot inventory counts |
| `mnemon_metrics_branches` | none | per-branch timeline ID, LSN, state, age and creation time |
| `mnemon_metrics_snapshots` | none | snapshot size and LSN |
| `mnemon_project_metrics` | `project_id` | measured values for one project |
| `thanaton_fleet_metrics` | none | organizations, projects, deployments; guest VMs and idle cost are explicitly null/stale |
| `thanaton_fleet_projects` | none | per-project state, runtime and deployment counts |
| `thanaton_fleet_deployments` | none | build duration and snapshot size |
| `thanaton_fleet_snapshots` | none | volume snapshot inventory |

Authentication comes from `NEPHIS_API_KEY` in the MCP server environment. The gateway binds tenant-scoped calls to the tenant behind the key.

See `METRICS_API_REFERENCE.md` for endpoint paths and provenance rules.
