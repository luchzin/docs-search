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
 * Gets virtual environment Python executable path.
 */
function getVenvPython(venvDir) {
  return IS_WIN
    ? path.join(venvDir, "Scripts", "python.exe")
    : path.join(venvDir, "bin", "python");
}

/**
 * Ensures Python virtualenv exists in target repository.
 */
function ensureVenv(repoDir, pythonCmdPrefix) {
  const venvDir = path.join(repoDir, "venv");
  const venvPython = getVenvPython(venvDir);

  if (fs.existsSync(venvPython)) {
    logger.info(`Using existing Python virtual environment at: ${venvDir}`);
    return venvPython;
  }

  logger.step(`Creating Python virtual environment in ${venvDir}...`);
  const mainCmd = pythonCmdPrefix[0];
  const args = [...pythonCmdPrefix.slice(1), "-m", "venv", "venv"];
  runCmd(mainCmd, args, repoDir);

  if (!fs.existsSync(venvPython)) {
    throw new Error(`Virtualenv creation succeeded but Python executable was not found at ${venvPython}`);
  }

  logger.success("Virtual environment created successfully.");
  return venvPython;
}

/**
 * Installs Python dependencies from requirements.txt.
 */
function installDependencies(repoDir, venvPython) {
  const reqFile = path.join(repoDir, "requirements.txt");
  if (!fs.existsSync(reqFile)) {
    logger.warn(`No requirements.txt found in ${repoDir}`);
    return;
  }

  logger.step("Installing backend Python dependencies...");
  try {
    runCmd(venvPython, ["-m", "pip", "install", "--upgrade", "pip"], repoDir);
  } catch (err) {
    logger.warn("Could not upgrade pip, continuing with installation...");
  }

  runCmd(venvPython, ["-m", "pip", "install", "-r", "requirements.txt"], repoDir);
  logger.success("Backend Python dependencies installed successfully.");
}

/**
 * Runs Django database migrations.
 */
function runMigrations(repoDir, venvPython) {
  logger.step("Running RAG database migrations...");
  runCmd(venvPython, ["manage.py", "migrate"], repoDir);
  logger.success("Database migrations completed.");
}

/**
 * Spawns Django backend server.
 */
function startServer(repoDir, venvPython, port = 8000) {
  logger.step(`Starting Django Backend API server on http://127.0.0.1:${port}...`);
  const proc = spawn(
    venvPython,
    ["manage.py", "runserver", `0.0.0.0:${port}`],
    {
      cwd: repoDir,
      stdio: "inherit",
      shell: IS_WIN,
    }
  );

  return proc;
}

module.exports = {
  ensureVenv,
  installDependencies,
  runMigrations,
  startServer,
};
