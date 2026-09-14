# Docs Search CLI (`docs-search-cli`)

Command-line tool to automatically check prerequisites, install, configure, and launch the **Docs Search RAG Application**.

## Features

- 🔍 **System Prerequisite Checks**: Automatically verifies Python (3.8+), Python `venv` module, Node.js (18+), npm, and Git. Rejects broken Windows App Execution Alias stubs.
- 🛠️ **Automated Setup**: Clones/updates repository, creates Python virtualenv, installs backend `requirements.txt`, runs Django database migrations, and installs Vue frontend dependencies.
- 🚀 **One-Command Launch**: Spawns both Django Backend API and Vue Frontend Dev servers, and automatically opens your web browser.
- 📦 **Modular Code Structure**: Clean separation of concerns (`env-checker`, `repo-manager`, `backend`, `frontend`, `logger`, `index`).

## Usage

### Run directly with `npx` (No installation needed)

```bash
npx docs-search-cli
```

### Or install globally via `npm`

```bash
npm install -g docs-search-cli
docs-search
```

## Available Commands & Options

```bash
npx docs-search-cli [command] [options]
```

### Commands

| Command | Description |
|---|---|
| `start` | Setup environment, install dependencies, run migrations & start servers (default) |
| `install` | Perform full installation and build without starting servers |
| `check` | Check system environment & prerequisites only |

### Options

| Flag | Short | Description | Default |
|---|---|---|---|
| `--port <port>` | `-p` | Backend API server port | `8000` |
| `--frontend-port <port>` | | Frontend dev server port | `5173` |
| `--dir <dir>` | `-d` | Target installation directory | `~/.docs-search` |
| `--skip-build` | | Skip Vue frontend build step | `false` |
| `--no-open` | | Do not launch web browser automatically | `false` |
| `--help` | `-h` | Display CLI help menu | |
| `--version` | `-v` | Display CLI version | |

## Project Architecture

```
cli/
├── bin/
│   └── cli.js            # Executable CLI entrypoint
├── src/
│   ├── env-checker.js    # Python, venv, Node, npm, Git prerequisite checks
│   ├── repo-manager.js   # Local codebase detection & remote repository cloning
│   ├── backend.js        # Virtualenv creation, pip dependencies, Django migrations
│   ├── frontend.js       # Vue npm dependencies, build, and dev server
│   ├── logger.js         # Colorized ANSI logger
│   └── index.js          # Main CLI orchestrator
└── package.json
```
