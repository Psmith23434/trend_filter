"""
Trend Filter — GUI Launcher
Run with:  python gui.py
Requires:  Python 3.9+  (tkinter is part of the standard library)
"""
from __future__ import annotations

import os
import sys
import subprocess
import threading
import webbrowser
import time
import queue
import platform
import urllib.request
import urllib.error
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent.resolve()
API_URL    = "http://127.0.0.1:8000"
DASH_URL   = f"{API_URL}/dashboard/"
SCAN_URL   = f"{API_URL}/scan"
HEALTH_URL = f"{API_URL}/health"
PYTHON     = sys.executable          # same Python that's running this script

# Colours
COL_BG      = "#1a1a2e"
COL_SURFACE = "#16213e"
COL_CARD    = "#0f3460"
COL_ACCENT  = "#00b4d8"
COL_GREEN   = "#06d6a0"
COL_RED     = "#ef233c"
COL_AMBER   = "#f4a261"
COL_TEXT    = "#e0e0e0"
COL_MUTED   = "#8a8a9a"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _server_alive() -> bool:
    """Return True if the FastAPI server is responding."""
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


# ── Main App ───────────────────────────────────────────────────────────────────

class TrendFilterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trend Filter")
        self.geometry("860x620")
        self.minsize(760, 520)
        self.configure(bg=COL_BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._server_proc: subprocess.Popen | None = None
        self._log_queue: queue.Queue = queue.Queue()
        self._poll_id = None

        self._build_ui()
        self._update_status()
        self._drain_log_queue()  # start periodic log flush

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Top bar ──
        top = tk.Frame(self, bg=COL_SURFACE, pady=8)
        top.pack(fill="x")

        tk.Label(top, text="📡  Trend Filter", font=("Segoe UI", 16, "bold"),
                 bg=COL_SURFACE, fg=COL_ACCENT).pack(side="left", padx=16)

        self._status_dot = tk.Label(top, text="●", font=("Segoe UI", 18),
                                     bg=COL_SURFACE, fg=COL_RED)
        self._status_dot.pack(side="right", padx=6)
        self._status_lbl = tk.Label(top, text="Server: offline",
                                     font=("Segoe UI", 10), bg=COL_SURFACE,
                                     fg=COL_MUTED)
        self._status_lbl.pack(side="right", padx=4)

        # ── Button row ──
        btn_row = tk.Frame(self, bg=COL_BG, pady=10)
        btn_row.pack(fill="x", padx=16)

        self._btn_start = self._btn(btn_row, "▶  Start Server",  COL_GREEN,  self._start_server)
        self._btn_start.pack(side="left", padx=(0, 8))

        self._btn_stop = self._btn(btn_row, "■  Stop Server",   COL_RED,    self._stop_server)
        self._btn_stop.pack(side="left", padx=(0, 8))
        self._btn_stop.configure(state="disabled")

        self._btn_scan = self._btn(btn_row, "🔍  Run Scan",      COL_ACCENT, self._run_scan)
        self._btn_scan.pack(side="left", padx=(0, 8))
        self._btn_scan.configure(state="disabled")

        self._btn_dash = self._btn(btn_row, "🌐  Open Dashboard", COL_AMBER,  self._open_dashboard)
        self._btn_dash.pack(side="left", padx=(0, 8))
        self._btn_dash.configure(state="disabled")

        tk.Button(btn_row, text="🔄  git pull",
                  font=("Segoe UI", 10), bg=COL_CARD, fg=COL_TEXT,
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  activebackground=COL_SURFACE, activeforeground=COL_TEXT,
                  command=self._git_pull).pack(side="left", padx=(0, 8))

        # ── Scan progress bar ──
        self._progress_var = tk.IntVar(value=0)
        self._progress = ttk.Progressbar(self, variable=self._progress_var,
                                          mode="indeterminate", length=200)
        # (packed on demand)

        # ── Tabs ──
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self._style_notebook(nb)

        # Tab 1 — Server log
        log_frame = tk.Frame(nb, bg=COL_BG)
        nb.add(log_frame, text="  Server Log  ")
        self._log = scrolledtext.ScrolledText(
            log_frame, bg="#0d0d1a", fg=COL_TEXT,
            font=("Consolas", 9), relief="flat", wrap="word",
            insertbackground=COL_ACCENT, state="disabled")
        self._log.pack(fill="both", expand=True, padx=4, pady=4)
        self._log.tag_config("info",    foreground=COL_ACCENT)
        self._log.tag_config("ok",      foreground=COL_GREEN)
        self._log.tag_config("warn",    foreground=COL_AMBER)
        self._log.tag_config("error",   foreground=COL_RED)
        self._log.tag_config("muted",   foreground=COL_MUTED)

        tk.Button(log_frame, text="Clear log", font=("Segoe UI", 8),
                  bg=COL_CARD, fg=COL_MUTED, relief="flat", padx=8, pady=3,
                  cursor="hand2", command=self._clear_log).pack(anchor="e", padx=4, pady=(0, 4))

        # Tab 2 — Settings
        cfg_frame = tk.Frame(nb, bg=COL_BG)
        nb.add(cfg_frame, text="  Settings  ")
        self._build_settings(cfg_frame)

    def _btn(self, parent, text, colour, cmd):
        return tk.Button(parent, text=text,
                         font=("Segoe UI", 10, "bold"),
                         bg=colour, fg="#ffffff" if colour != COL_AMBER else "#1a1a2e",
                         relief="flat", padx=14, pady=7, cursor="hand2",
                         activebackground=colour, activeforeground="white",
                         command=cmd)

    def _style_notebook(self, nb):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",          background=COL_BG,      borderwidth=0)
        style.configure("TNotebook.Tab",      background=COL_CARD,    foreground=COL_MUTED,
                         padding=[12, 6],     font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", COL_SURFACE)],
                  foreground=[("selected", COL_ACCENT)])
        style.configure("TProgressbar",        troughcolor=COL_CARD,  background=COL_ACCENT)

    def _build_settings(self, parent):
        """Simple .env editor for key settings."""
        env_path = BASE_DIR / ".env"
        env_example = BASE_DIR / ".env.example"

        def _load():
            src = env_path if env_path.exists() else env_example
            return src.read_text(encoding="utf-8") if src.exists() else ""

        lbl = tk.Label(parent, text="Edit .env settings (saved to E:\\Projects\\Trend\\.env)",
                        font=("Segoe UI", 10, "bold"), bg=COL_BG, fg=COL_TEXT)
        lbl.pack(anchor="w", padx=12, pady=(12, 4))

        self._env_editor = scrolledtext.ScrolledText(
            parent, bg=COL_SURFACE, fg=COL_TEXT,
            font=("Consolas", 9), relief="flat",
            insertbackground=COL_ACCENT, height=18)
        self._env_editor.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self._env_editor.insert("1.0", _load())

        btn_row = tk.Frame(parent, bg=COL_BG)
        btn_row.pack(fill="x", padx=12, pady=(0, 12))
        tk.Button(btn_row, text="💾  Save .env",
                  font=("Segoe UI", 10), bg=COL_GREEN, fg="#111",
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._save_env).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="↺  Reload from file",
                  font=("Segoe UI", 10), bg=COL_CARD, fg=COL_TEXT,
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  command=lambda: (self._env_editor.delete("1.0", "end"),
                                   self._env_editor.insert("1.0", _load()))).pack(side="left")

    # ── Actions ────────────────────────────────────────────────────────────────

    def _start_server(self):
        if self._server_proc and self._server_proc.poll() is None:
            self._log_line("Server is already running.", "warn")
            return

        self._log_line("Starting uvicorn server...", "info")
        cmd = [PYTHON, "-m", "uvicorn", "api.main:app", "--reload",
               "--host", "127.0.0.1", "--port", "8000"]
        try:
            self._server_proc = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
            )
        except Exception as exc:
            self._log_line(f"Failed to start server: {exc}", "error")
            return

        # Stream server output to log in background thread
        threading.Thread(target=self._stream_proc, args=(self._server_proc,),
                         daemon=True).start()

        # Poll until server responds
        threading.Thread(target=self._wait_for_server, daemon=True).start()

    def _stream_proc(self, proc):
        for line in iter(proc.stdout.readline, ""):
            self._log_queue.put((line.rstrip(), "muted"))
        self._log_queue.put(("[Server process ended]", "warn"))
        self.after(0, self._update_status)

    def _wait_for_server(self):
        for _ in range(30):          # up to 15 seconds
            if _server_alive():
                self._log_queue.put(("✔ Server is online at http://127.0.0.1:8000", "ok"))
                self.after(0, self._update_status)
                return
            time.sleep(0.5)
        self._log_queue.put(("⚠ Server did not respond within 15 s — check log.", "warn"))
        self.after(0, self._update_status)

    def _stop_server(self):
        if not self._server_proc:
            return
        self._log_line("Stopping server...", "warn")
        try:
            self._server_proc.terminate()
            self._server_proc.wait(timeout=5)
        except Exception:
            try:
                self._server_proc.kill()
            except Exception:
                pass
        self._server_proc = None
        self._log_line("Server stopped.", "warn")
        self._update_status()

    def _run_scan(self):
        if not _server_alive():
            messagebox.showwarning("Server offline", "Start the server first.")
            return
        self._btn_scan.configure(state="disabled", text="⏳  Scanning...")
        self._progress.pack(fill="x", padx=16, pady=(0, 4))
        self._progress.start(12)
        self._log_line("POST /scan — running full pipeline (may take 1-3 min)...", "info")
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        import urllib.request, json, urllib.error
        try:
            req = urllib.request.Request(SCAN_URL, method="POST",
                                         headers={"Content-Length": "0"})
            with urllib.request.urlopen(req, timeout=300) as r:
                body = json.loads(r.read())
                count = sum(len(v) for v in body.get("grouped", {}).values())
                self._log_queue.put((f"✔ Scan complete — {count} trends found.", "ok"))
        except urllib.error.HTTPError as e:
            self._log_queue.put((f"✘ Scan failed HTTP {e.code}: {e.read().decode()[:300]}", "error"))
        except Exception as exc:
            self._log_queue.put((f"✘ Scan error: {exc}", "error"))
        finally:
            self.after(0, self._scan_done)

    def _scan_done(self):
        self._progress.stop()
        self._progress.pack_forget()
        self._btn_scan.configure(state="normal", text="🔍  Run Scan")

    def _open_dashboard(self):
        webbrowser.open(DASH_URL)

    def _git_pull(self):
        self._log_line("Running git pull...", "info")
        def _pull():
            try:
                result = subprocess.run(
                    ["git", "pull"],
                    cwd=str(BASE_DIR),
                    capture_output=True, text=True, timeout=30)
                out = result.stdout.strip() or result.stderr.strip()
                tag = "ok" if result.returncode == 0 else "error"
                self._log_queue.put((out, tag))
                if result.returncode == 0:
                    self._log_queue.put(("↻ Uvicorn will auto-reload changed files.", "muted"))
            except Exception as exc:
                self._log_queue.put((f"git pull failed: {exc}", "error"))
        threading.Thread(target=_pull, daemon=True).start()

    def _save_env(self):
        env_path = BASE_DIR / ".env"
        content = self._env_editor.get("1.0", "end-1c")
        env_path.write_text(content, encoding="utf-8")
        self._log_line(f"Saved {env_path}", "ok")

    # ── Status polling ─────────────────────────────────────────────────────────

    def _update_status(self):
        alive = _server_alive()
        proc_running = self._server_proc and self._server_proc.poll() is None

        if alive:
            self._status_dot.configure(fg=COL_GREEN)
            self._status_lbl.configure(text="Server: online", fg=COL_GREEN)
            self._btn_start.configure(state="disabled")
            self._btn_stop.configure(state="normal")
            self._btn_scan.configure(state="normal")
            self._btn_dash.configure(state="normal")
        else:
            self._status_dot.configure(fg=COL_RED if not proc_running else COL_AMBER)
            self._status_lbl.configure(
                text="Server: starting..." if proc_running else "Server: offline",
                fg=COL_AMBER if proc_running else COL_MUTED)
            self._btn_start.configure(state="disabled" if proc_running else "normal")
            self._btn_stop.configure(state="normal" if proc_running else "disabled")
            self._btn_scan.configure(state="disabled")
            self._btn_dash.configure(state="disabled")

        # Re-check every 3 seconds
        self._poll_id = self.after(3000, self._update_status)

    # ── Log helpers ────────────────────────────────────────────────────────────

    def _drain_log_queue(self):
        try:
            while True:
                line, tag = self._log_queue.get_nowait()
                self._log_line(line, tag)
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _log_line(self, text: str, tag: str = "muted"):
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def _on_close(self):
        if self._server_proc and self._server_proc.poll() is None:
            if messagebox.askyesno("Stop server?",
                                    "The server is still running.\nStop it before closing?"):
                self._stop_server()
        if self._poll_id:
            self.after_cancel(self._poll_id)
        self.destroy()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = TrendFilterApp()
    app.mainloop()
