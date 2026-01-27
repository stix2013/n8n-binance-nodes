import { spawn } from "bun";

console.log("🚀 Initializing n8n-binance-nodes environment...");

// Helper to read .env
function getEnvValue(key: string): string | undefined {
  try {
    const envFile = Bun.file(".env");
    const text = await envFile.text();
    const match = text.match(new RegExp(`${key}=(.+)`));
    return match ? match[1].trim().replace(/"/g, "") : undefined;
  } catch {
    return undefined;
  }
}

const ZROK_RESERVED_NAME = getEnvValue("ZROK_RESERVED_NAME") || "stix2025n8n";
const ZROK_PUBLIC_URL = getEnvValue("ZROK_PUBLIC_URL") || "https://stixgoauth2025.share.zrok.io";

// 1. Start Docker Compose
console.log("\n📦 Starting Docker containers...");
const docker = Bun.spawn(["docker", "compose", "up", "-d"], {
  stdout: "inherit",
  stderr: "inherit",
});

await docker.exited;

if (docker.exitCode !== 0) {
  console.error("❌ Docker Compose failed to start. Exiting.");
  process.exit(1);
}

console.log("✅ Docker services are running.");

// 2. Start Zrok Tunnel
console.log(`\n🌐 Starting Zrok Tunnel (Reserved: ${ZROK_RESERVED_NAME})...`);
console.log("-------------------------------------------------------");
console.log(`Target URL: ${ZROK_PUBLIC_URL}`);
console.log("Press Ctrl+C to stop the tunnel.");
console.log("-------------------------------------------------------");

const zrok = Bun.spawn(["zrok", "share", "reserved", ZROK_RESERVED_NAME], {
  stdout: "inherit",
  stderr: "inherit",
});

const handleShutdown = () => {
  console.log("\n🛑 Shutting down...");
  zrok.kill();
  process.exit(0);
};

process.on("SIGINT", handleShutdown);
process.on("SIGTERM", handleShutdown);

await zrok.exited;