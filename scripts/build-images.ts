import { getEnvValue, buildImage } from "./utils/docker-build";

async function main() {
  console.log("🐳 Docker Image Builder (Build All)");
  console.log("==================================");

  // Load versions from .env
  const n8nVersion = await getEnvValue("N8N_VERSION") || "2.6.4";
  const apiVersion = await getEnvValue("API_VERSION") || "0.4.1";
  const apiPythonVersion = await getEnvValue("API_PYTHON_VERSION") || "3.14";

  console.log(`Configured Versions:`);
  console.log(`- N8N_VERSION: ${n8nVersion}`);
  console.log(`- API_VERSION: ${apiVersion}\n`);

  // 1. Build custom n8n nodes
  console.log("\n📦 Building custom n8n nodes...");
  const { execSync } = await import("child_process");
  execSync("cd nodes/@stix/n8n-nodes-binance-kline && bun install && bun run build", { stdio: "inherit" });
  execSync("cd nodes/@stix/n8n-nodes-markdown-saver && bun install && bun run build", { stdio: "inherit" });

  // 2. Build custom-n8n image
  await buildImage(
    `n8n-custom:${n8nVersion}`,
    "dockers/Dockerfile.n8n",
    ".",
    { N8N_VERSION: n8nVersion }
  );

  // 3. Build n8n-runners
  await buildImage(
    `n8nio-runners:${n8nVersion}-local`,
    "dockers/Dockerfile",
    "./dockers",
    { N8N_VERSION: n8nVersion }
  );

  // 4. Build api-python
  await buildImage(
    `api-python${apiPythonVersion}:${apiVersion}`,
    "dockers/Dockerfile.python",
    ".",
    { API_VERSION: apiVersion }
  );

  console.log("\n✨ All images built successfully!");
}

main();
