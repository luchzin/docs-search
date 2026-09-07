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
DEBUG_FORCE_FAIL = False  # set True to force every managed subprocess call to fail (for testing error paths)
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


def get_python_cmd():
    """
    Find a real Python interpreter to run manage.py / pip with.

    CRITICAL: never use sys.executable when this launcher itself has been
    frozen (PyInstaller/py2exe/etc). In a frozen build, sys.executable
    points at THIS launcher's own .exe, not at a Python interpreter — so
    calling it re-spawns another copy of this GUI instead of running
    Django/pip. That's the "new same window on each step" bug.

    Returns a list (command prefix), e.g. ["C:\\Python311\\python.exe"]
    or ["py", "-3"], never a bare string — some valid interpreters
    (the Windows `py` launcher) are two tokens, not one.
    """
    if not getattr(sys, "frozen", False):
        # Running as a normal .py script — sys.executable really is python.
        return [sys.executable]

    candidates = []

    if sys.platform.startswith("win"):
        # The `py` launcher is the most reliable way to find a real
        # Windows Python install and isn't affected by the WindowsApps
        # alias-stub problem below.
        py_launcher = shutil.which("py")
        if py_launcher:
            candidates.append([py_launcher, "-3"])
        candidates.append(["python"])
        candidates.append(["python3"])
    else:
        candidates.append(["python3"])
        candidates.append(["python"])

    for cmd in candidates:
        resolved = _resolve_and_validate_python(cmd)
        if resolved:
            return resolved

    return None


def _resolve_and_validate_python(cmd):
    """
    Resolve the first token of `cmd` via PATH and actually execute
    `cmd --version` to confirm it's a real interpreter.

    This specifically guards against the Windows "App execution alias"
    stubs at %USERPROFILE%\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe
    and python3.exe. Those exist on PATH by default on a clean Windows
    install, shutil.which() happily finds them, but running them just
    prints "Python was not found; run without arguments to install from
    the Microsoft Store..." and exits with code 9009 — silently breaking
    any code that trusts `which` alone.
    """
    exe = shutil.which(cmd[0])
    if not exe:
        return None

    # Reject the known Microsoft Store alias-stub location outright,
    # even if it happens to pass the --version probe on some systems.
    if sys.platform.startswith("win") and "WindowsApps" in exe:
        return None

    try:
        probe = [exe] + cmd[1:] + ["--version"]
        creationflags = 0
        if sys.platform.startswith("win"):
            creationflags = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(
            probe,
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=creationflags,
            startupinfo=get_startupinfo(),
        )
        combined = (result.stdout or "") + (result.stderr or "")
        if result.returncode == 0 and "python" in combined.lower():
            return [exe] + cmd[1:]
    except Exception:
        pass

    return None


def get_startupinfo():
    """Configure subprocess startup info to hide terminal windows on Windows."""
    if sys.platform.startswith("win"):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        return si
    return None


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

        # Set initial ready status (Waiting for user click, NO auto-start)
        self.set_status("Ready. Click Launch to start.")

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
            text="Status: Ready",
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
        """Executes a command silently in the background and registers the process."""
        if self.is_closing:
            return False

        if DEBUG_FORCE_FAIL:
            self.log(
                f"[DEBUG_FORCE_FAIL] Skipping and failing: "
                f"{' '.join(cmd) if isinstance(cmd, list) else cmd}"
            )
            return False

        creationflags = 0
        if sys.platform.startswith("win"):
            creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

        popen_kwargs = {
            "cwd": cwd,
            "shell": shell,
            "creationflags": creationflags,
            "startupinfo": get_startupinfo(),
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "bufsize": 1,
        }

        cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd

        try:
            p = subprocess.Popen(cmd, **popen_kwargs)
            with self.process_lock:
                self.active_processes.append(p)

            # Capture output as it streams so we can show it on failure,
            # without ever swallowing it into DEVNULL.
            output_lines = []

            def _drain():
                try:
                    for line in iter(p.stdout.readline, ""):
                        output_lines.append(line.rstrip())
                    p.stdout.close()
                except Exception:
                    pass

            drain_thread = threading.Thread(target=_drain, daemon=True)
            drain_thread.start()

            # Wait for process while checking for closure
            while p.poll() is None:
                if self.is_closing:
                    self._kill_process(p)
                    return False
                time.sleep(0.1)

            drain_thread.join(timeout=2)

            with self.process_lock:
                if p in self.active_processes:
                    self.active_processes.remove(p)

            if p.returncode != 0:
                self.log(f"❌ Command failed ({cmd_str}) — exit code {p.returncode}")
                tail = output_lines[-25:] if len(output_lines) > 25 else output_lines
                for line in tail:
                    if line.strip():
                        self.log(f"    {line}")

            return p.returncode == 0
        except Exception as e:
            self.log(f"Command error ({cmd_str}): {e}")
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

        py_cmd = get_python_cmd()
        if not py_cmd:
            return False

        try:
            res = subprocess.run(
                py_cmd + ["-c", "import django; import rest_framework"],
                capture_output=True,
            )
            if res.returncode != 0:
                return False
        except Exception:
            return False

        return True

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
                self.is_running = True
                self.update_button(tk.NORMAL, "⏹️ Stop RAG Application")
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

            # 3. Resolve a real Python interpreter (never sys.executable if frozen)
            py_cmd = get_python_cmd()
            if not py_cmd:
                self.log(
                    "❌ No working Python interpreter found. Install Python 3 from "
                    "https://python.org (check 'Add to PATH' during install), or if "
                    "Python is already installed, disable the fake launcher at "
                    "Settings > Apps > Advanced app settings > App execution aliases "
                    "(turn OFF 'python.exe' and 'python3.exe')."
                )
                self.set_status("Error: Python Missing")
                return False
            self.log(f"✅ Using Python: {' '.join(py_cmd)}")

            # 4. Install Django dependencies
            self.set_status("Installing RAG Backend dependencies...")
            req_file = os.path.join(TARGET_DIR, "requirements.txt")
            if os.path.exists(req_file):
                self.log("Installing backend requirements...")
                if not self.run_command_managed(
                    py_cmd + ["-m", "pip", "install", "-r", req_file], cwd=TARGET_DIR
                ):
                    return False

            if self.is_closing:
                return False

            # Run migrations
            self.log("Running RAG database migrations...")
            if not self.run_command_managed(py_cmd + ["manage.py", "migrate"], cwd=TARGET_DIR):
                return False

            if self.is_closing:
                return False

            # 5. Install Frontend dependencies
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

        py_cmd = get_python_cmd()
        if not py_cmd:
            self.log(
                "❌ No working Python interpreter found. Install Python 3 from "
                "https://python.org (check 'Add to PATH' during install), or if "
                "Python is already installed, disable the fake launcher at "
                "Settings > Apps > Advanced app settings > App execution aliases "
                "(turn OFF 'python.exe' and 'python3.exe')."
            )
            self.set_status("Error: Python Missing")
            self.is_running = False
            self.update_button(tk.NORMAL, "🚀 Launch RAG Application")
            return

        npm_bin = get_npm_cmd()
        creationflags = 0
        if sys.platform.startswith("win"):
            creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

        popen_kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "bufsize": 1,
            "creationflags": creationflags,
            "startupinfo": get_startupinfo(),
        }

        try:
            # 1. Spawn Django Backend Server (Port 8000) - Completely hidden
            django_cmd = py_cmd + ["manage.py", "runserver", "8000"]
            self.log(f"Starting Django RAG API Server: {' '.join(django_cmd)}")
            p1 = subprocess.Popen(django_cmd, cwd=TARGET_DIR, **popen_kwargs)
            with self.process_lock:
                self.active_processes.append(p1)
            threading.Thread(target=self._read_stream, args=(p1, "Django API"), daemon=True).start()

            if self.is_closing:
                self.stop_servers()
                return

            # 2. Spawn Frontend Server (Vite) - Completely hidden
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
                    subprocess.call(
                        ["taskkill", "/F", "/T", "/PID", str(p.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
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
    # Defensive guard: if this file is ever frozen (PyInstaller) and somehow
    # invoked with extra args (e.g. by a broken subprocess call elsewhere),
    # bail instead of opening another GUI window.
    if getattr(sys, "frozen", False) and len(sys.argv) > 1:
        sys.exit(0)

    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()