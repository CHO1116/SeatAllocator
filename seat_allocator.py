from __future__ import annotations

import json
import os
import random
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from pathlib import Path

APP_NAME = "자리온"


def _get_app_dir() -> Path:
    # Windows: %APPDATA%\JariOn
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / "JariOn"

    # macOS: ~/Library/Application Support/JariOn
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "JariOn"

    # Linux/Unix: $XDG_CONFIG_HOME/JariOn or ~/.config/JariOn
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "JariOn"
    return Path.home() / ".config" / "JariOn"


APP_DIR = _get_app_dir()
CONFIG_PATH = APP_DIR / "settings.json"

COLORS = {
    "bg": "#F5F3EE", "paper": "#FFFFFF", "ink": "#202A43", "muted": "#788198",
    "line": "#E6E8EE", "navy": "#263A62", "blue": "#4E6FE8", "blue_soft": "#EEF1FF",
    "coral": "#F07F67", "mint": "#DDF3E9", "mint_ink": "#24765A", "gold": "#F5C96A",
    "seat": "#F8F9FC", "seat_line": "#DCE1EC", "fixed": "#FFF1E8", "fixed_line": "#F2B38C",
}


def load_config() -> dict:
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {"rows": 5, "cols": 5, "names": [], "fixed": {}, "pin": ""}


def save_config(data: dict) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(CONFIG_PATH)


class SeatAllocatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg = load_config()
        self.rows = self._bounded(self.cfg.get("rows", 5), 5)
        self.cols = self._bounded(self.cfg.get("cols", 5), 5)
        self.names = list(self.cfg.get("names", []))
        self.fixed = dict(self.cfg.get("fixed", {}))
        self.pin = str(self.cfg.get("pin", ""))
        try:
            self.seating: dict[int, str] = {int(k): str(v) for k, v in self.cfg.get("seating", {}).items()}
            self.seating = {k: v for k, v in self.seating.items() if 0 <= k < self.rows * self.cols and v in self.names}
        except (AttributeError, TypeError, ValueError):
            self.seating = {}
        self.animating = False
        self.animation_ticks = 0
        self._name_file = ""

        root.title(f"{APP_NAME} · 우리 반 자리 배치")
        root.configure(bg=COLORS["bg"])
        root.geometry("1280x900")
        root.minsize(1020, 720)
        root.option_add("*Font", ("Malgun Gothic", 10))
        self._style()
        self._build()
        self._refresh_all()
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    @staticmethod
    def _bounded(value, default):
        try:
            return max(1, min(8, int(value)))
        except (ValueError, TypeError):
            return default

    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["paper"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["ink"])
        style.configure("Card.TLabel", background=COLORS["paper"], foreground=COLORS["ink"])
        style.configure("Muted.Card.TLabel", background=COLORS["paper"], foreground=COLORS["muted"])
        style.configure("Title.TLabel", background=COLORS["bg"], foreground=COLORS["ink"], font=("Malgun Gothic", 22, "bold"))
        style.configure("Sub.TLabel", background=COLORS["bg"], foreground=COLORS["muted"], font=("Malgun Gothic", 10))
        style.configure("CardTitle.TLabel", background=COLORS["paper"], foreground=COLORS["ink"], font=("Malgun Gothic", 12, "bold"))
        style.configure("Primary.TButton", font=("Malgun Gothic", 13, "bold"), foreground="white", background=COLORS["blue"], padding=(24, 13), borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#3E5DD1"), ("disabled", "#AAB5E8")])
        style.configure("Secondary.TButton", font=("Malgun Gothic", 10, "bold"), foreground=COLORS["navy"], background=COLORS["blue_soft"], padding=(12, 8), borderwidth=0)
        style.map("Secondary.TButton", background=[("active", "#E1E6FF")])
        style.configure("Small.TButton", font=("Malgun Gothic", 9), foreground=COLORS["navy"], background=COLORS["paper"], padding=(8, 5), borderwidth=0)
        style.map("Small.TButton", background=[("active", "#F3F5FA")])
        style.configure("Treeview", font=("Malgun Gothic", 10), rowheight=30, background=COLORS["paper"], fieldbackground=COLORS["paper"], foreground=COLORS["ink"], borderwidth=0)
        style.configure("Treeview.Heading", font=("Malgun Gothic", 9, "bold"), background="#F7F8FB", foreground=COLORS["muted"], relief="flat")
        style.map("Treeview", background=[("selected", COLORS["blue_soft"])], foreground=[("selected", COLORS["navy"])])

    def _build(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        header = ttk.Frame(self.root, padding=(28, 20, 28, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        mark = tk.Canvas(header, width=42, height=42, bg=COLORS["bg"], highlightthickness=0)
        mark.grid(row=0, column=0, rowspan=2, padx=(0, 13))
        mark.create_oval(2, 2, 40, 40, fill=COLORS["navy"], outline="")
        mark.create_text(21, 21, text="✳", fill=COLORS["gold"], font=("Segoe UI Symbol", 21, "bold"))
        ttk.Label(header, text="자리온", style="Title.TLabel").grid(row=0, column=1, sticky="sw")
        ttk.Label(header, text="오늘의 교실, 설레는 자리 바꾸기", style="Sub.TLabel").grid(row=1, column=1, sticky="nw", pady=(1, 0))
        self.status_var = tk.StringVar(value="준비됐어요")
        tk.Label(header, textvariable=self.status_var, bg=COLORS["mint"], fg=COLORS["mint_ink"], padx=12, pady=7, font=("Malgun Gothic", 9, "bold")).grid(row=0, column=2, rowspan=2, padx=12)
        self.settings_btn = ttk.Button(header, text="⚙  교사 설정", style="Small.TButton", command=self._teacher_settings)
        self.settings_btn.grid(row=0, column=3, rowspan=2, sticky="e")

        body = ttk.Frame(self.root, padding=(28, 10, 28, 18))
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)
        self._build_front(body)
        content = ttk.Frame(body)
        content.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        self._build_seating(content)
        self._build_roster(content)
        footer = ttk.Frame(body)
        footer.grid(row=2, column=0, sticky="ew", pady=(13, 0))
        footer.grid_columnconfigure(0, weight=1)
        self.hint_var = tk.StringVar(value="명단을 불러오면 자리를 배치할 수 있어요.")
        ttk.Label(footer, textvariable=self.hint_var, style="Sub.TLabel").grid(row=0, column=0, sticky="w")
        self.draw_btn = ttk.Button(footer, text="✦   자리 배치하기", style="Primary.TButton", command=self._start_draw)
        self.draw_btn.grid(row=0, column=1, sticky="e")

    def _build_front(self, parent):
        card = tk.Frame(parent, bg=COLORS["navy"], height=178, highlightthickness=0)
        card.grid(row=0, column=0, sticky="ew")
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)
        left = tk.Frame(card, bg=COLORS["navy"])
        left.place(relx=.07, rely=.29, anchor="w")
        tk.Label(left, text="칠판", bg=COLORS["navy"], fg="#B8C5E0", font=("Malgun Gothic", 9, "bold")).pack(anchor="w")
        tk.Label(left, text="앞쪽", bg=COLORS["navy"], fg="white", font=("Malgun Gothic", 19, "bold")).pack(anchor="w", pady=(4, 3))
        tk.Label(left, text="선생님을 바라보는 방향이에요", bg=COLORS["navy"], fg="#C8D1E3", font=("Malgun Gothic", 9)).pack(anchor="w")
        self.teacher_canvas = tk.Canvas(card, width=230, height=166, bg=COLORS["navy"], highlightthickness=0)
        self.teacher_canvas.place(relx=.5, rely=1.0, anchor="s")
        self._draw_teacher()
        tk.Label(card, text="오늘은 어떤 자리가 기다릴까요?", bg=COLORS["navy"], fg="#E7ECF6", font=("Malgun Gothic", 11, "bold")).place(relx=.91, rely=.45, anchor="e")
        tk.Label(card, text="모두에게 새로운 이웃이 생겨요", bg=COLORS["navy"], fg="#AEBBD5", font=("Malgun Gothic", 9)).place(relx=.91, rely=.62, anchor="e")

    def _draw_teacher(self):
        c = self.teacher_canvas
        c.delete("all")
        # Chalkboard and small sparkle details
        c.create_rectangle(20, 17, 210, 93, fill="#33543F", outline="#D4B77B", width=5)
        c.create_line(30, 86, 200, 86, fill="#54745B", width=1)
        c.create_text(114, 48, text="함께 배우고\n함께 웃는 우리 반", fill="#F4EBCF", font=("Malgun Gothic", 11, "bold"), justify="center")
        c.create_text(41, 35, text="✦", fill="#F5C96A", font=("Segoe UI Symbol", 12))
        c.create_text(185, 68, text="✧", fill="#E6D7A8", font=("Segoe UI Symbol", 11))
        # teacher: friendly illustrated face, hair, blouse and arms
        c.create_oval(87, 77, 143, 132, fill="#F2BE9D", outline="")
        c.create_oval(83, 76, 147, 111, fill="#342D38", outline="")
        c.create_oval(82, 94, 92, 120, fill="#342D38", outline="")
        c.create_oval(138, 94, 148, 120, fill="#342D38", outline="")
        c.create_oval(101, 101, 106, 106, fill="#382F35", outline="")
        c.create_oval(124, 101, 129, 106, fill="#382F35", outline="")
        c.create_arc(105, 108, 126, 124, start=205, extent=130, style="arc", outline="#B85550", width=2)
        c.create_polygon(88, 127, 142, 127, 164, 162, 68, 162, fill="#F08A72", outline="")
        c.create_polygon(109, 128, 116, 138, 123, 128, 118, 145, fill="#FFF6EF", outline="")
        c.create_line(83, 138, 66, 153, fill="#F2BE9D", width=8, capstyle="round")
        c.create_line(148, 138, 166, 151, fill="#F2BE9D", width=8, capstyle="round")
        # podium
        c.create_rectangle(53, 151, 178, 169, fill="#C99562", outline="")
        c.create_rectangle(53, 151, 178, 155, fill="#E3B77F", outline="")
        c.create_text(114, 161, text="우리 반", fill="#795333", font=("Malgun Gothic", 8, "bold"))

    def _build_seating(self, parent):
        self.seat_card = tk.Frame(parent, bg=COLORS["paper"], highlightbackground=COLORS["line"], highlightthickness=1)
        self.seat_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.seat_card.grid_columnconfigure(0, weight=1)
        self.seat_card.grid_rowconfigure(1, weight=1)
        top = tk.Frame(self.seat_card, bg=COLORS["paper"])
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 5))
        top.grid_columnconfigure(0, weight=1)
        tk.Label(top, text="자리 배치", bg=COLORS["paper"], fg=COLORS["ink"], font=("Malgun Gothic", 13, "bold")).grid(row=0, column=0, sticky="w")
        self.size_var = tk.StringVar()
        tk.Label(top, textvariable=self.size_var, bg=COLORS["paper"], fg=COLORS["muted"], font=("Malgun Gothic", 9)).grid(row=0, column=1, sticky="e")
        self.board = tk.Canvas(self.seat_card, bg=COLORS["paper"], highlightthickness=0)
        self.board.grid(row=1, column=0, sticky="nsew", padx=20, pady=(2, 16))
        self.board.bind("<Configure>", lambda _e: self._render_seats())

    def _build_roster(self, parent):
        self.roster_card = tk.Frame(parent, bg=COLORS["paper"], width=270, highlightbackground=COLORS["line"], highlightthickness=1)
        self.roster_card.grid(row=0, column=1, sticky="ns")
        self.roster_card.grid_propagate(False)
        tk.Label(self.roster_card, text="우리 반 명단", bg=COLORS["paper"], fg=COLORS["ink"], font=("Malgun Gothic", 12, "bold")).pack(anchor="w", padx=17, pady=(17, 2))
        self.roster_count = tk.Label(self.roster_card, text="아직 명단이 없어요", bg=COLORS["paper"], fg=COLORS["muted"], font=("Malgun Gothic", 9))
        self.roster_count.pack(anchor="w", padx=17, pady=(0, 11))
        self.roster_tree = ttk.Treeview(self.roster_card, columns=("name",), show="headings", selectmode="browse")
        self.roster_tree.heading("name", text="학생 이름")
        self.roster_tree.column("name", anchor="w", width=210)
        self.roster_tree.pack(fill="both", expand=True, padx=12)
        self.roster_tree.tag_configure("assigned", foreground=COLORS["mint_ink"])
        actions = tk.Frame(self.roster_card, bg=COLORS["paper"])
        actions.pack(fill="x", padx=13, pady=12)
        ttk.Button(actions, text="＋ 이름 입력", style="Secondary.TButton", command=self._add_name_dialog).pack(fill="x", pady=(0, 7))
        ttk.Button(actions, text="▤  명단 파일 불러오기", style="Secondary.TButton", command=self._import_names).pack(fill="x")
        tk.Label(self.roster_card, text="TXT 파일 · 한 줄에 한 명", bg=COLORS["paper"], fg=COLORS["muted"], font=("Malgun Gothic", 8)).pack(pady=(0, 12))

    def _refresh_all(self):
        capacity = self.rows * self.cols
        self.size_var.set(f"{self.rows} × {self.cols}  ·  {capacity}석")
        self.roster_count.configure(text=f"{len(self.names)}명 등록 · {capacity}석")
        self.roster_tree.delete(*self.roster_tree.get_children())
        placed_names = set(self.seating.values())
        for name in self.names:
            tag = ("assigned",) if name in placed_names else ()
            self.roster_tree.insert("", "end", values=(name,), tags=tag)
        self._render_seats()
        self.status_var.set("명단을 불러와 주세요" if not self.names else f"학생 {len(self.names)}명 준비 완료")

    def _render_seats(self):
        if not hasattr(self, "board"):
            return
        c = self.board
        c.delete("all")
        w, h = max(200, c.winfo_width()), max(200, c.winfo_height())
        gap = 9 if self.cols <= 6 else 5
        rows = self.rows
        cols = self.cols
        cell_w = min((w - 8 - (cols - 1) * gap) / cols, 145)
        cell_h = min((h - 8 - (rows - 1) * gap) / rows, 82)
        total_w, total_h = cols * cell_w + (cols - 1) * gap, rows * cell_h + (rows - 1) * gap
        x0, y0 = (w - total_w) / 2, (h - total_h) / 2
        for r in range(rows):
            for col in range(cols):
                seat = r * cols + col
                x, y = x0 + col * (cell_w + gap), y0 + r * (cell_h + gap)
                name = self.seating.get(seat, "")
                # Fixed assignments are intentionally indistinguishable in the student-facing view.
                fill = "#EFF2FF" if name else COLORS["seat"]
                outline = "#B9C5FF" if name else COLORS["seat_line"]
                c.create_rectangle(x, y, x + cell_w, y + cell_h, fill=fill, outline=outline, width=1.3)
                c.create_oval(x + 9, y + 9, x + 29, y + 29, fill="#E7EAFE", outline="")
                c.create_text(x + 19, y + 19, text=f"{r+1}-{col+1}", fill=COLORS["blue"], font=("Malgun Gothic", 7, "bold"))
                if name:
                    c.create_text(x + cell_w / 2, y + cell_h / 2 + 8, text=name, fill=COLORS["ink"], font=("Malgun Gothic", 11, "bold"), width=cell_w - 12)
                else:
                    c.create_text(x + cell_w / 2, y + cell_h / 2 + 7, text="빈 자리", fill="#AAB1C0", font=("Malgun Gothic", 9))

    def _import_names(self):
        path = filedialog.askopenfilename(title="학생 명단 텍스트 파일 선택", filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")])
        if not path:
            return
        try:
            raw = Path(path).read_bytes()
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = raw.decode("cp949")
            names = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
            # Also accept comma separated entries while keeping one-name-per-line as the suggested format.
            names = [part.strip() for line in names for part in line.split(",") if part.strip()]
            names = list(dict.fromkeys(names))
            if not names:
                messagebox.showwarning("명단 확인", "파일에서 이름을 찾지 못했어요.", parent=self.root)
                return
            self.names = names
            self.seating = {}
            self._name_file = path
            self._persist()
            self._refresh_all()
            self.hint_var.set(f"{len(names)}명의 명단을 불러왔어요. 준비되면 배치를 눌러 주세요.")
            if len(names) > self.rows * self.cols:
                messagebox.showinfo("좌석 수 확인", f"학생은 {len(names)}명이고 좌석은 {self.rows * self.cols}석이에요. 교사 설정에서 좌석 수를 늘릴 수 있어요.", parent=self.root)
        except OSError as e:
            messagebox.showerror("파일 열기 실패", str(e), parent=self.root)

    def _add_name_dialog(self):
        value = simpledialog.askstring("학생 이름 입력", "추가할 이름을 입력하세요.", parent=self.root)
        if value and value.strip():
            name = value.strip()
            if name not in self.names:
                self.names.append(name)
                self._persist()
                self._refresh_all()

    def _teacher_settings(self):
        if not self.pin:
            pin = simpledialog.askstring("교사 전용 설정", "처음 사용합니다. 교사 PIN을 설정해 주세요.\n이 PIN으로 설정 화면을 보호합니다.", show="●", parent=self.root)
            if pin is None:
                return
            pin = pin.strip()
            if len(pin) < 4:
                messagebox.showwarning("PIN 설정", "PIN은 4자 이상으로 설정해 주세요.", parent=self.root)
                return
            self.pin = pin
            self._persist()
            self._open_settings()
            return
        entered = simpledialog.askstring("교사 전용 설정", "교사 PIN을 입력하세요.", show="●", parent=self.root)
        if entered is None:
            return
        if entered.strip() != self.pin:
            messagebox.showerror("PIN 확인", "PIN이 맞지 않아요.", parent=self.root)
            return
        self._open_settings()

    def _open_settings(self):
        working_fixed = dict(self.fixed)
        win = tk.Toplevel(self.root)
        win.title("교사 전용 설정")
        win.configure(bg=COLORS["bg"])
        win.geometry("650x590")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()
        outer = tk.Frame(win, bg=COLORS["bg"], padx=22, pady=20)
        outer.pack(fill="both", expand=True)
        tk.Label(outer, text="교사 전용 설정", bg=COLORS["bg"], fg=COLORS["ink"], font=("Malgun Gothic", 18, "bold")).pack(anchor="w")
        tk.Label(outer, text="학생 화면에는 설정 내용이 표시되지 않아요. 변경한 내용은 저장하고 닫아야 적용돼요.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Malgun Gothic", 9)).pack(anchor="w", pady=(2, 15))
        dims = tk.Frame(outer, bg=COLORS["paper"], padx=15, pady=13, highlightbackground=COLORS["line"], highlightthickness=1)
        dims.pack(fill="x")
        tk.Label(dims, text="책상 배치", bg=COLORS["paper"], fg=COLORS["ink"], font=("Malgun Gothic", 10, "bold")).grid(row=0, column=0, sticky="w")
        rows_v, cols_v = tk.IntVar(value=self.rows), tk.IntVar(value=self.cols)
        tk.Spinbox(dims, from_=1, to=8, width=5, textvariable=rows_v, font=("Malgun Gothic", 10), relief="solid", bd=1).grid(row=0, column=1, padx=(20, 5))
        tk.Label(dims, text="행 ×", bg=COLORS["paper"], fg=COLORS["muted"]).grid(row=0, column=2)
        tk.Spinbox(dims, from_=1, to=8, width=5, textvariable=cols_v, font=("Malgun Gothic", 10), relief="solid", bd=1).grid(row=0, column=3, padx=5)
        tk.Label(dims, text="열  (각 1~8)", bg=COLORS["paper"], fg=COLORS["muted"]).grid(row=0, column=4, sticky="w")

        fixed_box = tk.Frame(outer, bg=COLORS["paper"], padx=15, pady=13, highlightbackground=COLORS["line"], highlightthickness=1)
        fixed_box.pack(fill="both", expand=True, pady=14)
        tk.Label(fixed_box, text="미리 지정할 자리", bg=COLORS["paper"], fg=COLORS["ink"], font=("Malgun Gothic", 10, "bold")).pack(anchor="w")
        tk.Label(fixed_box, text="지정한 학생은 매번 같은 책상에 배정돼요.", bg=COLORS["paper"], fg=COLORS["muted"], font=("Malgun Gothic", 9)).pack(anchor="w", pady=(2, 9))
        list_frame = tk.Frame(fixed_box, bg=COLORS["paper"])
        list_frame.pack(fill="both", expand=True)
        columns = ("student", "seat")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        tree.heading("student", text="학생")
        tree.heading("seat", text="지정 좌석")
        tree.column("student", width=240)
        tree.column("seat", width=170, anchor="center")
        tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)
        for student, seat in working_fixed.items():
            tree.insert("", "end", iid=student, values=(student, seat))

        addrow = tk.Frame(fixed_box, bg=COLORS["paper"])
        addrow.pack(fill="x", pady=(10, 0))
        student_var = tk.StringVar(value=self.names[0] if self.names else "")
        student_combo = ttk.Combobox(addrow, textvariable=student_var, values=self.names, state="readonly", width=24)
        student_combo.pack(side="left")
        seat_var = tk.StringVar(value="1행 1열")
        seat_combo = ttk.Combobox(addrow, textvariable=seat_var, state="readonly", width=15)
        seat_combo.pack(side="left", padx=8)

        def update_seat_options(*_):
            rr, cc = self._bounded(rows_v.get(), self.rows), self._bounded(cols_v.get(), self.cols)
            opts = [f"{r+1}행 {c+1}열" for r in range(rr) for c in range(cc)]
            seat_combo.configure(values=opts)
            if seat_var.get() not in opts:
                seat_var.set(opts[0])
        rows_v.trace_add("write", update_seat_options)
        cols_v.trace_add("write", update_seat_options)
        update_seat_options()

        def add_fixed():
            student = student_var.get()
            seat = seat_var.get()
            if not student:
                messagebox.showinfo("학생 선택", "먼저 명단을 불러와 주세요.", parent=win)
                return
            if any(s == seat and n != student for n, s in working_fixed.items()):
                messagebox.showwarning("좌석 중복", "이미 다른 학생에게 지정된 자리예요.", parent=win)
                return
            working_fixed[student] = seat
            if tree.exists(student):
                tree.item(student, values=(student, seat))
            else:
                tree.insert("", "end", iid=student, values=(student, seat))
        def remove_fixed():
            selected = tree.selection()
            if selected:
                student = selected[0]
                working_fixed.pop(student, None)
                tree.delete(student)
        ttk.Button(addrow, text="자리 지정", style="Secondary.TButton", command=add_fixed).pack(side="left")
        ttk.Button(addrow, text="선택 삭제", style="Small.TButton", command=remove_fixed).pack(side="left", padx=5)

        buttons = tk.Frame(outer, bg=COLORS["bg"])
        buttons.pack(fill="x")
        def save_and_close():
            self.rows = self._bounded(rows_v.get(), 5)
            self.cols = self._bounded(cols_v.get(), 5)
            self.fixed = working_fixed
            # Keep the configuration intact; fixed seats outside the new layout are ignored until expanded again.
            self.seating = {}
            self._persist()
            self._refresh_all()
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", save_and_close)
        win.bind("<Escape>", lambda _event: win.destroy())
        ttk.Button(buttons, text="변경 취소", style="Small.TButton", command=win.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="저장하고 닫기", style="Secondary.TButton", command=save_and_close).pack(side="right")
        ttk.Button(buttons, text="PIN 변경", style="Small.TButton", command=lambda: self._change_pin(win)).pack(side="left")

    def _change_pin(self, parent):
        current = simpledialog.askstring("PIN 변경", "현재 PIN을 입력하세요.", show="●", parent=parent)
        if current is None:
            return
        if current.strip() != self.pin:
            messagebox.showerror("PIN 확인", "현재 PIN이 맞지 않아요.", parent=parent)
            return
        new = simpledialog.askstring("PIN 변경", "새 PIN을 입력하세요. (4자 이상)", show="●", parent=parent)
        if new is None:
            return
        new = new.strip()
        if len(new) < 4:
            messagebox.showwarning("PIN 확인", "PIN은 4자 이상으로 설정해 주세요.", parent=parent)
            return
        self.pin = new
        self._persist()
        messagebox.showinfo("PIN 변경", "새 PIN을 저장했어요.", parent=parent)

    def _start_draw(self):
        if self.animating:
            return
        if not self.names:
            self._import_names()
            if not self.names:
                return
        cap = self.rows * self.cols
        if len(self.names) > cap:
            messagebox.showwarning("좌석이 부족해요", f"학생 {len(self.names)}명에 비해 좌석은 {cap}석이에요.\n교사 설정에서 행과 열을 늘려 주세요.", parent=self.root)
            return
        invalid = [n for n in self.fixed if n not in self.names]
        if invalid:
            messagebox.showwarning("지정 좌석 확인", "명단에 없는 학생의 지정 좌석이 있어요. 교사 설정에서 확인해 주세요.", parent=self.root)
            return
        fixed_seats = {}
        for name, label in self.fixed.items():
            try:
                rr, cc = label.replace("행", "").replace("열", "").split()
                idx = (int(rr)-1) * self.cols + int(cc)-1
                if int(rr) > self.rows or int(cc) > self.cols:
                    raise ValueError
                if idx in fixed_seats.values():
                    raise ValueError
                fixed_seats[name] = idx
            except (ValueError, TypeError):
                messagebox.showwarning("지정 좌석 확인", f"'{name}' 학생의 좌석 설정이 현재 배치와 맞지 않아요. 교사 설정에서 확인해 주세요.", parent=self.root)
                return
        remaining_seats = [i for i in range(cap) if i not in fixed_seats.values()]
        remaining_names = [n for n in self.names if n not in fixed_seats]
        random.shuffle(remaining_names)
        target = dict(fixed_seats)
        target.update({name: seat for name, seat in zip(remaining_names, remaining_seats)})
        self.target_seating = {seat: name for name, seat in target.items()}
        self.animating = True
        self.animation_ticks = 0
        self.draw_btn.configure(state="disabled", text="자리 섞는 중…")
        self.settings_btn.configure(state="disabled")
        self.status_var.set("두근두근, 자리를 섞고 있어요")
        self.hint_var.set("새로운 이웃을 만날 준비를 해요!")
        self._animate()

    def _animate(self):
        self.animation_ticks += 1
        if self.animation_ticks < 18:
            seats = list(range(self.rows * self.cols))
            random.shuffle(seats)
            names = self.names[:]
            random.shuffle(names)
            self.seating = {seat: name for seat, name in zip(seats, names)}
            self._render_seats()
            self.root.after(90 + self.animation_ticks * 4, self._animate)
        else:
            self.seating = self.target_seating
            self.animating = False
            self.draw_btn.configure(state="normal", text="✦   다시 배치하기")
            self.settings_btn.configure(state="normal")
            self.status_var.set("자리 배치 완���!")
            self.hint_var.set("새로운 자리를 확인해 보세요. 지정된 자리는 매번 그대로예요.")
            self._render_seats()
            self._refresh_roster_only()
            self._persist()

    def _refresh_roster_only(self):
        self.roster_tree.delete(*self.roster_tree.get_children())
        placed = set(self.seating.values())
        for name in self.names:
            self.roster_tree.insert("", "end", values=(name,), tags=(("assigned",) if name in placed else ()))

    def _persist(self):
        self.cfg.update({"rows": self.rows, "cols": self.cols, "names": self.names, "fixed": self.fixed,
                         "pin": self.pin, "seating": {str(k): v for k, v in self.seating.items()}})
        try:
            save_config(self.cfg)
        except OSError as e:
            messagebox.showwarning("저장할 수 없어요", f"설정 파일을 저장하지 못했어요.\n{e}", parent=self.root)

    def _on_close(self):
        self._persist()
        self.root.destroy()


def main():
    root = tk.Tk()
    SeatAllocatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
