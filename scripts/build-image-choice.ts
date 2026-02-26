import { getEnvValue, buildImage } from "./utils/docker-build";

const ESC = "\u001b";
const UP = `${ESC}[A`;
const DOWN = `${ESC}[B`;
const ENTER = "\r";
const CTRL_C = "\u0003";

const options = [
  { id: "all", label: "🚀 Build All Images" },
  { id: "n8n", label: "🔧 custom-n8n (with nodes)" },
  { id: "runners", label: "📦 n8n-runners" },
  { id: "api", label: "🐍 api-python" },
  { id: "exit", label: "❌ Exit" },
];

async function selectOption() {
  let selectedIndex = 0;
  const stdin = process.stdin;
  const stdout = process.stdout;

  // Set raw mode to capture keypresses
  stdin.setRawMode(true);
  stdin.resume();
  stdin.setEncoding("utf8");

  // Hide cursor
  stdout.write(`${ESC}[?25l`);

  const render = () => {
    // Move cursor to start of menu area (clear previous lines if needed)
    stdout.write(`${ESC}[G`); // Move to column 1
    
    console.log("\n🐳 Select which image to build (Use ↑/↓, Enter to select):");
    options.forEach((opt, i) => {
      if (i === selectedIndex) {
        stdout.write(`  ${ESC}[32m> ${opt.label}${ESC}[0m\n`); // Green with cursor
      } else {
        stdout.write(`    ${opt.label}\n`);
      }
    });
  };

  render();

  return new Promise<string>((resolve) => {
    stdin.on("data", (key: string) => {
      if (key === CTRL_C) {
        stdout.write(`${ESC}[?25h`); // Show cursor
        process.exit(0);
      }

      if (key === UP) {
        selectedIndex = (selectedIndex - 1 + options.length) % options.length;
        // Move cursor back up to redraw menu
        stdout.write(`${ESC}[${options.length + 2}A`);
        render();
      } else if (key === DOWN) {
        selectedIndex = (selectedIndex + 1) % options.length;
        stdout.write(`${ESC}[${options.length + 2}A`);
        render();
      } else if (key === ENTER) {
        // Cleanup menu from terminal
        stdout.write(`${ESC}[${options.length + 2}A${ESC}[J`);
        stdout.write(`${ESC}[?25h`); // Show cursor
        stdin.setRawMode(false);
        stdin.pause();
        resolve(options[selectedIndex].id);
      }
    });
  });
}

async function main() {
  const choice = await selectOption();

  const n8nVersion = await getEnvValue("N8N_VERSION") || "2.6.4";
  const apiVersion = await getEnvValue("API_VERSION") || "1.4.0";
  const apiPythonVersion = await getEnvValue("API_PYTHON_VERSION") || "3.14";
  const { execSync } = await import("child_process");

  switch (choice) {
    case "all":
      console.log("\n📦 Building custom n8n nodes...");
      execSync("cd nodes/@stix/n8n-nodes-binance-kline && bun install && bun run build", { stdio: "inherit" });
      execSync("cd nodes/@stix/n8n-nodes-markdown-saver && bun install && bun run build", { stdio: "inherit" });
      await buildImage(`n8n-custom:${n8nVersion}`, "dockers/Dockerfile.n8n", ".", { N8N_VERSION: n8nVersion });
      await buildImage(`n8nio-runners:${n8nVersion}-local`, "dockers/Dockerfile.runners", "./dockers", { N8N_VERSION: n8nVersion });
      await buildImage(`api-python${apiPythonVersion}:${apiVersion}`, "dockers/Dockerfile.python", ".", { API_VERSION: apiVersion });
      break;
    case "n8n":
      console.log("\n📦 Building custom n8n nodes...");
      execSync("cd nodes/@stix/n8n-nodes-binance-kline && bun install && bun run build", { stdio: "inherit" });
      execSync("cd nodes/@stix/n8n-nodes-markdown-saver && bun install && bun run build", { stdio: "inherit" });
      await buildImage(`n8n-custom:${n8nVersion}`, "dockers/Dockerfile.n8n", ".", { N8N_VERSION: n8nVersion });
      break;
    case "runners":
      await buildImage(`n8nio-runners:${n8nVersion}-local`, "dockers/Dockerfile.runners", "./dockers", { N8N_VERSION: n8nVersion });
      break;
    case "api":
      await buildImage(`api-python${apiPythonVersion}:${apiVersion}`, "dockers/Dockerfile.python", ".", { API_VERSION: apiVersion });
      break;
    case "exit":
      console.log("\n👋 Exiting...");
      process.exit(0);
      break;
  }

  console.log("\n✨ Process complete!");
}

main();
