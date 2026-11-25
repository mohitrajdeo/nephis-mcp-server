const fs = require('fs');
const content = fs.readFileSync('D:/MOHIT/docker/JUDGE0/nephis-mcp-repo/src/index.ts', 'utf-8');

// Find TOOLS array
const toolsStart = content.indexOf('const TOOLS: Tool[] = [');
const toolsEnd = content.indexOf('export const TOOLS_EXPORT = TOOLS;');
const toolsSlice = content.slice(toolsStart, toolsEnd);

const regex = /name:\s*"([a-zA-Z0-9_]+)",\s*description:\s*"([^"]+)",\s*inputSchema:\s*({[\s\S]*?\n\s*},)/g;
let match;
const schemaMap = {};
while ((match = regex.exec(toolsSlice)) !== null) {
  const name = match[1];
  const schemaStr = match[3].slice(0, -1);
  try {
    const fn = new Function('return ' + schemaStr);
    schemaMap[name] = fn();
  } catch (e) {
    schemaMap[name] = { raw: schemaStr };
  }
}

const remaining = [
  'thanaton_run_code','thanaton_spawn_sandbox','thanaton_list_sandboxes','thanaton_wake_sandbox',
  'thanaton_sleep_sandbox','thanaton_destroy_sandbox','thanaton_create_project','thanaton_deploy_code',
  'thanaton_get_logs','thanaton_manage_env','thanaton_rollback','thanaton_promote',
  'thanaton_deployment_status','thanaton_set_preview','thanaton_project_metrics','thanaton_sandbox_telemetry',
  'thanaton_cluster_live_metrics','mnemon_metrics_catalog','mnemon_metrics_branches','mnemon_metrics_snapshots',
  'mnemon_project_metrics','thanaton_fleet_metrics','thanaton_fleet_projects','thanaton_fleet_deployments',
  'thanaton_fleet_snapshots','thanaton_configure_waf','mnemon_create_tenant','mnemon_list_tenants',
  'mnemon_promote_branch','mnemon_reset_branch','mnemon_get_schema','mnemon_configure_scaling',
  'mnemon_time_travel','mnemon_branch_lineage','mnemon_query_advisor','mnemon_create_snapshot',
  'mnemon_pitr_timelines','mnemon_pitr_restore','mnemon_cdc_stats','mnemon_cdc_publish',
  'mnemon_import_database','mnemon_import_status','mnemon_import_cutover','mnemon_vector_quantize',
  'mnemon_vector_stats','mnemon_admin_kill_query','mnemon_admin_reap_branches','thanaton_reap_extents',
  'mnemon_clone_vector','eschaton_preflight_check','nephis_fast_batch','eschaton_fast_batch',
  'thanaton_pty_info','mnemon_wal_rewind','thanaton_manage_crons','eschaton_sanitize_check',
  'eschaton_dbms_eval','eschaton_fileio_eval','thanaton_live_migrate','mnemon_rls_policy',
  'ananke_checkpoint'
];

for (const t of remaining) {
  const s = schemaMap[t] || {};
  const req = s.required || [];
  const props = Object.keys(s.properties || {});
  console.log(`${t} | req: [${req.join(', ')}] | props: [${props.join(', ')}]`);
}
