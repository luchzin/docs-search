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

        # Process management & execution flags
        self.active_processes = []
        self.process_lock = threading.Lock()
        self.is_running = False
        self.is_closing = False

        self.create_widgets()

        # Handle app close event to cleanly kill all child processes & threads
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Auto-launch RAG app on load after window renders
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
        """Thread-safe and shutdown-safe logging into the text area."""
        if self.is_closing:
            return

        def _write():
            try:
                if not self.is_closing and self.root.winfo_exists():
                    self.log_box.insert(tk.END, text + "\n")
                    self.log_box.see(tk.END)
            except Exception:
                pass

        try:
            self.root.after(0, _write)
        except Exception:
            pass

    def set_status(self, text):
        """Update the status label safely from any thread."""
        if self.is_closing:
            return

        def _update():
            try:
                if not self.is_closing and self.root.winfo_exists():
                    self.status_label.config(text=f"Status: {text}")
            except Exception:
                pass

        try:
            self.root.after(0, _update)
        except Exception:
            pass

    def update_button(self, state, text):
        """Update main button text and state safely."""
        if self.is_closing:
            return

        def _update():
            try:
                if not self.is_closing and self.root.winfo_exists():
                    self.btn_main.config(state=state, text=text)
            except Exception:
                pass

        try:
            self.root.after(0, _update)
        except Exception:
            pass

    def run_command_managed(self, cmd, cwd=None, shell=False):
        """Executes a command and registers the process so it can be cleanly killed on window exit."""
        if self.is_closing:
            return False

        popen_kwargs = {
            "cwd": cwd,
            "shell": shell,
            "creationflags": (
                subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform.startswith("win") else 0
            ),
            "preexec_fn": os.setsid if not sys.platform.startswith("win") else None,
        }

        try:
            p = subprocess.Popen(cmd, **popen_kwargs)
            with self.process_lock:
                self.active_processes.append(p)

            # Wait for process while checking for closure
            while p.poll() is None:
                if self.is_closing:
                    self._kill_process(p)
                    return False
                time.sleep(0.1)

            with self.process_lock:
                if p in self.active_processes:
                    self.active_processes.remove(p)

            return p.returncode == 0
        except Exception as e:
            self.log(f"Command error ({' '.join(cmd) if isinstance(cmd, list) else cmd}): {e}")
            return False

    def install_git_managed(self):
        """Attempt to install Git based on the host OS."""
        self.log("Git is not detected. Attempting to install Git automatically...")
        try:
            if sys.platform.startswith("win"):
                self.log("Running: winget install --id Git.Git -e --source winget")
                success = self.run_command_managed(
                    ["winget", "install", "--id", "Git.Git", "-e", "--source", "winget"]
                )
                if not success:
                    self.log("winget failed. Trying choco...")
                    self.run_command_managed(["choco", "install", "git", "-y"])
            elif sys.platform.startswith("darwin"):
                if shutil.which("brew"):
                    self.log("Running: brew install git")
                    self.run_command_managed(["brew", "install", "git"])
                else:
                    self.log("Running: xcode-select --install")
                    self.run_command_managed(["xcode-select", "--install"])
            elif sys.platform.startswith("linux"):
                self.log("Running: sudo apt-get update && sudo apt-get install -y git")
                self.run_command_managed(["sudo", "apt-get", "update"])
                self.run_command_managed(["sudo", "apt-get", "install", "-y", "git"])
        except Exception as e:
            self.log(f"Auto-install git encountered an error: {e}")

        if is_git_installed():
            self.log("Git successfully installed!")
            return True
        else:
            self.log(
                "Could not install Git automatically. Please install Git manually from https://git-scm.com/downloads"
            )
            return False

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
        if self.is_closing:
            return

        if self.check_all_ready():
            self.log("✨ All RAG dependencies and repository components are ready!")
            self.log("🚀 Instantly starting servers & launching RAG assistant...")
            self.start_servers_thread()
        else:
            self.log("📦 Setup required. Starting RAG setup and engine launch...")
            self.start_full_flow_thread()

    def toggle_rag_app(self):
        """Single button action: launches RAG app if stopped, stops it if running."""
        if self.is_closing:
            return

        if self.is_running:
            self.stop_servers()
        else:
            if self.check_all_ready():
                self.start_servers_thread()
            else:
                self.start_full_flow_thread()

    def start_full_flow_thread(self):
        if self.is_closing:
            return
        self.update_button(tk.DISABLED, "⏳ Setting up RAG...")
        threading.Thread(target=self._run_full_flow, daemon=True).start()

    def _run_full_flow(self):
        try:
            if self.is_closing or not self._run_setup():
                if not self.is_closing:
                    self.log("❌ Setup failed or cancelled. Stopping launch.")
                    self.update_button(tk.NORMAL, "🚀 Launch RAG Application")
                return
            if not self.is_closing:
                self._start_servers()
        except Exception as e:
            if not self.is_closing:
                self.log(f"❌ Error during launch flow: {e}")
                self.update_button(tk.NORMAL, "🚀 Launch RAG Application")

    def _run_setup(self):
        try:
            if self.is_closing:
                return False

            self.set_status("Checking Git & Repository...")

            # 1. Check / Install Git
            if not is_git_installed():
                if not self.install_git_managed():
                    self.log("⚠️ Git is missing, but proceeding with local files if available...")
            else:
                self.log("✅ Git environment verified.")

            if self.is_closing:
                return False

            # 2. Clone or verify Repo
            if not os.path.exists(os.path.join(TARGET_DIR, "manage.py")):
                if not is_git_installed():
                    self.log("❌ Cannot clone repo: Git is not installed.")
                    self.set_status("Error: Git Missing")
                    return False
                self.log(f"Cloning RAG codebase into {TARGET_DIR}...")
                if not self.run_command_managed(["git", "clone", REPO_URL, TARGET_DIR]):
                    return False
            else:
                self.log(f"RAG codebase present at {TARGET_DIR}.")
                if is_git_installed() and os.path.exists(os.path.join(TARGET_DIR, ".git")):
                    self.log("Fetching latest RAG updates...")
                    self.run_command_managed(["git", "-C", TARGET_DIR, "pull"])

            if self.is_closing:
                return False

            # 3. Install Django dependencies
            self.set_status("Installing RAG Backend dependencies...")
            req_file = os.path.join(TARGET_DIR, "requirements.txt")
            if os.path.exists(req_file):
                self.log("Installing backend requirements...")
                if not self.run_command_managed(
                    [sys.executable, "-m", "pip", "install", "-r", req_file], cwd=TARGET_DIR
                ):
                    return False

            if self.is_closing:
                return False

            # Run migrations
            self.log("Running RAG database migrations...")
            if not self.run_command_managed([sys.executable, "manage.py", "migrate"], cwd=TARGET_DIR):
                return False

            if self.is_closing:
                return False

            # 4. Install Frontend dependencies
            self.set_status("Installing RAG Frontend dependencies...")
            npm_bin = get_npm_cmd()
            if os.path.exists(FRONTEND_DIR):
                if not os.path.exists(os.path.join(FRONTEND_DIR, "node_modules")):
                    self.log("Installing frontend packages (npm install)...")
                    if not self.run_command_managed(
                        [npm_bin, "install"],
                        cwd=FRONTEND_DIR,
                        shell=sys.platform.startswith("win"),
                    ):
                        return False
                else:
                    self.log("Frontend packages (node_modules) already present.")
            else:
                self.log(f"⚠️ Frontend directory missing at {FRONTEND_DIR}")

            if self.is_closing:
                return False

            self.log("🎉 Setup complete!")
            self.set_status("Setup Complete")
            return True

        except Exception as e:
            self.log(f"❌ Setup Error: {e}")
            self.set_status("Error during setup")
            return False

    def start_servers_thread(self):
        if self.is_closing:
            return

        if not os.path.exists(os.path.join(TARGET_DIR, "manage.py")):
            messagebox.showwarning("Warning", "Repository not found. Setup is required.")
            return

        if self.is_running:
            self.log("RAG Application servers are already active.")
            return

        self.is_running = True
        self.set_status("Starting RAG Engine...")
        self.update_button(tk.NORMAL, "⏹️ Stop RAG Application")

        threading.Thread(target=self._start_servers, daemon=True).start()

    def _start_servers(self):
        if self.is_closing:
            return

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
            with self.process_lock:
                self.active_processes.append(p1)
            threading.Thread(target=self._read_stream, args=(p1, "Django API"), daemon=True).start()

            if self.is_closing:
                self.stop_servers()
                return

            # 2. Spawn Frontend Server (Vite)
            frontend_cmd = [npm_bin, "run", "dev"]
            self.log(f"Starting Vue RAG Frontend Server: {' '.join(frontend_cmd)}")
            p2 = subprocess.Popen(
                frontend_cmd,
                cwd=FRONTEND_DIR,
                shell=sys.platform.startswith("win"),
                **popen_kwargs,
            )
            with self.process_lock:
                self.active_processes.append(p2)
            threading.Thread(target=self._read_stream, args=(p2, "Frontend"), daemon=True).start()

            # 3. Wait for servers to start, periodically checking for shutdown
            self.set_status("RAG Engine Active")
            self.log(f"Waiting {BROWSER_DELAY_SEC}s for RAG engine initialization...")

            for _ in range(int(BROWSER_DELAY_SEC * 10)):
                if self.is_closing or not self.is_running:
                    return
                time.sleep(0.1)

            if self.is_running and not self.is_closing:
                self.log(f"🌐 Opening browser for RAG Search at: {LAUNCH_URL}")
                webbrowser.open(LAUNCH_URL)

        except Exception as e:
            if not self.is_closing:
                self.log(f"❌ Error starting servers: {e}")
                self.stop_servers()

    def _read_stream(self, proc, prefix):
        """Continuously pipe stdout/stderr to the log box safely."""
        try:
            for line in iter(proc.stdout.readline, ""):
                if self.is_closing or not self.is_running:
                    break
                self.log(f"[{prefix}] {line.strip()}")
            proc.stdout.close()
        except Exception:
            pass

    def _kill_process(self, p):
        """Safely terminate a child process and its process group."""
        try:
            if p.poll() is None:
                if sys.platform.startswith("win"):
                    subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)])
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except Exception:
            pass

    def stop_servers(self):
        """Cleanly terminate all servers and child processes."""
        self.is_running = False
        self.log("Stopping RAG application servers & background processes...")

        with self.process_lock:
            for p in list(self.active_processes):
                self._kill_process(p)
            self.active_processes.clear()

        self.set_status("Stopped")
        self.update_button(tk.NORMAL, "🚀 Launch RAG Application")
        self.log("All RAG servers stopped.")

    def on_close(self):
        """Ensure all child processes & threads are terminated immediately when window is closed."""
        self.is_closing = True
        self.is_running = False

        # Kill all running child processes immediately
        with self.process_lock:
            for p in list(self.active_processes):
                self._kill_process(p)
            self.active_processes.clear()

        try:
            self.root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()