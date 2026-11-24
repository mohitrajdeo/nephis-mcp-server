import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const apiKey = process.env.NEPHIS_API_KEY || "";
const transport = new StdioClientTransport({
  command: "node",
  args: ["dist/index.js"],
  env: { ...process.env, NEPHIS_API_KEY: apiKey },
});
const client = new Client({ name: "metrics-probe", version: "1.0.0" });
await client.connect(transport);

const listed = await client.listTools();
const metricsTools = listed.tools.filter((t) => t.name.includes("metrics"));
console.log("metrics tools:", metricsTools.map((t) => t.name).join(", "));

for (const name of ["mnemon_metrics_catalog", "thanaton_fleet_metrics", "thanaton_fleet_projects"]) {
  const res = await client.callTool({ name, arguments: {} });
  const text = res.content?.[0]?.text ?? "";
  console.log(name, "->", text.slice(0, 320).replace(/\s+/g, " "));
}

await client.close();
