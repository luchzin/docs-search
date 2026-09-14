const isTTY = process.stdout.isTTY;

const colors = {
  reset: isTTY ? "\x1b[0m" : "",
  bold: isTTY ? "\x1b[1m" : "",
  dim: isTTY ? "\x1b[2m" : "",
  green: isTTY ? "\x1b[32m" : "",
  yellow: isTTY ? "\x1b[33m" : "",
  red: isTTY ? "\x1b[31m" : "",
  cyan: isTTY ? "\x1b[36m" : "",
  magenta: isTTY ? "\x1b[35m" : "",
};

const logger = {
  info(msg) {
    console.log(`${colors.cyan}ℹ${colors.reset} ${msg}`);
  },
  success(msg) {
    console.log(`${colors.green}✔${colors.reset} ${msg}`);
  },
  warn(msg) {
    console.warn(`${colors.yellow}⚠${colors.reset} ${msg}`);
  },
  error(msg) {
    console.error(`${colors.red}✖${colors.reset} ${msg}`);
  },
  step(msg) {
    console.log(`\n${colors.bold}${colors.magenta}➜${colors.reset} ${colors.bold}${msg}${colors.reset}`);
  },
  dim(msg) {
    console.log(`${colors.dim}${msg}${colors.reset}`);
  },
  banner() {
    console.log(`
${colors.cyan}${colors.bold}=====================================================${colors.reset}
${colors.bold}   📚 Docs Search RAG Application CLI Manager       ${colors.reset}
${colors.cyan}${colors.bold}=====================================================${colors.reset}
`);
  },
};

module.exports = logger;
