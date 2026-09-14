const { spawnSync } = require("child_process");
const os = require("os");
const logger = require("./logger");

const IS_WIN = os.platform() === "win32";

/**
 * Executes command synchronously and returns result object.
 */
function execCommand(cmd, args = []) {
  try {
    const res = spawnSync(cmd, args, {
      encoding: "utf-8",
      shell: IS_WIN,
      timeout: 10000,
    });
    return {
      status: res.status,
      stdout: (res.stdout || "").trim(),
      stderr: (res.stderr || "").trim(),
      error: res.error,
    };
  } catch (err) {
    return { status: -1, stdout: "", stderr: err.message, error: err };
  }
}

/**
 * Validates Python binary and verifies version >= 3.8.
 * Rejects Windows App Execution Alias stubs.
 */
function checkPythonCmd(cmdPrefix) {
  const cmdStr = Array.isArray(cmdPrefix) ? cmdPrefix.join(" ") : cmdPrefix;
  const mainCmd = Array.isArray(cmdPrefix) ? cmdPrefix[0] : cmdPrefix;
  const args = Array.isArray(cmdPrefix)
    ? [...cmdPrefix.slice(1), "--version"]
    : ["--version"];

  const res = execCommand(mainCmd, args);
  if (res.status !== 0 || res.error) {
    return null;
  }

  const output = (res.stdout || res.stderr || "").trim();
  // Windows store stub output check:
  if (output.includes("Python was not found") || output.includes("Microsoft Store")) {
    return null;
  }

  const match = output.match(/Python\s+(\d+)\.(\d+)\.(\d+)/i);
  if (!match) return null;

  const major = parseInt(match[1], 10);
  const minor = parseInt(match[2], 10);

  if (major < 3 || (major === 3 && minor < 8)) {
    return {
      valid: false,
      cmd: cmdPrefix,
      version: `${major}.${minor}`,
      error: `Python version ${major}.${minor} is below required minimum version 3.8`,
    };
  }

  return {
    valid: true,
    cmd: Array.isArray(cmdPrefix) ? cmdPrefix : [cmdPrefix],
    version: `${match[1]}.${match[2]}.${match[3]}`,
  };
}

/**
 * Finds a working Python 3 executable on system.
 */
function findPython() {
  const candidates = IS_WIN
    ? [["py", "-3"], ["python"], ["python3"]]
    : [["python3"], ["python"]];

  for (const candidate of candidates) {
    const res = checkPythonCmd(candidate);
    if (res && res.valid) {
      return res;
    }
  }

  return {
    valid: false,
    cmd: null,
    error: "Python 3 (3.8 or higher) is not installed or not available in PATH.",
  };
}

/**
 * Checks if venv module is supported by selected Python.
 */
function checkVenv(pythonCmd) {
  const mainCmd = pythonCmd[0];
  const args = [...pythonCmd.slice(1), "-m", "venv", "--help"];
  const res = execCommand(mainCmd, args);
  if (res.status !== 0) {
    return {
      valid: false,
      error: "Python 'venv' module is missing. On Ubuntu/Debian, install it with: sudo apt install python3-venv",
    };
  }
  return { valid: true };
}

/**
 * Checks Node.js installation (>= 18).
 */
function checkNode() {
  const res = execCommand("node", ["--version"]);
  if (res.status !== 0 || res.error) {
    return {
      valid: false,
      version: null,
      error: "Node.js is not installed or not in PATH.",
    };
  }

  const match = res.stdout.match(/v?(\d+)\.(\d+)\.(\d+)/);
  if (!match) {
    return { valid: false, version: res.stdout, error: "Could not parse Node.js version." };
  }

  const major = parseInt(match[1], 10);
  if (major < 18) {
    return {
      valid: false,
      version: res.stdout,
      error: `Node.js version ${res.stdout} is below required minimum version 18.0.0`,
    };
  }

  return { valid: true, version: res.stdout };
}

/**
 * Checks npm installation.
 */
function checkNpm() {
  const npmCmd = IS_WIN ? "npm.cmd" : "npm";
  const res = execCommand(npmCmd, ["--version"]);
  if (res.status !== 0 || res.error) {
    return { valid: false, cmd: npmCmd, error: "npm is not installed." };
  }
  return { valid: true, cmd: npmCmd, version: res.stdout };
}

/**
 * Checks Git installation.
 */
function checkGit() {
  const res = execCommand("git", ["--version"]);
  if (res.status !== 0 || res.error) {
    return { valid: false, error: "Git is not installed." };
  }
  return { valid: true, version: res.stdout };
}

/**
 * Comprehensive environment check runner.
 */
function checkAllEnv(options = {}) {
  logger.step("Checking system environment & prerequisites...");

  const results = {
    valid: true,
    python: null,
    venv: null,
    node: null,
    npm: null,
    git: null,
    errors: [],
  };

  // 1. Python check
  const pythonRes = findPython();
  results.python = pythonRes;
  if (!pythonRes.valid) {
    results.valid = false;
    results.errors.push(pythonRes.error);
    logger.error(`Python: ${pythonRes.error}`);
  } else {
    logger.success(`Python: ${pythonRes.version} (${pythonRes.cmd.join(" ")})`);
    // Check venv
    const venvRes = checkVenv(pythonRes.cmd);
    results.venv = venvRes;
    if (!venvRes.valid) {
      results.valid = false;
      results.errors.push(venvRes.error);
      logger.error(`Python venv: ${venvRes.error}`);
    } else {
      logger.success("Python venv module available");
    }
  }

  // 2. Node.js check
  const nodeRes = checkNode();
  results.node = nodeRes;
  if (!nodeRes.valid) {
    results.valid = false;
    results.errors.push(nodeRes.error);
    logger.error(`Node.js: ${nodeRes.error}`);
  } else {
    logger.success(`Node.js: ${nodeRes.version}`);
  }

  // 3. npm check
  const npmRes = checkNpm();
  results.npm = npmRes;
  if (!npmRes.valid) {
    results.valid = false;
    results.errors.push(npmRes.error);
    logger.error(`npm: ${npmRes.error}`);
  } else {
    logger.success(`npm: v${npmRes.version}`);
  }

  // 4. Git check
  const gitRes = checkGit();
  results.git = gitRes;
  if (!gitRes.valid) {
    if (options.isLocalRepo) {
      logger.warn("Git is not installed, but using local source directory.");
    } else {
      results.valid = false;
      results.errors.push(gitRes.error);
      logger.error(`Git: ${gitRes.error}`);
    }
  } else {
    logger.success(`Git: ${gitRes.version}`);
  }

  if (!results.valid) {
    logger.warn("\nSystem prerequisite check failed. Please resolve the following issues:");
    results.errors.forEach((err, idx) => {
      logger.dim(`  ${idx + 1}. ${err}`);
    });
    logger.info("\nInstallation Instructions:");
    if (!results.python.valid) {
      logger.dim("  • Python 3.8+: Download from https://www.python.org/downloads/ (check 'Add to PATH' on Windows)");
    }
    if (results.venv && !results.venv.valid) {
      logger.dim("  • Python venv: Run 'sudo apt install python3-venv' (Ubuntu/Debian)");
    }
    if (!results.node.valid) {
      logger.dim("  • Node.js 18+: Download from https://nodejs.org/");
    }
    if (!results.git.valid && !options.isLocalRepo) {
      logger.dim("  • Git: Download from https://git-scm.com/");
    }
  }

  return results;
}

module.exports = {
  findPython,
  checkVenv,
  checkNode,
  checkNpm,
  checkGit,
  checkAllEnv,
};
