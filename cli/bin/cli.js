#!/usr/bin/env node

const { main } = require("../src/index");

main().catch((err) => {
  console.error("Unhandled CLI Error:", err);
  process.exit(1);
});
