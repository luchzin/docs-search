const chalkModule = require("chalk");
const chalk = chalkModule.default || chalkModule;

const logger = {
  info(msg) {
    console.log(`${chalk.cyanBright.bold("ℹ")} ${chalk.cyan(msg)}`);
  },

  success(msg) {
    console.log(`${chalk.greenBright.bold("✔")} ${chalk.greenBright(msg)}`);
  },

  warn(msg) {
    console.warn(`${chalk.yellowBright.bold("⚠")} ${chalk.yellow(msg)}`);
  },

  error(msg) {
    console.error(`${chalk.redBright.bold("✖")} ${chalk.red(msg)}`);
  },

  step(msg) {
    console.log(
      `\n${chalk.magentaBright.bold("➜")} ${chalk.magenta.bold(msg)}`,
    );
  },

  dim(msg) {
    console.log(chalk.gray(msg));
  },

  banner() {
    const text = "Docs Search RAG Application CLI Manager";
    const palette = [
      chalk.redBright.bold,
      chalk.yellowBright.bold,
      chalk.greenBright.bold,
      chalk.cyanBright.bold,
      chalk.blueBright.bold,
      chalk.magentaBright.bold,
    ];

    let colorIdx = 0;
    const title = text
      .split("")
      .map((char) => {
        // Don't advance the color cycle on spaces
        if (char === " ") return " ";
        const style = palette[colorIdx % palette.length];
        colorIdx++;
        return style(char);
      })
      .join("");

    const divider = chalk.bold.hex("#00D2FF")(
      "=====================================================",
    );
    console.log(`\n${divider}\n   ${title}\n${divider}\n`);
  },
};

module.exports = logger;
