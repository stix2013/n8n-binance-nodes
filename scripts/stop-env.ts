import { spawn } from "bun";

console.log("🛑 Stopping n8n-binance-nodes environment...");

// 1. Stop Zrok Tunnel (if running)
const zrokPs = Bun.spawnSync(["pgrep", "-f", "zrok share reserved"]);
const zrokPid = zrokPs.stdout.toString().trim();

if (zrokPid) {
  console.log(`🌐 Stopping Zrok tunnel (PID: ${zrokPid})...`);
  try {
    process.kill(parseInt(zrokPid));
    console.log("✅ Zrok tunnel stopped.");
  } catch {
    console.warn("⚠️ Failed to kill Zrok process.");
  }
} else {
  console.log("ℹ️ No Zrok tunnel running.");
}

// 2. Stop Docker Containers
console.log("\n📦 Stopping Docker containers...");
const docker = Bun.spawn(["docker", "compose", "down"], {
  stdout: "inherit",
  stderr: "inherit",
});

await docker.exited;

if (docker.exitCode !== 0) {
  console.error("❌ Docker Compose failed to stop. Exiting.");
  process.exit(1);
}

console.log("✅ Docker services stopped.");
