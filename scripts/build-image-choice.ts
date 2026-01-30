import { getEnvValue, buildImage } from "./utils/docker-build";

const ESC = "\u001b";
const UP = `${ESC}[A`;
const DOWN = `${ESC}[B`;
const ENTER = "\r";
const CTRL_C = "\u0003";

const options = [
  { id: "all", label: "🚀 Build All Images" },
  { id: "runners", label: "📦 n8n-runners" },
  { id: "api", label: "🐍 api-python" },
  { id: "postgres", label: "🐘 custom-postgres" },
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

  const n8nVersion = await getEnvValue("N8N_VERSION") || "2.6.0";
  const apiVersion = await getEnvValue("API_VERSION") || "0.4.1";

  switch (choice) {
    case "all":
      await buildImage(`n8nio-runners:${n8nVersion}-local`, "dockers/Dockerfile", "./dockers", { N8N_VERSION: n8nVersion });
      await buildImage(`api-python3.13:${apiVersion}`, "dockers/Dockerfile.python", ".", { API_VERSION: apiVersion });
      await buildImage("postgres-custom:16-alpine", "dockers/Dockerfile.postgres", "./dockers");
      break;
    case "runners":
      await buildImage(`n8nio-runners:${n8nVersion}-local`, "dockers/Dockerfile", "./dockers", { N8N_VERSION: n8nVersion });
      break;
    case "api":
      await buildImage(`api-python3.13:${apiVersion}`, "dockers/Dockerfile.python", ".", { API_VERSION: apiVersion });
      break;
    case "postgres":
      await buildImage("postgres-custom:16-alpine", "dockers/Dockerfile.postgres", "./dockers");
      break;
  }

  console.log("\n✨ Process complete!");
}

main();
