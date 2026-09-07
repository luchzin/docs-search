import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import webbrowser
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# --- CONFIGURATION ---
REPO_URL = "https://github.com/luchzin/docs-search"

# Determine target directory: use script's directory if manage.py is present, otherwise ~/docs-search
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(SCRIPT_DIR, "manage.py")):
    TARGET_DIR = SCRIPT_DIR
else:
    TARGET_DIR = os.path.join(os.path.expanduser("~"), "docs-search")

FRONTEND_DIR = os.path.join(TARGET_DIR, "frontend")
LAUNCH_URL = "http://localhost:5173"
BROWSER_DELAY_SEC = 4
# ---------------------


def is_git_installed():
    return shutil.which("git") is not None


def install_git(log_callback=print):
    """Attempt to install Git based on the host OS."""
    log_callback("Git is not detected. Attempting to install Git automatically...")
    try:
        if sys.platform.startswith("win"):
            log_callback("Running: winget install --id Git.Git -e --source winget")
            res = subprocess.run(
                ["winget", "install", "--id", "Git.Git", "-e", "--source", "winget"],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                log_callback("winget failed. Trying choco...")
                subprocess.run(["choco", "install", "git", "-y"], check=True)
        elif sys.platform.startswith("darwin"):
            if shutil.which("brew"):
                log_callback("Running: brew install git")
                subprocess.run(["brew", "install", "git"], check=True)
            else:
                log_callback("Running: xcode-select --install")
                subprocess.run(["xcode-select", "--install"], check=True)
        elif sys.platform.startswith("linux"):
            log_callback("Running: sudo apt-get update && sudo apt-get install -y git")
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "git"], check=True)
    except Exception as e:
        log_callback(f"Auto-install git encountered an error: {e}")

    if is_git_installed():
        log_callback("Git successfully installed!")
        return True
    else:
        log_callback(
            "Could not install Git automatically. Please install Git manually from https://git-scm.com/downloads"
        )
        return False


def get_npm_cmd():
    """Find npm executable across platforms."""
    npm_path = shutil.which("npm")
    if npm_path:
        return npm_path
    if sys.platform.startswith("win"):
        return "npm.cmd"
    return "npm"


class AppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Docs Search - RAG AI Assistant")
        self.root.geometry("720x540")
        self.root.minsize(600, 400)

        # Track child processes & status
        self.processes = []
        self.is_running = False

        self.create_widgets()

        # Handle app close event to kill lingering child servers
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Auto-launch RAG app on load
        self.root.after(600, self.auto_start_flow)

    def create_widgets(self):
        # Header / Title Banner Frame
        header_frame = ttk.Frame(self.root, padding=(15, 10, 15, 5))
        header_frame.pack(fill=tk.X)

        title_label = ttk.Label(
            header_frame,
            text="🤖 RAG AI Document Search Engine",
            font=("Helvetica", 14, "bold"),
        )
        title_label.pack(anchor=tk.W)

        sub_label = ttk.Label(
            header_frame,
            text="Automated Desktop Knowledge Base & Neural Search System",
            font=("Helvetica", 9),
        )
        sub_label.pack(anchor=tk.W, pady=(2, 0))

        # Divider line
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=15, pady=8)

        # Main Control Bar Frame (Single Launch/Stop Button + Status)
        ctrl_frame = ttk.Frame(self.root, padding=(15, 5, 15, 10))
        ctrl_frame.pack(fill=tk.X)

        # Single primary button for launch / stop toggle
        self.btn_main = ttk.Button(
            ctrl_frame,
            text="🚀 Launch RAG Application",
            command=self.toggle_rag_app,
            width=28,
        )
        self.btn_main.pack(side=tk.LEFT, padx=(0, 10))

        self.status_label = ttk.Label(
            ctrl_frame,
            text="Status: Initializing...",
            font=("Helvetica", 10, "italic"),
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Console Log Area
        log_frame = ttk.Frame(self.root, padding=(15, 0, 15, 15))
        log_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            log_frame,
            text="System Activity Log:",
            font=("Helvetica", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 4))

        self.log_box = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            bg="#111827",
            fg="#F3F4F6",
            insertbackground="white",
            font=("Menlo", 9) if sys.platform.startswith("darwin") else ("Consolas", 9),
            bd=1,
            relief=tk.SUNKEN,
        )
        self.log_box.pack(fill=tk.BOTH, expand=True)

    def log(self, text):
        """Thread-safe logging into the text area."""
        def _write():
            self.log_box.insert(tk.END, text + "\n")
            self.log_box.see(tk.END)
        self.root.after(0, _write)

    def set_status(self, text):
        """Update the status label safely from any thread."""
        self.root.after(0, lambda: self.status_label.config(text=f"Status: {text}"))

    def check_all_ready(self):
        """Check if repo and all dependencies are already installed."""
        manage_py = os.path.join(TARGET_DIR, "manage.py")
        if not os.path.exists(manage_py):
            return False

        node_modules = os.path.join(FRONTEND_DIR, "node_modules")
        if not os.path.exists(node_modules):
            return False

        try:
            res = subprocess.run(
                [sys.executable, "-c", "import django; import rest_framework"],
                capture_output=True,
            )
            if res.returncode != 0:
                return False
        except Exception:
            return False

        return True

    def auto_start_flow(self):
        """Automatically checks readiness and launches on app startup."""
        if self.check_all_ready():
            self.log("✨ All RAG dependencies and repository components are ready!")
            self.log("🚀 Instantly starting servers & launching RAG assistant...")
            self.start_servers_thread()
        else:
            self.log("📦 Setup required. Starting RAG setup and engine launch...")
            self.start_full_flow_thread()

    def toggle_rag_app(self):
        """Single button action: launches RAG app if stopped, stops it if running."""
        if self.is_running:
            self.stop_servers()
        else:
            if self.check_all_ready():
                self.start_servers_thread()
            else:
                self.start_full_flow_thread()

    def start_full_flow_thread(self):
        self.btn_main.config(state=tk.DISABLED, text="⏳ Setting up RAG...")
        threading.Thread(target=self._run_full_flow, daemon=True).start()

    def _run_full_flow(self):
        try:
            if not self._run_setup():
                self.log("❌ Setup failed. Stopping launch.")
                self.root.after(0, lambda: self.btn_main.config(state=tk.NORMAL, text="🚀 Launch RAG Application"))
                return
            self._start_servers()
        except Exception as e:
            self.log(f"❌ Error during launch flow: {e}")
            self.root.after(0, lambda: self.btn_main.config(state=tk.NORMAL, text="🚀 Launch RAG Application"))

    def _run_setup(self):
        try:
            self.set_status("Checking Git & Repository...")

            # 1. Check / Install Git
            if not is_git_installed():
                if not install_git(log_callback=self.log):
                    self.log("⚠️ Git is missing, but proceeding with local files if available...")
            else:
                self.log("✅ Git environment verified.")

            # 2. Clone or verify Repo
            if not os.path.exists(os.path.join(TARGET_DIR, "manage.py")):
                if not is_git_installed():
                    self.log("❌ Cannot clone repo: Git is not installed.")
                    self.set_status("Error: Git Missing")
                    return False
                self.log(f"Cloning RAG codebase into {TARGET_DIR}...")
                subprocess.run(["git", "clone", REPO_URL, TARGET_DIR], check=True)
            else:
                self.log(f"RAG codebase present at {TARGET_DIR}.")
                if is_git_installed() and os.path.exists(os.path.join(TARGET_DIR, ".git")):
                    try:
                        self.log("Fetching latest RAG updates...")
                        subprocess.run(["git", "-C", TARGET_DIR, "pull"], check=False)
                    except Exception as e:
                        self.log(f"git pull notice: {e}")

            # 3. Install Django dependencies
            self.set_status("Installing RAG Backend dependencies...")
            req_file = os.path.join(TARGET_DIR, "requirements.txt")
            if os.path.exists(req_file):
                self.log("Installing backend requirements...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", req_file],
                    cwd=TARGET_DIR,
                    check=True,
                )

            # Run migrations
            self.log("Running RAG database migrations...")
            subprocess.run([sys.executable, "manage.py", "migrate"], cwd=TARGET_DIR, check=True)

            # 4. Install Frontend dependencies
            self.set_status("Installing RAG Frontend dependencies...")
            npm_bin = get_npm_cmd()
            if os.path.exists(FRONTEND_DIR):
                if not os.path.exists(os.path.join(FRONTEND_DIR, "node_modules")):
                    self.log("Installing frontend packages (npm install)...")
                    subprocess.run(
                        [npm_bin, "install"],
                        cwd=FRONTEND_DIR,
                        check=True,
                        shell=sys.platform.startswith("win"),
                    )
                else:
                    self.log("Frontend packages (node_modules) already present.")
            else:
                self.log(f"⚠️ Frontend directory missing at {FRONTEND_DIR}")

            self.log("🎉 Setup complete!")
            self.set_status("Setup Complete")
            return True

        except Exception as e:
            self.log(f"❌ Setup Error: {e}")
            self.set_status("Error during setup")
            return False

    def start_servers_thread(self):
        if not os.path.exists(os.path.join(TARGET_DIR, "manage.py")):
            messagebox.showwarning("Warning", "Repository not found. Setup is required.")
            return

        if self.is_running:
            self.log("RAG Application servers are already active.")
            return

        self.is_running = True
        self.set_status("Starting RAG Engine...")
        self.root.after(0, lambda: self.btn_main.config(state=tk.NORMAL, text="⏹️ Stop RAG Application"))

        threading.Thread(target=self._start_servers, daemon=True).start()

    def _start_servers(self):
        npm_bin = get_npm_cmd()
        popen_kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "bufsize": 1,
            "creationflags": (
                subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform.startswith("win") else 0
            ),
            "preexec_fn": os.setsid if not sys.platform.startswith("win") else None,
        }

        try:
            # 1. Spawn Django Backend Server (Port 8000)
            django_cmd = [sys.executable, "manage.py", "runserver", "8000"]
            self.log(f"Starting Django RAG API Server: {' '.join(django_cmd)}")
            p1 = subprocess.Popen(django_cmd, cwd=TARGET_DIR, **popen_kwargs)
            self.processes.append(p1)
            threading.Thread(target=self._read_stream, args=(p1, "Django API"), daemon=True).start()

            # 2. Spawn Frontend Server (Vite)
            frontend_cmd = [npm_bin, "run", "dev"]
            self.log(f"Starting Vue RAG Frontend Server: {' '.join(frontend_cmd)}")
            p2 = subprocess.Popen(
                frontend_cmd,
                cwd=FRONTEND_DIR,
                shell=sys.platform.startswith("win"),
                **popen_kwargs,
            )
            self.processes.append(p2)
            threading.Thread(target=self._read_stream, args=(p2, "Frontend"), daemon=True).start()

            # 3. Wait for servers to start, then launch browser
            self.set_status("RAG Engine Active")
            self.log(f"Waiting {BROWSER_DELAY_SEC}s for RAG engine initialization...")
            time.sleep(BROWSER_DELAY_SEC)

            if self.is_running:
                self.log(f"🌐 Opening browser for RAG Search at: {LAUNCH_URL}")
                webbrowser.open(LAUNCH_URL)

        except Exception as e:
            self.log(f"❌ Error starting servers: {e}")
            self.stop_servers()

    def _read_stream(self, proc, prefix):
        """Continuously pipe stdout/stderr to the log box."""
        for line in iter(proc.stdout.readline, ""):
            if not self.is_running:
                break
            self.log(f"[{prefix}] {line.strip()}")
        proc.stdout.close()

    def stop_servers(self):
        """Cleanly terminate both servers and processes."""
        self.is_running = False
        self.log("Stopping RAG application servers...")

        for p in self.processes:
            try:
                if sys.platform.startswith("win"):
                    subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)])
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception:
                pass

        self.processes.clear()
        self.set_status("Stopped")
        self.root.after(0, lambda: self.btn_main.config(state=tk.NORMAL, text="🚀 Launch RAG Application"))
        self.log("All RAG servers stopped.")

    def on_close(self):
        """Ensure processes are killed when window is closed."""
        self.stop_servers()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()