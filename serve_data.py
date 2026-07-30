import json
import os
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext
from http.server import HTTPServer, BaseHTTPRequestHandler

_BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
REPORT_PATH = os.path.join(_BASE_DIR, "report.txt")
MARKERS_PATH = os.path.join(_BASE_DIR, "markers.json")
TEMPLATE_PATH = os.path.join(_BASE_DIR, "markers_template.json")
HOST = "localhost"
PORT = 8766

_markers_data = {}  # data from MarkersPanel
_sync_state = {"play": False, "time": None, "cmd": None}  # auto-sync from browser


def get_data():
    data = {"midrolls": [], "start_scale": 0, "finish_scale": 0, "start_prev": 0, "finish_prev": 0, "postroll": 0, "duration": 0}
    if _markers_data:
        data.update(_markers_data)
    return data


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/markers":
            data = _markers_data.copy()
        elif path == "/sync":
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            key = qs.get("key", [""])[0]
            if key:
                t = qs.get("time", ["0"])[0]
                _sync_state["key"] = key
                _sync_state["key_time"] = float(t)
                data = {"ok": True, "key": key}
            else:
                state = qs.get("state", [""])[0]
                is_play = state in ("play", "timeupdate")
                _sync_state["play"] = is_play
                t = qs.get("time")
                if t:
                    try:
                        _sync_state["time"] = float(t[0])
                    except:
                        pass
                dur = qs.get("duration")
                if dur:
                    try:
                        _sync_state["duration"] = float(dur[0])
                    except:
                        pass
                _sync_state["cmd"] = "play" if is_play else state
                data = {"ok": True, "play": _sync_state["play"]}
        elif path == "/":
            data = get_data()
        else:
            data = get_data()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    def log_message(self, *args):
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ИВИ")
        self.geometry("520x540")
        self.resizable(False, False)
        try:
            ico = self._res_path("ivi.ico")
            if os.path.exists(ico):
                self.iconbitmap(ico)
        except Exception:
            pass

        self.server = None
        self.server_thread = None
        self.com_thread = None
        self.markers_window = None
        self.markers_data = None

        self._logo_img = None
        try:
            from PIL import Image, ImageTk
            ico_path = self._res_path("ivi.ico")
            if os.path.exists(ico_path):
                img = Image.open(ico_path)
                # берём самый большой размер (0)
                img = img.resize((96, 96), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                tk.Label(self, image=self._logo_img).pack(pady=(8, 0))
        except Exception:
            pass
        tk.Label(self, text="Video Tester", font=("Segoe UI", 12), fg="#555").pack(pady=(0, 2))
        self.status_var = tk.StringVar(value="Статус: запуск...")
        tk.Label(self, textvariable=self.status_var, fg="#2563eb", font=("Segoe UI", 11, "bold")).pack(pady=6)

        url_frame = tk.Frame(self)
        url_frame.pack(pady=2)
        self.url_label = tk.Label(url_frame, font=("Segoe UI", 10))
        self.url_label.pack()

        log_frame = tk.LabelFrame(self, text="  Лог  ", font=("Segoe UI", 9))
        log_frame.pack(fill="both", expand=True, padx=12, pady=(6, 8))
        self.log_area = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9), wrap=tk.WORD, bg="#f8f9fa", state=tk.NORMAL)
        self.log_area.pack(fill="both", expand=True, padx=4, pady=4)
        tk.Button(log_frame, text="📋 Копировать лог", command=self.copy_log, font=("Segoe UI", 9), padx=10, pady=2).pack(pady=(0, 4))

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=(0, 10))
        self.stop_btn = tk.Button(btn_frame, text="Остановить сервер", command=self.stop, bg="#dc3545", fg="white", font=("Segoe UI", 10, "bold"), padx=20, pady=4)
        self.stop_btn.pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Открыть в браузере", command=self.open_browser, font=("Segoe UI", 10), padx=20, pady=4).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Отчет", command=self.open_report, font=("Segoe UI", 10), padx=16, pady=4).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Метки", command=self.open_markers, font=("Segoe UI", 10), padx=16, pady=4).pack(side=tk.LEFT, padx=4)

        self.log("Запуск сервера...")
        self.after(100, self.start)

    def _res_path(self, name):
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, name)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)

    def log(self, msg):
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)

    def copy_log(self):
        text = self.log_area.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.log("Лог скопирован в буфер обмена")

    def start(self):
        self.server = HTTPServer((HOST, PORT), Handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.after(200, self._poll_sync)

        url = f"http://{HOST}:{PORT}"
        self.url_label.config(text=f"Сервер: {url}", fg="#059669", font=("Segoe UI", 12, "bold"))
        self.status_var.set("Статус: запущен")
        self.log(f"Сервер запущен на {url}")

        self.after(3000, lambda: self.open_report())

    def _poll_sync(self):
        panel = self.markers_window
        if panel and panel.winfo_exists():
            cmd = _sync_state.pop("cmd", None)
            t = _sync_state.pop("time", None)
            if cmd == "seek":
                panel.video_seek(t)
            elif cmd == "play":
                panel.video_play(t)
            elif cmd == "pause":
                panel.video_pause(t)
            if not panel._data.get("duration"):
                dur = _sync_state.get("duration")
                if dur is not None and dur > 0:
                    panel._data["duration"] = int(dur)
                    _sync_state.pop("duration", None)
                    panel._sync_markers()
                    panel._update_summary()
                    panel._add_log(f"Длительность: {panel._format_time(int(dur))} (авто)")
            key = _sync_state.pop("key", None)
            if key:
                kt = _sync_state.pop("key_time", 0)
                panel.elapsed = kt
                panel.timer_var.set(panel._format_time(kt))
                method = getattr(panel, "mark_" + key, None)
                if method:
                    method()
        self.after(200, self._poll_sync)

    def open_report(self):
        try:
            os.startfile(REPORT_PATH)
            self.log("Отчет открыт")
        except Exception as e:
            self.log(f"Не удалось открыть отчет: {e}")

    def open_browser(self):
        import webbrowser
        webbrowser.open(f"http://{HOST}:{PORT}")

    def stop(self):
        self.status_var.set("Статус: остановка...")
        self.stop_btn.config(state=tk.DISABLED, text="Остановка...")
        if self.server:
            self.server.shutdown()
        self.log("Сервер остановлен")
        self.status_var.set("Статус: остановлен")
        self.after(500, self.destroy)

    def destroy(self):
        try:
            if self.server:
                self.server.server_close()
        except Exception:
            pass
        try:
            import subprocess
            subprocess.run(["taskkill", "/f", "/im", "EXCEL.EXE"], capture_output=True, timeout=5)
        except Exception:
            pass
        try:
            if hasattr(self, 'markers_window') and self.markers_window:
                self.markers_window.destroy()
        except Exception:
            pass
        super().destroy()

    def open_markers(self):
        if not hasattr(self, 'markers_window') or not self.markers_window or not self.markers_window.winfo_exists():
            self.markers_window = MarkersPanel(self)
        else:
            self.markers_window.lift()


class MarkersPanel(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Метки")
        self.geometry("520x760")
        self.minsize(400, 500)
        self.resizable(True, True)
        self.attributes("-topmost", True)
        try:
            ico = parent._res_path("ivi.ico")
            if os.path.exists(ico):
                self.iconbitmap(ico)
        except Exception:
            pass

        self.running = False
        self.elapsed = 0.0
        self.history = []

        self._data = self._load_markers()
        self._template = self._load_template()
        self._undo_stack = []
        self._timer_job = None
        self._sync_markers()

        global _current_panel
        _current_panel = self

        self._build_ui()
        self._update_template_label()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        # Timer
        self.timer_var = tk.StringVar(value="00:00:00")
        tk.Label(self, textvariable=self.timer_var, font=("Segoe UI", 28, "bold"), fg="#0d6efd").pack(pady=(10, 2))
        self.status_var = tk.StringVar(value="—")
        tk.Label(self, textvariable=self.status_var, font=("Segoe UI", 9), fg="#888").pack()

        # Buttons row
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=6)
        buttons = [
            ("↩ Отменить", self.undo),
            ("✕ Очистить", self.clear_all),
        ]
        for text, cmd in buttons:
            tk.Button(btn_frame, text=text, command=cmd, font=("Segoe UI", 9), padx=8, pady=2).pack(side=tk.LEFT, padx=2)

        tk.Frame(self, height=2, bg="#ccc").pack(fill="x", padx=10, pady=2)

        # Marker buttons
        mk_frame = tk.Frame(self)
        mk_frame.pack(pady=4)
        self._marker_btns = []
        markers = [
            ("1 Мидрол", self.mark_midroll, "#0d6efd"),
            ("2 Нач.заст.", self.mark_start_scale, "#198754"),
            ("3 Кон.заст.", self.mark_finish_scale, "#198754"),
            ("4 Нач.пред.", self.mark_start_prev, "#6f42c1"),
            ("5 Кон.пред.", self.mark_finish_prev, "#6f42c1"),
            ("6 Построл", self.mark_postroll, "#fd7e14"),
            ("7 Длит.", self.mark_duration, "#dc3545"),
        ]
        for label, cmd, color in markers:
            btn = tk.Button(mk_frame, text=label, command=cmd,
                          font=("Segoe UI", 10, "bold"), padx=8, pady=4,
                          bg=color, fg="white", width=18)
            btn.pack(pady=1)
            self._marker_btns.append(btn)

        tk.Frame(self, height=2, bg="#ccc").pack(fill="x", padx=10, pady=2)

        # Template buttons
        tmpl_frame = tk.Frame(self)
        tmpl_frame.pack(pady=2)
        self.template_var = tk.StringVar(value="Шаблон: —")
        tk.Label(tmpl_frame, textvariable=self.template_var, font=("Segoe UI", 9), fg="#555").pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(tmpl_frame, text="Запомнить шаблон", command=self.template_save, font=("Segoe UI", 9), padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        tk.Button(tmpl_frame, text="Вставить шаблон", command=self.template_apply, font=("Segoe UI", 9), padx=8, pady=2).pack(side=tk.LEFT, padx=2)

        tk.Frame(self, height=2, bg="#ccc").pack(fill="x", padx=10, pady=2)

        # Markers summary
        self.summary_frame = tk.Frame(self)
        self.summary_frame.pack(fill="x", padx=10, pady=(5, 2))
        self.summary_label = tk.Label(self.summary_frame, font=("Segoe UI", 10, "bold"), fg="#222", anchor="w")
        self.summary_label.pack(fill="x")
        self.summary_edit_frame = tk.Frame(self.summary_frame)
        self.summary_edit_frame.pack(fill="x", pady=(2, 0))
        self._summary_entries = []

        tk.Frame(self, height=2, bg="#ccc").pack(fill="x", padx=10, pady=2)

        # Markers log
        self.log_text = tk.Text(self, height=5, font=("Consolas", 9), bg="#ffffff", state=tk.DISABLED)
        self.log_text.pack(fill="both", expand=True, padx=8, pady=(2, 6))
        self._update_summary()

    def _add_log(self, text):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _update_summary(self):
        d = self._data
        cnt_mid = len(d["midrolls"])
        total = cnt_mid + (1 if d["start_scale"] else 0) + (1 if d["start_prev"] else 0) + (1 if d["postroll"] else 0) + (1 if d["duration"] else 0)
        if total == 0:
            self.summary_label.config(text="Меток: 0")
        else:
            parts = [f"Меток: {total}"]
            if cnt_mid: parts.append(f"мидролов {cnt_mid}")
            if d["start_scale"] or d["finish_scale"]:
                parts.append(f"заст.{d['start_scale']}–{d['finish_scale']}")
            if d["start_prev"] or d["finish_prev"]:
                parts.append(f"пред.{d['start_prev']}–{d['finish_prev']}")
            if d["postroll"]: parts.append(f"построл {d['postroll']}")
            if d["duration"]: parts.append(f"длит.{d['duration']}")
            self.summary_label.config(text="  ".join(parts))
        for e in self._summary_entries:
            e.destroy()
        self._summary_entries.clear()
        row = 0
        for i, t in enumerate(d["midrolls"]):
            lbl = tk.Label(self.summary_edit_frame, text=f"M{i+1}:", font=("Consolas", 9))
            lbl.grid(row=row, column=0, sticky="w", padx=(0, 2))
            ent = tk.Entry(self.summary_edit_frame, font=("Consolas", 9), width=10, justify="center")
            ent.insert(0, self._format_time(t))
            ent.grid(row=row, column=1, sticky="w", padx=(0, 8))
            ent.bind("<Return>", lambda e, idx=i: self._edit_marker("midroll", idx, e.widget.get()))
            ent.bind("<FocusOut>", lambda e, idx=i: self._edit_marker("midroll", idx, e.widget.get()))
            self._summary_entries.append(ent)
            row += 1
        pairs = [
            ("Нач.заст.", "start_scale", "Кон.заст.", "finish_scale"),
            ("Нач.пред.", "start_prev", "Кон.пред.", "finish_prev"),
        ]
        for lbl1, key1, lbl2, key2 in pairs:
            val1, val2 = d[key1], d[key2]
            if not val1 and not val2:
                continue
            tk.Label(self.summary_edit_frame, text=f"{lbl1}:", font=("Consolas", 9)).grid(row=row, column=0, sticky="w", padx=(0, 2))
            e1 = tk.Entry(self.summary_edit_frame, font=("Consolas", 9), width=10, justify="center")
            e1.insert(0, self._format_time(val1) if val1 else "")
            e1.grid(row=row, column=1, sticky="w", padx=(0, 8))
            e1.bind("<Return>", lambda e, k=key1: self._edit_field(k, e.widget.get()))
            e1.bind("<FocusOut>", lambda e, k=key1: self._edit_field(k, e.widget.get()))
            self._summary_entries.extend([e1])
            tk.Label(self.summary_edit_frame, text=f"{lbl2}:", font=("Consolas", 9)).grid(row=row, column=2, sticky="w", padx=(0, 2))
            e2 = tk.Entry(self.summary_edit_frame, font=("Consolas", 9), width=10, justify="center")
            e2.insert(0, self._format_time(val2) if val2 else "")
            e2.grid(row=row, column=3, sticky="w")
            e2.bind("<Return>", lambda e, k=key2: self._edit_field(k, e.widget.get()))
            e2.bind("<FocusOut>", lambda e, k=key2: self._edit_field(k, e.widget.get()))
            self._summary_entries.extend([e2])
            row += 1
        singles = [
            ("Построл", "postroll"),
            ("Длит.", "duration"),
        ]
        for lbl, key in singles:
            val = d[key]
            if not val:
                continue
            tk.Label(self.summary_edit_frame, text=f"{lbl}:", font=("Consolas", 9)).grid(row=row, column=0, sticky="w", padx=(0, 2))
            e = tk.Entry(self.summary_edit_frame, font=("Consolas", 9), width=10, justify="center")
            e.insert(0, self._format_time(val))
            e.grid(row=row, column=1, sticky="w", padx=(0, 8))
            e.bind("<Return>", lambda e, k=key: self._edit_field(k, e.widget.get()))
            e.bind("<FocusOut>", lambda e, k=key: self._edit_field(k, e.widget.get()))
            self._summary_entries.append(e)
            row += 1

    def _time_from_str(self, s):
        s = s.strip()
        if not s:
            return 0
        try:
            parts = s.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            else:
                return int(s)
        except ValueError:
            return None

    def _edit_marker(self, key, idx, val):
        t = self._time_from_str(val)
        if t is None:
            return
        if key == "midroll":
            if 0 <= idx < len(self._data["midrolls"]):
                self._data["midrolls"][idx] = t
                self._add_log(f"M{idx+1} изменено: {self._format_time(t)}")
        self._sync_markers()
        self._update_summary()

    def _edit_field(self, key, val):
        t = self._time_from_str(val)
        if t is None:
            return
        self._data[key] = t
        self._add_log(f"{key} изменено: {self._format_time(t)}")
        self._sync_markers()
        self._update_summary()

    def _format_time(self, secs):
        h = int(secs // 3600)
        m = int(secs % 3600 // 60)
        s = int(secs % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _load_markers(self):
        default = {"midrolls": [], "start_scale": 0, "finish_scale": 0, "start_prev": 0, "finish_prev": 0, "postroll": 0, "duration": 0}
        try:
            with open(MARKERS_PATH, encoding="utf-8") as f:
                data = json.load(f)
                for k in default:
                    data.setdefault(k, default[k])
                return data
        except:
            return default

    def _save_markers(self):
        try:
            with open(MARKERS_PATH, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.parent.log(f"Ошибка сохранения меток: {e}")

    def _load_template(self):
        default = {"start_scale": 0, "finish_scale": 0, "start_prev": 0, "finish_prev": 0, "postroll": 0, "duration": 0, "midrolls": []}
        try:
            with open(TEMPLATE_PATH, encoding="utf-8") as f:
                data = json.load(f)
                for k in default:
                    data.setdefault(k, default[k])
                return data
        except:
            return default

    def _save_template(self):
        try:
            with open(TEMPLATE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._template, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.parent.log(f"Ошибка сохранения шаблона: {e}")

    def template_save(self):
        self._template = self._data.copy()
        self._save_template()
        self._update_template_label()
        self._add_log("Шаблон сохранён")

    def _update_template_label(self):
        cnt = len(self._template.get("midrolls", []))
        s = self._template["start_scale"]
        f = self._template["finish_scale"]
        if cnt or s or f or self._template["postroll"] or self._template["duration"]:
            self.template_var.set(f"Шаблон: {cnt} мидр., заст.{s}–{f}")
        else:
            self.template_var.set("Шаблон: —")

    def template_apply(self):
        for k in self._template:
            if k == "midrolls":
                continue
            self._data[k] = self._template[k]
        self._sync_markers()
        self._update_summary()
        self._add_log("Шаблон применён (мидролы не тронуты)")

    def _update_timer(self):
        if self.running:
            self.elapsed += 0.1
            self.timer_var.set(self._format_time(self.elapsed))
            self._timer_job = self.after(100, self._update_timer)

    def video_play(self, time_sec):
        if time_sec is not None:
            self.elapsed = time_sec
            self.timer_var.set(self._format_time(self.elapsed))
        if not self.running:
            self.running = True
            self.status_var.set("Воспроизведение")
            self._update_timer()

    def video_pause(self, time_sec):
        if time_sec is not None:
            self.elapsed = time_sec
            self.timer_var.set(self._format_time(self.elapsed))
        self.running = False
        self.status_var.set("Пауза")
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None

    def video_seek(self, time_sec):
        if time_sec is not None:
            self.elapsed = time_sec
            self.timer_var.set(self._format_time(self.elapsed))

    @property
    def current_time(self):
        return int(self.elapsed * 1000) // 1000  # integer seconds

    def _save_action(self, action, value):
        self._undo_stack.append((action, value))

    def undo(self):
        if not self._undo_stack:
            self._add_log("↩ Нет действий для отмены")
            return
        action, value = self._undo_stack.pop()
        if action == "midroll":
            if self._data["midrolls"]:
                removed = self._data["midrolls"].pop()
                self._add_log(f"↩ Отменён мидрол: {self._format_time(removed)}")
        elif action == "start_scale":
            self._data["start_scale"] = 0
            self._add_log("↩ Отменено: начало заставки")
        elif action == "finish_scale":
            self._data["finish_scale"] = 0
            self._add_log("↩ Отменено: конец заставки")
        elif action == "start_prev":
            self._data["start_prev"] = 0
            self._add_log("↩ Отменено: начало предыдущей")
        elif action == "finish_prev":
            self._data["finish_prev"] = 0
            self._add_log("↩ Отменено: конец предыдущей")
        elif action == "postroll":
            self._data["postroll"] = 0
            self._add_log("↩ Отменено: построл")
        elif action == "duration":
            self._data["duration"] = 0
            self._add_log("↩ Отменено: длительность")
        self._update_summary()
        self._sync_markers()

    def clear_all(self):
        self._data = {"midrolls": [], "start_scale": 0, "finish_scale": 0, "start_prev": 0, "finish_prev": 0, "postroll": 0, "duration": 0}
        self._undo_stack.clear()
        self._update_summary()
        self._add_log("✕ Все метки очищены")
        self._sync_markers()

    def transmit(self):
        d = self._data
        lines = []
        for m in d["midrolls"]:
            lines.append(m)
        parts = []
        if d["duration"]: parts.append(f"duration={d['duration']}")
        if d["postroll"]: parts.append(f"postroll={d['postroll']}")
        if d["start_scale"]: parts.append(f"start_scale={d['start_scale']}")
        if d["finish_scale"]: parts.append(f"finish_scale={d['finish_scale']}")
        if d["start_prev"]: parts.append(f"start_prev={d['start_prev']}")
        if d["finish_prev"]: parts.append(f"finish_prev={d['finish_prev']}")
        text = "midrolls=" + ",".join(str(m) for m in d["midrolls"]) + "  " + "  ".join(parts)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.parent.log(f"📋 Метки скопированы в буфер обмена")
        self._add_log(f"📋 Скопировано: {text[:80]}...")

    def _sync_markers(self):
        global _markers_data
        _markers_data = self._data.copy()

    def mark_midroll(self):
        t = self.current_time
        self._data["midrolls"].append(t)
        self._save_action("midroll", t)
        self._add_log(f"Мидрол {len(self._data['midrolls'])}: {self._format_time(t)}")
        self._update_summary()
        self._sync_markers()

    def mark_start_scale(self):
        t = self.current_time
        self._data["start_scale"] = t
        self._save_action("start_scale", t)
        self._add_log(f"Начало заставки: {self._format_time(t)}")
        self._update_summary()
        self._sync_markers()

    def mark_finish_scale(self):
        t = self.current_time
        if not self._data["start_scale"]:
            self._data["start_scale"] = 0
            self._save_action("start_scale", 0)
            self._add_log(f"Начало заставки: 00:00:00 (авто)")
        self._data["finish_scale"] = t
        self._save_action("finish_scale", t)
        self._add_log(f"Конец заставки: {self._format_time(t)}")
        self._update_summary()
        self._sync_markers()

    def mark_start_prev(self):
        t = self.current_time
        self._data["start_prev"] = t
        self._save_action("start_prev", t)
        self._add_log(f"Начало предыдущей: {self._format_time(t)}")
        self._update_summary()
        self._sync_markers()

    def mark_finish_prev(self):
        t = self.current_time
        self._data["finish_prev"] = t
        self._save_action("finish_prev", t)
        self._add_log(f"Конец предыдущей: {self._format_time(t)}")
        self._update_summary()
        self._sync_markers()

    def mark_postroll(self):
        t = self.current_time
        self._data["postroll"] = t
        self._save_action("postroll", t)
        self._add_log(f"Построл: {self._format_time(t)}")
        self._update_summary()
        self._sync_markers()

    def mark_duration(self):
        t = self.current_time
        self._data["duration"] = t
        self._save_action("duration", t)
        self._add_log(f"Длительность: {self._format_time(t)}")
        self._update_summary()
        self._sync_markers()

    def on_close(self):
        global _current_panel
        _current_panel = None
        self.running = False
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None
        self._save_markers()
        global _markers_data
        _markers_data = self._data.copy()
        if hasattr(self.parent, 'markers_data'):
            self.parent.markers_data = self._data.copy()
        cnt = len(self._data.get("midrolls", []))
        self.parent.log(f"Метки сохранены: {cnt} мидролов, файл {MARKERS_PATH}")
        self.parent.log(f"  localhost:8766/markers — данные меток")
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
