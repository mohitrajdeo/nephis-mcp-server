# Provider Metrics API Reference

Every endpoint below is served by the control planes deployed on the remote host. Responses carry value, unit, `observed_at`, `source` and `stale`. A value the provider did not return is `null` with `stale: true` — never a generated measurement.

## Authentication

Pass the account key as `X-API-Key` or `Authorization: Bearer <key>`. The gateway binds tenant-scoped requests to the tenant behind the key; a `?tenant=` or `tenant_id` that does not match returns `403 tenant scope does not match the presented API key`.

Mnemon keys: `mrd_live_…`, `nephis_live_…`. Thanaton keys: `esk_live_…`.

## Mnemon endpoints

| Route | Returns |
|---|---|
| `GET /v1/metrics/catalog` | `counts` (projects, branches, snapshots), `fetched_at`, `source`, per-project summaries with `created_at`/`updated_at` |
| `GET /v1/metrics/branches` | `count`, per-branch `branch_id`, `name`, `parent_branch_id`, `state`, `timeline_id`, `target_lsn`, `age_seconds`, `created_at` |
| `GET /v1/metrics/snapshots` | `count`, per-snapshot `size_mb`, `snapshot_lsn`, `branch_id`, `created_at` |
| `GET /v1/projects/{id}/metrics/overview` | `branch_count`, `snapshot_count` as measured values; `measured_storage_mb` is `null`/stale when not provided |

## Thanaton endpoints

| Route | Returns |
|---|---|
| `GET /api/v1/metrics/fleet/overview` | `metrics.organizations`, `metrics.projects`, `metrics.deployments` with units and sources; `guest_vms` and `idle_cost` are explicitly `null`/stale |
| `GET /api/v1/metrics/fleet/projects` | `count`, per-project `state`, `runtime`, `execution_mode`, `memory_mb`, `vcpu_count`, `deployment_count`, `created_at`, `updated_at` |
| `GET /api/v1/metrics/fleet/deployments` | `count`, per-deployment `build_duration_ms`, `snapshot_size_bytes`, `status`, `hypervisor_node_id`, `created_at` |
| `GET /api/v1/metrics/fleet/snapshots` | `count`, per-snapshot `size_mb`, `state`, `rootfs_hash`, `created_at` |

## Deployment

Two Go services run on the remote host as systemd units:

- `nephis-metrics-mnemon.service` — port `7101`, binary `/opt/nephis/metrics/mnemon-api-metrics`
- `nephis-metrics-thanaton.service` — port `8399`, binary `/opt/nephis/metrics/thanaton-api-metrics`

nginx routes `/v1/metrics/` to `7101` and `/api/v1/metrics/fleet/` to `8399` across the portal server blocks.

## Examples

curl:

```bash
curl -H "X-API-Key: $NEPHIS_API_KEY" https://nephis.theeducode.com/v1/metrics/catalog
curl -H "X-API-Key: $NEPHIS_API_KEY" https://nephis.theeducode.com/api/v1/metrics/fleet/overview
```

CLI:

```bash
mnemon metrics catalog
mnemon metrics branches
mnemon metrics project --project-id <id>
thanaton metrics overview
thanaton metrics deployments
```

Manual pages: `mnemon man metrics`, `thanaton man metrics`.

MCP tools: `mnemon_metrics_catalog`, `mnemon_metrics_branches`, `mnemon_metrics_snapshots`, `mnemon_project_metrics`, `thanaton_fleet_metrics`, `thanaton_fleet_projects`, `thanaton_fleet_deployments`, `thanaton_fleet_snapshots`.

TypeScript SDK:

```ts
const client = new ThanatonClient({ apiKey: process.env.NEPHIS_API_KEY });
await client.getMnemonMetricsCatalog();
await client.getMnemonBranchMetrics();
await client.getMnemonSnapshotMetrics();
await client.getMnemonProjectMetrics(projectId);
await client.getThanatonFleetMetrics();
await client.getThanatonFleetProjects();
await client.getThanatonFleetDeployments();
await client.getThanatonFleetSnapshots();
```
