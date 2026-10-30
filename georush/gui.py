"""Korean desktop controls. Rendering runs in a worker; Tk stays on its own thread."""
from __future__ import annotations

from pathlib import Path
import json
import queue
import threading
import tkinter as tk
from tkinter import font as tkfont
import sys
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .paths import default_output_root, open_folder, history_path


class GeoRushApp(tk.Tk):
    def __init__(self):
        super().__init__()
        if sys.platform == 'win32':
            for name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont', 'TkCaptionFont', 'TkTooltipFont', 'TkFixedFont'):
                tkfont.nametofont(name).configure(family='Malgun Gothic', size=10)
        self.title(f"GeoRush Generator v{__version__}")
        self.geometry("1000x800")
        self.minsize(780, 680)
        self.configure(bg="#0A1730")
        self.events = queue.Queue()
        self.worker = None
        self.mode = tk.StringVar(value="Shorts")
        self.long_video_count = tk.StringVar(value="1")
        self.long_questions = tk.StringVar(value="40")
        self.video_count = tk.StringVar(value="1")
        self.difficulty = tk.StringVar(value="Mixed")
        self.questions = tk.IntVar(value=3)
        self.bgm = tk.StringVar(value="10%")
        self.output = tk.StringVar(value=str(default_output_root()))
        self.status = tk.StringVar(value="설정을 확인한 뒤 영상 제작 시작을 누르세요.")
        self.results = tk.StringVar(value="성공 0편 · 실패 0편")
        self.progress = tk.DoubleVar(value=0)
        self._build()
        self.after(100, self._poll)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#0A1730")
        style.configure("TLabel", background="#0A1730", foreground="#EDF4FF")
        style.configure("TButton", padding=8)
        style.configure("Accent.TButton", background="#FFD83D", foreground="#102247", padding=10)
        style.configure("TLabelframe", background="#0A1730")
        style.configure("TLabelframe.Label", background="#0A1730", foreground="#BDD7FF")
        outer = ttk.Frame(self, padding=20)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="GeoRush", font=("Arial", 28, "bold"), foreground="#FFD83D").pack(anchor="w")
        ttk.Label(outer, text="국기 퀴즈 Shorts / Longform · 영어 콘텐츠 · 무료 로컬 제작").pack(anchor="w", pady=(0, 16))
        mode_row = ttk.Frame(outer)
        mode_row.pack(fill="x", pady=(0,8))
        ttk.Label(mode_row, text="영상 종류").pack(side="left", padx=(0,12))
        self.mode_box = ttk.Combobox(mode_row, textvariable=self.mode, values=("Shorts","Longform"), state="readonly", width=16)
        self.mode_box.pack(side="left")
        self.mode_box.bind("<<ComboboxSelected>>", self._mode_changed)
        self.long_settings = ttk.LabelFrame(outer, text="Longform 전용 설정 · 1920×1080 · Mixed", padding=10)
        ttk.Label(self.long_settings, text="제작 편수").grid(row=0,column=0,padx=8)
        ttk.Combobox(self.long_settings,textvariable=self.long_video_count,values=("1","2","3"),state="readonly",width=8).grid(row=0,column=1)
        ttk.Label(self.long_settings, text="문제 수").grid(row=0,column=2,padx=8)
        ttk.Combobox(self.long_settings,textvariable=self.long_questions,values=("20","30","40"),state="readonly",width=8).grid(row=0,column=3)
        ttk.Label(self.long_settings,text="Easy → Normal → Hard → Expert (편집 기준)\n20문제 3:44 · 30문제 5:24 · 40문제 7:04").grid(row=1,column=0,columnspan=4,sticky="w",pady=6)
        fields = ttk.LabelFrame(outer, text="Shorts 설정 / 공통 BGM·출력", padding=12)
        self.settings_fields = fields
        fields.pack(fill="x")
        fields.columnconfigure(1, weight=1)
        fields.columnconfigure(3, weight=1)
        for row, (name, variable, values) in enumerate([
            ("제작할 영상 개수", self.video_count, ("1", "3", "5", "10")),
            ("난이도", self.difficulty, ("Easy", "Normal", "Hard", "Mixed")),
        ]):
            ttk.Label(fields, text=name).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
            ttk.Combobox(fields, textvariable=variable, values=values, state="readonly", width=18).grid(row=row, column=1, sticky="w")
        ttk.Label(fields, text="한 영상당 문제 수").grid(row=0, column=2, sticky="w", padx=(20, 10))
        ttk.Spinbox(fields, from_=1, to=5, textvariable=self.questions, width=8, state="readonly").grid(row=0, column=3, sticky="w")
        ttk.Label(fields, text="BGM 볼륨").grid(row=1, column=2, sticky="w", padx=(20, 10))
        ttk.Combobox(fields, textvariable=self.bgm, values=("8%", "10%", "12%"), state="readonly", width=8).grid(row=1, column=3, sticky="w")
        self.short_controls = [widget for widget in fields.winfo_children()
                               if widget.grid_info() and (int(widget.grid_info()['column'])<2
                               or int(widget.grid_info()['row'])==0)]
        ttk.Label(fields, text="출력 폴더").grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(fields, textvariable=self.output).grid(row=2, column=1, columnspan=3, sticky="ew", pady=(12, 0))
        folder_buttons = ttk.Frame(fields)
        folder_buttons.grid(row=3, column=1, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Button(folder_buttons, text="폴더 선택", command=self._choose_folder).pack(side="left", padx=(0, 8))
        ttk.Button(folder_buttons, text="출력 폴더 열기", command=self._open_output).pack(side="left")
        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=12)
        self.start_button = ttk.Button(actions, text="영상 제작 시작", style="Accent.TButton", command=self._start)
        self.start_button.pack(side="left")
        ttk.Label(actions, textvariable=self.results).pack(side="right")
        ttk.Progressbar(outer, maximum=100, variable=self.progress).pack(fill="x", pady=(0, 6))
        ttk.Label(outer, textvariable=self.status, wraplength=900).pack(anchor="w", pady=(0, 10))
        notebook = ttk.Notebook(outer)
        notebook.pack(fill="both", expand=True)
        log_frame = ttk.Frame(notebook, padding=6)
        history_frame = ttk.Frame(notebook, padding=6)
        notebook.add(log_frame, text="진행 및 오류 로그")
        notebook.add(history_frame, text="제작 이력")
        self.log = tk.Text(log_frame, height=10, wrap="word", bg="#071226", fg="#E2EDFF", insertbackground="#FFFFFF", state="disabled")
        log_scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True)
        ttk.Button(history_frame, text="제작 이력 새로고침", command=self._refresh_history).pack(anchor="w", pady=(0, 6))
        columns = ("time", "status", "difficulty", "path", "error")
        self.history = ttk.Treeview(history_frame, columns=columns, show="headings", height=8)
        for key, title, width in [("time", "제작 시각", 160), ("status", "상태", 80), ("difficulty", "난이도", 80), ("path", "결과 폴더", 280), ("error", "오류", 240)]:
            self.history.heading(key, text=title)
            self.history.column(key, width=width, minwidth=60)
        history_scroll = ttk.Scrollbar(history_frame, orient="horizontal", command=self.history.xview)
        self.history.configure(xscrollcommand=history_scroll.set)
        self.history.pack(fill="both", expand=True)
        history_scroll.pack(fill="x")
        self.history.bind("<Double-1>", self._open_history)
        ttk.Label(outer, text="Python과 FFmpeg가 포함돼 있어 별도 설치가 필요 없습니다. 영상 생성은 인터넷·API 키 없이 실행합니다.", wraplength=900).pack(anchor="w", pady=(12, 0))
        self._write_log("GeoRush Generator 준비 완료. 기본 3문제, BGM 10%, TTS 없음.")

    def _mode_changed(self, _event=None):
        if self.mode.get() == 'Longform':
            self.long_settings.pack(fill="x", before=self.settings_fields, pady=(0,8))
            for widget in self.short_controls: widget.grid_remove()
        else:
            self.long_settings.pack_forget()
            for widget in self.short_controls: widget.grid()

    def _choose_folder(self):
        selected = filedialog.askdirectory(title="GeoRush 출력 폴더 선택", initialdir=str(Path(self.output.get()).parent))
        if selected:
            self.output.set(selected)
            self._refresh_history()

    def _open_output(self):
        try:
            path = Path(self.output.get()).expanduser()
            if not path.is_dir():
                raise FileNotFoundError("아직 출력 폴더가 없습니다. 먼저 영상을 제작하세요.")
            open_folder(path)
        except Exception as exc:
            messagebox.showerror("출력 폴더", str(exc), parent=self)

    def _start(self):
        if self.worker is not None and self.worker.is_alive():
            return
        try:
            longform = self.mode.get() == 'Longform'
            count = int(self.long_video_count.get() if longform else self.video_count.get())
            questions = int(self.long_questions.get() if longform else self.questions.get())
            valid = count in (1,2,3) and questions in (20,30,40) if longform else count in (1,3,5,10) and 1<=questions<=5
            if not valid:
                raise ValueError("영상 개수와 문제 수를 확인하세요.")
            if not self.output.get().strip():
                raise ValueError("출력 폴더를 선택하세요.")
            arguments = dict(_mode=self.mode.get(), count=count, difficulty="Mixed" if longform else self.difficulty.get(), questions_per_video=questions,
                             bgm_volume=int(self.bgm.get().rstrip("%"))/100,
                             output_root=Path(self.output.get()).expanduser(), progress_callback=self.events.put)
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("설정 오류", str(exc), parent=self)
            return
        self.progress.set(0)
        self.results.set("성공 0편 · 실패 0편")
        self.status.set("제작을 시작합니다. 이 창에서 진행 상황을 확인할 수 있습니다.")
        self.start_button.configure(state="disabled")
        self.mode_box.configure(state="disabled")
        self._write_log(f"배치 시작: {count}편 / {questions}문제 / {self.difficulty.get()} / BGM {self.bgm.get()}")
        self.worker = threading.Thread(target=self._run, args=(arguments,), name="GeoRush-render", daemon=True)
        self.worker.start()

    def _run(self, arguments):
        try:
            mode = arguments.pop('_mode')
            if mode == 'Longform':
                from .longform.pipeline import generate_batch
            else:
                from .pipeline import generate_batch
            rows = generate_batch(**arguments)
            self.events.put({"_done": True, "results": rows})
        except Exception as exc:
            self.events.put({"_fatal": True, "message": f"{type(exc).__name__}: {exc}"})

    def _poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event.get("_done"):
                    rows = event.get("results", [])
                    successes = sum(row.get("status") == "success" for row in rows)
                    failures = len(rows)-successes
                    self.results.set(f"성공 {successes}편 · 실패 {failures}편")
                    self.progress.set(100)
                    self.status.set("배치 제작 완료. 결과 영상과 제작 이력을 확인하세요." if not failures else "일부 영상 제작에 실패했습니다. 오류 로그를 확인하세요.")
                    for row in rows:
                        self._write_log(str(row.get("output_path", row.get("path", ""))) if row.get("status") == "success" else "실패: "+str(row.get("error", "원인 불명")))
                    self.start_button.configure(state="normal")
                    self.mode_box.configure(state="readonly")
                    self._refresh_history()
                elif event.get("_fatal"):
                    self.status.set("제작 중 오류가 발생했습니다. 로그를 확인하세요.")
                    self._write_log(event.get("message", "알 수 없는 오류"))
                    self.start_button.configure(state="normal")
                    self.mode_box.configure(state="readonly")
                    self._refresh_history()
                else:
                    message = str(event.get("message", event.get("stage", "")))
                    if message:
                        self.status.set(message)
                        self._write_log(message)
                    if "progress" in event:
                        total = max(1, int(event.get("total", 1)))
                        index = max(1, int(event.get("index", 1)))
                        fraction = max(0.0, min(1.0, float(event["progress"])))
                        self.progress.set(max(0, min(100, 100*((index-1)+fraction)/total)))
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _write_log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", message+"\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _refresh_history(self):
        for item in self.history.get_children():
            self.history.delete(item)
        database = history_path()
        if not database.is_file():
            return
        try:
            from .history import History
            store = History(database)
            try:
                rows = store.list_runs(limit=100)
            finally:
                if hasattr(store, "close"):
                    store.close()
            for row in rows:
                self.history.insert("", "end", values=(row.get("created_at", ""), row.get("status", ""), json.loads(row.get("quiz_json", "{}")).get("mode", "Shorts")+" · "+row.get("difficulty", ""), row.get("output_path", ""), row.get("error", "") or ""))
        except Exception as exc:
            self._write_log("제작 이력을 읽지 못했습니다: "+str(exc))

    def _open_history(self, _event=None):
        selection = self.history.selection()
        if not selection:
            return
        values = self.history.item(selection[0], "values")
        if len(values) > 3 and values[3]:
            path = Path(values[3])
            if path.is_dir():
                try:
                    open_folder(path)
                except Exception as exc:
                    messagebox.showerror("제작 이력", str(exc), parent=self)

    def _close(self):
        if self.worker is not None and self.worker.is_alive():
            messagebox.showinfo("제작 진행 중", "제작 중에는 창을 닫지 않습니다. 배치가 끝난 후 닫아 주세요.", parent=self)
            return
        self.destroy()


def launch():
    GeoRushApp().mainloop()
