import { getEnvValue, buildImage } from "./utils/docker-build";

async function main() {
  console.log("🐳 Docker Image Builder (Build All)");
  console.log("==================================");

  // Load versions from .env
  const n8nVersion = await getEnvValue("N8N_VERSION") || "2.6.4";
  const apiVersion = await getEnvValue("API_VERSION") || "0.4.1";

  console.log(`Configured Versions:`);
  console.log(`- N8N_VERSION: ${n8nVersion}`);
  console.log(`- API_VERSION: ${apiVersion}\n`);

  // 1. Build n8n-runners
  await buildImage(
    `n8nio-runners:${n8nVersion}-local`,
    "dockers/Dockerfile",
    "./dockers",
    { N8N_VERSION: n8nVersion }
  );

  // 2. Build api-python
  await buildImage(
    `api-python3.13:${apiVersion}`,
    "dockers/Dockerfile.python",
    ".",
    { API_VERSION: apiVersion }
  );

  // 3. Build custom-postgres
  await buildImage(
    "postgres-custom:16-alpine",
    "dockers/Dockerfile.postgres",
    "./dockers"
  );

  console.log("\n✨ All images built successfully!");
}

main();
