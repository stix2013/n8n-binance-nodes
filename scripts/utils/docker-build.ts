import { spawn } from "bun";

/**
 * Helper to read .env values
 */
export async function getEnvValue(key: string): Promise<string | undefined> {
  try {
    const envFile = Bun.file(".env");
    const text = await envFile.text();
    const lines = text.split('\n');
    for (const line of lines) {
      const trimmedLine = line.trim();
      if (!trimmedLine || trimmedLine.startsWith('#')) continue;
      
      const [k, ...v] = trimmedLine.split('=');
      if (k && k.trim() === key) {
        return v.join('=').trim().replace(/"/g, "").replace(/'/g, "");
      }
    }
    return undefined;
  } catch {
    return undefined;
  }
}

/**
 * Executes a docker build command
 */
export async function buildImage(tag: string, dockerfile: string, context: string, args: Record<string, string> = {}) {
  console.log(`\n🔨 Building image: ${tag}...`);
  console.log(`   Dockerfile: ${dockerfile}`);
  console.log(`   Context:    ${context}`);
  
  const cmd = ["docker", "build", "-t", tag, "-f", dockerfile];
  
  for (const [key, value] of Object.entries(args)) {
    cmd.push("--build-arg", `${key}=${value}`);
  }
  
  cmd.push(context);

  const process = Bun.spawn(cmd, {
    stdout: "inherit",
    stderr: "inherit",
  });

  await process.exited;

  if (process.exitCode !== 0) {
    console.error(`❌ Failed to build image: ${tag}`);
    process.exit(1);
  }
  console.log(`✅ Successfully built: ${tag}`);
}
