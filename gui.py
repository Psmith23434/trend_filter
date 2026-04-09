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
BASE_DIR    = Path(__file__).parent.resolve()
ENV_FILE    = BASE_DIR / ".env"
API_URL     = "http://127.0.0.1:8000"
DASH_URL    = f"{API_URL}/dashboard/"
SCAN_URL    = f"{API_URL}/scan"
HEALTH_URL  = f"{API_URL}/health"
PYTHON      = sys.executable

# Collector definitions: (env_var, label, default_on)
COLLECTORS = [
    ("COLLECTOR_RSS",     "RSS Feeds (133 sources)",  True),
    ("COLLECTOR_REDDIT",  "Reddit",                   False),
    ("COLLECTOR_HN",      "Hacker News",              False),
    ("COLLECTOR_GOOGLE",  "Google Trends",            False),
    ("COLLECTOR_YOUTUBE", "YouTube",                  False),
    ("COLLECTOR_GITHUB",  "GitHub Trending",          False),
    ("COLLECTOR_AMAZON",  "Amazon Suggest",           False),
]

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
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def _read_env() -> dict:
    """Parse .env file into a dict."""
    env = {}
    src = ENV_FILE if ENV_FILE.exists() else BASE_DIR / ".env.example"
    if src.exists():
        for line in src.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _write_env(updates: dict):
    """Merge *updates* into the .env file, preserving all other lines."""
    lines = []
    src = ENV_FILE if ENV_FILE.exists() else BASE_DIR / ".env.example"
    existing = src.read_text(encoding="utf-8").splitlines() if src.exists() else []
    written = set()
    for line in existing:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                lines.append(f"{key}={updates[key]}")
                written.add(key)
                continue
        lines.append(line)
    # Append any keys not already present
    for k, v in updates.items():
        if k not in written:
            lines.append(f"{k}={v}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Main App ───────────────────────────────────────────────────────────────────

class TrendFilterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trend Filter")
        self.geometry("860x640")
        self.minsize(760, 540)
        self.configure(bg=COL_BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._server_proc: subprocess.Popen | None = None
        self._log_queue: queue.Queue = queue.Queue()
        self._poll_id = None
        self._collector_vars: dict[str, tk.BooleanVar] = {}

        self._build_ui()
        self._update_status()
        self._drain_log_queue()

    # ── UI ───────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Top bar
        top = tk.Frame(self, bg=COL_SURFACE, pady=8)
        top.pack(fill="x")
        tk.Label(top, text="📡  Trend Filter", font=("Segoe UI", 16, "bold"),
                 bg=COL_SURFACE, fg=COL_ACCENT).pack(side="left", padx=16)
        self._status_dot = tk.Label(top, text="●", font=("Segoe UI", 18),
                                     bg=COL_SURFACE, fg=COL_RED)
        self._status_dot.pack(side="right", padx=6)
        self._status_lbl = tk.Label(top, text="Server: offline",
                                     font=("Segoe UI", 10), bg=COL_SURFACE, fg=COL_MUTED)
        self._status_lbl.pack(side="right", padx=4)

        # Button row
        btn_row = tk.Frame(self, bg=COL_BG, pady=10)
        btn_row.pack(fill="x", padx=16)
        self._btn_start = self._btn(btn_row, "▶  Start Server",   COL_GREEN,  self._start_server)
        self._btn_start.pack(side="left", padx=(0, 8))
        self._btn_stop  = self._btn(btn_row, "■  Stop Server",    COL_RED,    self._stop_server)
        self._btn_stop.pack(side="left", padx=(0, 8))
        self._btn_stop.configure(state="disabled")
        self._btn_scan  = self._btn(btn_row, "🔍  Run Scan",       COL_ACCENT, self._run_scan)
        self._btn_scan.pack(side="left", padx=(0, 8))
        self._btn_scan.configure(state="disabled")
        self._btn_dash  = self._btn(btn_row, "🌐  Open Dashboard", COL_AMBER,  self._open_dashboard)
        self._btn_dash.pack(side="left", padx=(0, 8))
        self._btn_dash.configure(state="disabled")
        tk.Button(btn_row, text="🔄  git pull",
                  font=("Segoe UI", 10), bg=COL_CARD, fg=COL_TEXT,
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  activebackground=COL_SURFACE, activeforeground=COL_TEXT,
                  command=self._git_pull).pack(side="left", padx=(0, 8))

        # Progress bar (hidden until scan)
        self._progress = ttk.Progressbar(self, mode="indeterminate", length=200)

        # Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self._style_notebook(nb)

        # Tab 1 — Server Log
        log_frame = tk.Frame(nb, bg=COL_BG)
        nb.add(log_frame, text="  Server Log  ")
        self._log = scrolledtext.ScrolledText(
            log_frame, bg="#0d0d1a", fg=COL_TEXT,
            font=("Consolas", 9), relief="flat", wrap="word",
            insertbackground=COL_ACCENT, state="disabled")
        self._log.pack(fill="both", expand=True, padx=4, pady=4)
        self._log.tag_config("info",  foreground=COL_ACCENT)
        self._log.tag_config("ok",    foreground=COL_GREEN)
        self._log.tag_config("warn",  foreground=COL_AMBER)
        self._log.tag_config("error", foreground=COL_RED)
        self._log.tag_config("muted", foreground=COL_MUTED)
        tk.Button(log_frame, text="Clear log", font=("Segoe UI", 8),
                  bg=COL_CARD, fg=COL_MUTED, relief="flat", padx=8, pady=3,
                  cursor="hand2", command=self._clear_log).pack(anchor="e", padx=4, pady=(0, 4))

        # Tab 2 — Collectors
        col_frame = tk.Frame(nb, bg=COL_BG)
        nb.add(col_frame, text="  Collectors  ")
        self._build_collectors_tab(col_frame)

        # Tab 3 — Settings (.env)
        cfg_frame = tk.Frame(nb, bg=COL_BG)
        nb.add(cfg_frame, text="  Settings (.env)  ")
        self._build_settings(cfg_frame)

    def _btn(self, parent, text, colour, cmd):
        return tk.Button(parent, text=text,
                         font=("Segoe UI", 10, "bold"),
                         bg=colour, fg="#ffffff" if colour != COL_AMBER else "#1a1a2e",
                         relief="flat", padx=14, pady=7, cursor="hand2",
                         activebackground=colour, activeforeground="white",
                         command=cmd)

    def _style_notebook(self, nb):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TNotebook",     background=COL_BG,      borderwidth=0)
        s.configure("TNotebook.Tab", background=COL_CARD,    foreground=COL_MUTED,
                     padding=[12, 6], font=("Segoe UI", 10))
        s.map("TNotebook.Tab",
              background=[("selected", COL_SURFACE)],
              foreground=[("selected", COL_ACCENT)])
        s.configure("TProgressbar", troughcolor=COL_CARD, background=COL_ACCENT)

    def _build_collectors_tab(self, parent):
        tk.Label(parent,
                 text="Choose which data sources to include in each scan.",
                 font=("Segoe UI", 10), bg=COL_BG, fg=COL_MUTED
                 ).pack(anchor="w", padx=16, pady=(12, 6))

        env = _read_env()
        card = tk.Frame(parent, bg=COL_SURFACE, padx=16, pady=12)
        card.pack(fill="x", padx=16, pady=(0, 8))

        for env_var, label, default_on in COLLECTORS:
            # Read current value from .env if present
            raw = env.get(env_var, "true" if default_on else "false").lower()
            current = raw in ("1", "true", "yes")
            var = tk.BooleanVar(value=current)
            self._collector_vars[env_var] = var

            row = tk.Frame(card, bg=COL_SURFACE)
            row.pack(fill="x", pady=3)

            cb = tk.Checkbutton(
                row, variable=var, text=label,
                font=("Segoe UI", 10),
                bg=COL_SURFACE, fg=COL_TEXT,
                selectcolor=COL_CARD,
                activebackground=COL_SURFACE,
                activeforeground=COL_ACCENT,
                cursor="hand2",
            )
            cb.pack(side="left")

            # Badge: ON / OFF
            badge_var = tk.StringVar(value="ON" if current else "OFF")
            badge_col = tk.StringVar(value=COL_GREEN if current else COL_MUTED)
            badge = tk.Label(row, textvariable=badge_var,
                             font=("Segoe UI", 8, "bold"),
                             bg=COL_CARD, fg=COL_GREEN if current else COL_MUTED,
                             padx=6, pady=2)
            badge.pack(side="left", padx=8)

            def _make_trace(bv, bv_str, bdg):
                def _trace(*_):
                    on = bv.get()
                    bv_str.set("ON" if on else "OFF")
                    bdg.configure(fg=COL_GREEN if on else COL_MUTED)
                return _trace
            var.trace_add("write", _make_trace(var, badge_var, badge))

        save_btn = tk.Button(
            parent, text="💾  Save collector settings",
            font=("Segoe UI", 10, "bold"), bg=COL_GREEN, fg="#111",
            relief="flat", padx=14, pady=7, cursor="hand2",
            command=self._save_collectors)
        save_btn.pack(anchor="w", padx=16, pady=(4, 0))

        tk.Label(parent,
                 text="Changes take effect on the next scan (uvicorn hot-reloads automatically).",
                 font=("Segoe UI", 8), bg=COL_BG, fg=COL_MUTED
                 ).pack(anchor="w", padx=16, pady=(4, 0))

    def _build_settings(self, parent):
        env_path = ENV_FILE
        env_example = BASE_DIR / ".env.example"

        def _load():
            src = env_path if env_path.exists() else env_example
            return src.read_text(encoding="utf-8") if src.exists() else ""

        tk.Label(parent, text="Edit .env directly (advanced)",
                 font=("Segoe UI", 10, "bold"), bg=COL_BG, fg=COL_TEXT
                 ).pack(anchor="w", padx=12, pady=(12, 4))

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
                  command=lambda: (
                      self._env_editor.delete("1.0", "end"),
                      self._env_editor.insert("1.0", _load()))
                  ).pack(side="left")

    # ── Actions ────────────────────────────────────────────────────────────────

    def _save_collectors(self):
        updates = {
            env_var: "true" if self._collector_vars[env_var].get() else "false"
            for env_var, _, _ in COLLECTORS
        }
        _write_env(updates)
        active = [label for env_var, label, _ in COLLECTORS
                  if self._collector_vars[env_var].get()]
        self._log_line(f"Collector settings saved. Active: {', '.join(active) or 'none'}", "ok")
        self._log_line("Uvicorn will hot-reload — next scan will use the new settings.", "muted")

    def _start_server(self):
        if self._server_proc and self._server_proc.poll() is None:
            self._log_line("Server is already running.", "warn")
            return
        self._log_line("Starting uvicorn server...", "info")
        cmd = [PYTHON, "-m", "uvicorn", "api.main:app", "--reload",
               "--host", "127.0.0.1", "--port", "8000"]
        try:
            self._server_proc = subprocess.Popen(
                cmd, cwd=str(BASE_DIR),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
            )
        except Exception as exc:
            self._log_line(f"Failed to start server: {exc}", "error")
            return
        threading.Thread(target=self._stream_proc, args=(self._server_proc,), daemon=True).start()
        threading.Thread(target=self._wait_for_server, daemon=True).start()

    def _stream_proc(self, proc):
        for line in iter(proc.stdout.readline, ""):
            self._log_queue.put((line.rstrip(), "muted"))
        self._log_queue.put(("[Server process ended]", "warn"))
        self.after(0, self._update_status)

    def _wait_for_server(self):
        for _ in range(30):
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
        active = [label for env_var, label, _ in COLLECTORS
                  if self._collector_vars.get(env_var, tk.BooleanVar(value=False)).get()]
        self._log_line(f"POST /scan — active collectors: {', '.join(active) or 'none'}", "info")
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        import json
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
                result = subprocess.run(["git", "pull"], cwd=str(BASE_DIR),
                                        capture_output=True, text=True, timeout=30)
                out = result.stdout.strip() or result.stderr.strip()
                self._log_queue.put((out, "ok" if result.returncode == 0 else "error"))
                if result.returncode == 0:
                    self._log_queue.put(("↻ Uvicorn will auto-reload changed files.", "muted"))
            except Exception as exc:
                self._log_queue.put((f"git pull failed: {exc}", "error"))
        threading.Thread(target=_pull, daemon=True).start()

    def _save_env(self):
        content = self._env_editor.get("1.0", "end-1c")
        ENV_FILE.write_text(content, encoding="utf-8")
        self._log_line(f"Saved {ENV_FILE}", "ok")

    # ── Status polling ─────────────────────────────────────────────────────────

    def _update_status(self):
        alive      = _server_alive()
        proc_up    = self._server_proc and self._server_proc.poll() is None
        if alive:
            self._status_dot.configure(fg=COL_GREEN)
            self._status_lbl.configure(text="Server: online", fg=COL_GREEN)
            self._btn_start.configure(state="disabled")
            self._btn_stop.configure(state="normal")
            self._btn_scan.configure(state="normal")
            self._btn_dash.configure(state="normal")
        else:
            self._status_dot.configure(fg=COL_RED if not proc_up else COL_AMBER)
            self._status_lbl.configure(
                text="Server: starting..." if proc_up else "Server: offline",
                fg=COL_AMBER if proc_up else COL_MUTED)
            self._btn_start.configure(state="disabled" if proc_up else "normal")
            self._btn_stop.configure(state="normal" if proc_up else "disabled")
            self._btn_scan.configure(state="disabled")
            self._btn_dash.configure(state="disabled")
        self._poll_id = self.after(3000, self._update_status)

    # ── Log ───────────────────────────────────────────────────────────────────────

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
