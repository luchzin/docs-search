const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawnSync } = require("child_process");
const logger = require("./logger");

const DEFAULT_REPO_URL = "https://github.com/luchzin/docs-search.git";
const DEFAULT_BRANCH = "main";
const IS_WIN = os.platform() === "win32";

function runGit(args, cwd) {
  const res = spawnSync("git", args, {
    cwd,
    stdio: "inherit",
    shell: IS_WIN,
  });
  if (res.status !== 0) {
    throw new Error(`Git command failed with exit code ${res.status}`);
  }
}

/**
 * Checks whether target directory contains a valid docs-search codebase.
 */
function isValidDocsSearchDir(dirPath) {
  if (!dirPath || !fs.existsSync(dirPath)) return false;
  const hasManagePy = fs.existsSync(path.join(dirPath, "manage.py"));
  const hasAppDir = fs.existsSync(path.join(dirPath, "app"));
  const hasFrontendDir = fs.existsSync(path.join(dirPath, "frontend"));
  return hasManagePy && hasAppDir && hasFrontendDir;
}

/**
 * Locates local codebase or clones/updates remote repository.
 */
function findOrFetchRepo(options = {}) {
  const cwd = process.cwd();
  
  // 1. Check if user is currently inside docs-search repo directory
  if (isValidDocsSearchDir(cwd)) {
    logger.info(`Using current directory codebase at: ${cwd}`);
    return { path: cwd, isLocal: true };
  }

  // 2. Determine target app directory
  const baseDir = options.dir || path.join(os.homedir(), ".docs-search");
  const repoDir = path.join(baseDir, "repo");
  fs.mkdirSync(baseDir, { recursive: true });

  if (isValidDocsSearchDir(repoDir)) {
    if (fs.existsSync(path.join(repoDir, ".git"))) {
      logger.step(`Updating existing repository in ${repoDir}...`);
      try {
        runGit(["fetch", "origin", DEFAULT_BRANCH], repoDir);
        runGit(["checkout", DEFAULT_BRANCH], repoDir);
        runGit(["reset", "--hard", `origin/${DEFAULT_BRANCH}`], repoDir);
        logger.success("Repository updated successfully.");
      } catch (err) {
        logger.warn(`Failed to update repo via Git: ${err.message}. Using cached codebase.`);
      }
    } else {
      logger.info(`Using cached codebase at: ${repoDir}`);
    }
  } else {
    logger.step(`Cloning repository from ${DEFAULT_REPO_URL}...`);
    runGit(
      ["clone", "--branch", DEFAULT_BRANCH, "--depth", "1", DEFAULT_REPO_URL, repoDir],
      baseDir
    );
    logger.success("Repository cloned successfully.");
  }

  return { path: repoDir, isLocal: false };
}

module.exports = {
  isValidDocsSearchDir,
  findOrFetchRepo,
};
