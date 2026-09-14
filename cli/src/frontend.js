const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawnSync, spawn } = require("child_process");
const logger = require("./logger");

const IS_WIN = os.platform() === "win32";

function runCmd(cmd, args, cwd) {
  logger.dim(`> ${cmd} ${args.join(" ")}`);
  const res = spawnSync(cmd, args, { cwd, stdio: "inherit", shell: IS_WIN });
  if (res.error) {
    throw new Error(`Failed to execute ${cmd}: ${res.error.message}`);
  }
  if (res.status !== 0) {
    throw new Error(`Command exited with status code ${res.status}`);
  }
}

/**
 * Installs Vue frontend node packages if missing.
 */
function installDependencies(frontendDir, npmCmd = "npm") {
  if (!fs.existsSync(frontendDir)) {
    logger.warn(`Frontend directory not found at ${frontendDir}`);
    return;
  }

  const nodeModulesPath = path.join(frontendDir, "node_modules");
  if (fs.existsSync(nodeModulesPath)) {
    logger.info("Frontend node_modules directory already exists.");
    return;
  }

  logger.step("Installing Vue frontend dependencies (npm install)...");
  runCmd(npmCmd, ["install"], frontendDir);
  logger.success("Frontend dependencies installed successfully.");
}

/**
 * Builds Vue production bundle.
 */
function build(frontendDir, npmCmd = "npm") {
  if (!fs.existsSync(frontendDir)) return;
  logger.step("Building frontend production bundle...");
  runCmd(npmCmd, ["run", "build"], frontendDir);
  logger.success("Frontend built successfully.");
}

/**
 * Spawns Vite frontend development/preview server.
 */
function startServer(frontendDir, npmCmd = "npm", port = 5173) {
  if (!fs.existsSync(frontendDir)) {
    throw new Error(`Frontend directory missing at ${frontendDir}`);
  }

  logger.step(`Starting Vue Frontend Dev server on http://localhost:${port}...`);
  const proc = spawn(
    npmCmd,
    ["run", "dev", "--", "--port", String(port)],
    {
      cwd: frontendDir,
      stdio: "inherit",
      shell: IS_WIN,
    }
  );

  return proc;
}

module.exports = {
  installDependencies,
  build,
  startServer,
};
