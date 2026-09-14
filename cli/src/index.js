const path = require("path");
const open = require("open");
const logger = require("./logger");
const envChecker = require("./env-checker");
const repoManager = require("./repo-manager");
const backendManager = require("./backend");
const frontendManager = require("./frontend");

const pkg = require("../package.json");

function parseArgs(args) {
  const options = {
    command: "start",
    port: 8000,
    frontendPort: 5173,
    dir: null,
    skipBuild: false,
    noOpen: false,
    help: false,
    version: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === "--help" || arg === "-h") {
      options.help = true;
    } else if (arg === "--version" || arg === "-v") {
      options.version = true;
    } else if (arg === "--port" || arg === "-p") {
      options.port = parseInt(args[++i], 10) || 8000;
    } else if (arg === "--frontend-port") {
      options.frontendPort = parseInt(args[++i], 10) || 5173;
    } else if (arg === "--dir" || arg === "-d") {
      options.dir = args[++i];
    } else if (arg === "--skip-build") {
      options.skipBuild = true;
    } else if (arg === "--no-open") {
      options.noOpen = true;
    } else if (!arg.startsWith("-")) {
      options.command = arg.toLowerCase();
    }
  }

  return options;
}

function showHelp() {
  logger.banner();
  console.log(`
Usage: npx docs-search-cli [command] [options]

Commands:
  start               Install dependencies, setup application & start servers (default)
  install             Setup virtualenv and install all dependencies without starting
  check               Run system prerequisite checks (Python, Node, npm, Git)

Options:
  -p, --port <port>           Backend API server port (default: 8000)
  --frontend-port <port>      Frontend dev server port (default: 5173)
  -d, --dir <dir>             Custom installation directory (default: ~/.docs-search)
  --skip-build                Skip building the Vue frontend bundle
  --no-open                   Do not open browser automatically
  -h, --help                  Show CLI help menu
  -v, --version               Show CLI version
`);
}

async function main() {
  const rawArgs = process.argv.slice(2);
  const options = parseArgs(rawArgs);

  if (options.help) {
    showHelp();
    process.exit(0);
  }

  if (options.version) {
    console.log(`docs-search-cli v${pkg.version}`);
    process.exit(0);
  }

  logger.banner();

  // Determine if running inside local codebase
  const cwd = process.cwd();
  const isLocalRepo = repoManager.isValidDocsSearchDir(cwd);

  // 1. Run system prerequisite check
  const envResult = envChecker.checkAllEnv({ isLocalRepo });
  if (options.command === "check") {
    process.exit(envResult.valid ? 0 : 1);
  }

  if (!envResult.valid) {
    logger.error("Cannot proceed due to missing system prerequisites listed above.");
    process.exit(1);
  }

  // 2. Fetch or locate repository
  const repoInfo = repoManager.findOrFetchRepo(options);
  const repoDir = repoInfo.path;
  const frontendDir = path.join(repoDir, "frontend");

  // 3. Setup Python virtual environment
  const venvPython = backendManager.ensureVenv(repoDir, envResult.python.cmd);

  // 4. Install backend dependencies
  backendManager.installDependencies(repoDir, venvPython);

  // 5. Run database migrations
  backendManager.runMigrations(repoDir, venvPython);

  // 6. Install frontend dependencies
  frontendManager.installDependencies(frontendDir, envResult.npm.cmd || "npm");

  if (options.command === "install") {
    if (!options.skipBuild) {
      frontendManager.build(frontendDir, envResult.npm.cmd || "npm");
    }
    logger.success("\n🎉 Installation and setup completed successfully!");
    process.exit(0);
  }

  // 7. Start Backend & Frontend Servers
  const activeProcesses = [];

  const backendProc = backendManager.startServer(repoDir, venvPython, options.port);
  if (backendProc) activeProcesses.push(backendProc);

  const frontendProc = frontendManager.startServer(frontendDir, envResult.npm.cmd || "npm", options.frontendPort);
  if (frontendProc) activeProcesses.push(frontendProc);

  const cleanup = () => {
    logger.info("\nStopping servers...");
    activeProcesses.forEach((p) => {
      try {
        p.kill("SIGINT");
      } catch (e) {}
    });
    process.exit(0);
  };

  process.on("SIGINT", cleanup);
  process.on("SIGTERM", cleanup);

  // 8. Open Browser
  const frontendUrl = `http://localhost:${options.frontendPort}`;
  if (!options.noOpen) {
    logger.info(`Opening browser in 3 seconds at ${frontendUrl}...`);
    setTimeout(async () => {
      try {
        await open(frontendUrl);
      } catch (e) {
        logger.warn(`Could not launch browser automatically: ${e.message}`);
      }
    }, 3000);
  }

  logger.success(`\n🚀 RAG Application is running!`);
  logger.dim(`  • Frontend: ${frontendUrl}`);
  logger.dim(`  • Backend API: http://127.0.0.1:${options.port}/api/v1/`);
  logger.dim(`  • Press Ctrl+C to stop.\n`);
}

module.exports = { main };
