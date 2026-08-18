import calendar
import customtkinter as ctk
from datetime import date

MIN_YEAR = 2020


def _popup_close_on_outside(popup, anchor):
    """클릭 외부 감지 → 팝업 자동 닫기. 150ms 후 바인딩 시작(생성 클릭 무시)."""
    root = anchor.winfo_toplevel()
    state = {"bid": None}

    def check(event):
        try:
            if not popup.winfo_exists():
                cleanup()
                return
            px, py = popup.winfo_rootx(), popup.winfo_rooty()
            pw, ph = popup.winfo_width(), popup.winfo_height()
            if not (px <= event.x_root <= px + pw and py <= event.y_root <= py + ph):
                close()
        except Exception:
            cleanup()

    def cleanup():
        if state["bid"]:
            try:
                root.unbind("<Button-1>", state["bid"])
            except Exception:
                pass
            state["bid"] = None

    def close():
        cleanup()
        try:
            popup.destroy()
        except Exception:
            pass

    def start():
        state["bid"] = root.bind("<Button-1>", check, add=True)

    popup.after(150, start)
    popup.bind("<Escape>", lambda e: close())
    return cleanup


class _YearPopup(ctk.CTkToplevel):
    def __init__(self, anchor, year_var, on_select, lang="ko"):
        super().__init__(anchor.winfo_toplevel())
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._cleanup = _popup_close_on_outside(self, anchor)
        cur = int(year_var.get())
        today = date.today()
        f = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=6)
        f.pack(fill="both", expand=True, padx=1, pady=1)
        for y in range(today.year, MIN_YEAR - 1, -1):
            fg = "#1a56db" if y == cur else "transparent"
            tc = "white" if y == cur else ("gray10", "white")
            y_label = str(y) if lang == "en" else f"{y}년"
            ctk.CTkButton(f, text=y_label, height=30, font=ctk.CTkFont(size=13),
                          fg_color=fg, text_color=tc, hover_color="#dbeafe",
                          command=lambda y=y: self._sel(y, on_select)).pack(fill="x", pady=1, padx=2)
        self.update_idletasks()
        x = anchor.winfo_rootx()
        y_pos = anchor.winfo_rooty() + anchor.winfo_height() + 2
        h = min(self.winfo_reqheight(), 260)
        self.geometry(f"{self.winfo_reqwidth()}x{h}+{x}+{y_pos}")
        self.lift()

    def _sel(self, y, cb):
        self._cleanup()
        cb(y)
        try:
            self.destroy()
        except Exception:
            pass


_MONTH_ABBR_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class _MonthPopup(ctk.CTkToplevel):
    def __init__(self, anchor, year_var, month_var, on_select, lang="ko"):
        super().__init__(anchor.winfo_toplevel())
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._cleanup = _popup_close_on_outside(self, anchor)
        today = date.today()
        y = int(year_var.get())
        sel = int(month_var.get())
        f = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=6)
        f.pack(fill="both", expand=True, padx=1, pady=1)
        grid = ctk.CTkFrame(f, fg_color="transparent")
        grid.pack(padx=2, pady=2)
        for i in range(12):
            m = i + 1
            r, c = divmod(i, 4)
            is_future = y > today.year or (y == today.year and m > today.month)
            is_sel = (m == sel)
            fg = "#1a56db" if is_sel else ("transparent" if not is_future else ("gray80", "gray35"))
            tc = "white" if is_sel else (("gray55", "gray50") if is_future else ("gray10", "white"))
            state = "disabled" if is_future else "normal"
            m_label = _MONTH_ABBR_EN[i] if lang == "en" else f"{m}월"
            ctk.CTkButton(grid, text=m_label, width=52, height=28,
                          font=ctk.CTkFont(size=12), fg_color=fg, text_color=tc,
                          state=state, hover_color="#dbeafe",
                          command=lambda m=m: self._sel(m, on_select)).grid(row=r, column=c, padx=1, pady=1)
        self.update_idletasks()
        x = anchor.winfo_rootx()
        y_pos = anchor.winfo_rooty() + anchor.winfo_height() + 2
        self.geometry(f"{self.winfo_reqwidth()}x{self.winfo_reqheight()}+{x}+{y_pos}")
        self.lift()

    def _sel(self, m, cb):
        self._cleanup()
        cb(m)
        try:
            self.destroy()
        except Exception:
            pass


class CalendarDialog(ctk.CTkToplevel):
    def __init__(self, master, current: date, on_select, lang="ko"):
        super().__init__(master)
        self.on_select = on_select
        self.lang = lang
        self.title("Select Date" if lang == "en" else "날짜 선택")
        self.resizable(False, False)
        today = date.today()
        if current > today:
            current = today
        if current.year < MIN_YEAR:
            current = date(MIN_YEAR, 1, 1)
        self._selected = current
        self._vy = current.year
        self._vm = current.month
        self._cleanup_fn = _popup_close_on_outside(self, master)
        self._build()

    def _build(self):
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkButton(nav, text="◀", width=28, height=28, font=ctk.CTkFont(size=12),
                      command=self._prev_month).pack(side="left")
        self._nav_lbl = ctk.CTkLabel(nav, text="", font=ctk.CTkFont(size=14, weight="bold"), width=180)
        self._nav_lbl.pack(side="left", expand=True)
        ctk.CTkButton(nav, text="▶", width=28, height=28, font=ctk.CTkFont(size=12),
                      command=self._next_month).pack(side="right")
        self._gf = ctk.CTkFrame(self, fg_color="transparent")
        self._gf.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._refresh()

    def _refresh(self):
        for w in self._gf.winfo_children():
            w.destroy()
        y, m = self._vy, self._vm
        nav_text = f"{_MONTH_ABBR_EN[m-1]} {y}" if self.lang == "en" else f"{y}년 {m}월"
        self._nav_lbl.configure(text=nav_text)
        today = date.today()
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] if self.lang == "en" \
                    else ["월", "화", "수", "목", "금", "토", "일"]
        for i, h in enumerate(day_names):
            c = "#e53e3e" if i == 6 else ("#1a56db" if i == 5 else "gray")
            ctk.CTkLabel(self._gf, text=h, width=36, height=24,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=c).grid(row=0, column=i, padx=1, pady=1)
        first_wd = date(y, m, 1).weekday()
        days_in_month = calendar.monthrange(y, m)[1]
        min_d = date(MIN_YEAR, 1, 1)
        row, col = 1, first_wd
        for day in range(1, days_in_month + 1):
            d = date(y, m, day)
            disabled = d > today or d < min_d
            is_sel = (d == self._selected)
            is_today = (d == today)
            if is_sel:
                fg, tc = "#1a56db", "white"
            elif is_today:
                fg, tc = "#dbeafe", "#1a56db"
            else:
                fg, tc = "transparent", ("gray10", "white")
            if disabled:
                ctk.CTkLabel(self._gf, text=str(day), width=36, height=28,
                             font=ctk.CTkFont(size=11),
                             text_color="gray").grid(row=row, column=col, padx=1, pady=1)
            else:
                ctk.CTkButton(self._gf, text=str(day), width=36, height=28,
                              font=ctk.CTkFont(size=11), fg_color=fg, text_color=tc,
                              hover_color="#bfdbfe",
                              command=lambda d=d: self._select(d)).grid(row=row, column=col, padx=1, pady=1)
            col += 1
            if col == 7:
                col = 0
                row += 1

    def _prev_month(self):
        if self._vm == 1:
            if self._vy <= MIN_YEAR:
                return
            self._vy -= 1
            self._vm = 12
        else:
            self._vm -= 1
        self._refresh()

    def _next_month(self):
        today = date.today()
        if self._vy == today.year and self._vm == today.month:
            return
        if self._vm == 12:
            self._vy += 1
            self._vm = 1
        else:
            self._vm += 1
        self._refresh()

    def _select(self, d: date):
        self._cleanup_fn()
        self.on_select(d)
        try:
            self.destroy()
        except Exception:
            pass


class DateRow(ctk.CTkFrame):
    """날짜 입력 행: 년/월 클릭으로 팝업, 일 직접 입력 + 📅 버튼."""

    def __init__(self, master, on_change=None, lang="ko", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_change = on_change
        self.lang = lang
        today = date.today()
        self.year_var = ctk.StringVar(value=str(today.year))
        self.month_var = ctk.StringVar(value=f"{today.month:02d}")
        self.day_var = ctk.StringVar(value=f"{today.day:02d}")
        self._build()

    def _build(self):
        _lbl = lambda s: {"날짜": "Date", "년": "Y", "월": "M", "일": "D"}.get(s, s) \
                         if self.lang == "en" else s
        ctk.CTkLabel(self, text=_lbl("날짜"), font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 8))

        self._year_entry = ctk.CTkEntry(self, textvariable=self.year_var, width=70, height=32,
                                         font=ctk.CTkFont(size=13))
        self._year_entry.pack(side="left", padx=(0, 2))
        self._year_entry.bind("<Return>", lambda e: self._notify())
        self._year_entry.bind("<Button-1>", lambda e: self.after(50, self._open_year_picker))
        ctk.CTkLabel(self, text=_lbl("년"), font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 8))

        self._month_entry = ctk.CTkEntry(self, textvariable=self.month_var, width=44, height=32,
                                          font=ctk.CTkFont(size=13))
        self._month_entry.pack(side="left", padx=(0, 2))
        self._month_entry.bind("<Return>", lambda e: self._notify())
        self._month_entry.bind("<Button-1>", lambda e: self.after(50, self._open_month_picker))
        ctk.CTkLabel(self, text=_lbl("월"), font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 8))

        self._day_entry = ctk.CTkEntry(self, textvariable=self.day_var, width=44, height=32,
                                        font=ctk.CTkFont(size=13))
        self._day_entry.pack(side="left", padx=(0, 2))
        self._day_entry.bind("<Return>", lambda e: self._notify())
        self._day_entry.bind("<FocusOut>", lambda e: self._notify())

        ctk.CTkButton(self, text="📅", width=30, height=32, font=ctk.CTkFont(size=11),
                      command=self._open_calendar).pack(side="left", padx=(2, 4))
        ctk.CTkLabel(self, text=_lbl("일"), font=ctk.CTkFont(size=13)).pack(side="left")

    def _notify(self):
        if self.on_change:
            self.on_change(self.get_date_str())

    def get_date_str(self) -> str | None:
        try:
            y, m, d = int(self.year_var.get()), int(self.month_var.get()), int(self.day_var.get())
            return f"{y:04d}-{m:02d}-{d:02d}"
        except ValueError:
            return None

    def get_year_month(self) -> tuple[int, int] | None:
        try:
            return int(self.year_var.get()), int(self.month_var.get())
        except ValueError:
            return None

    def _open_year_picker(self):
        _YearPopup(self._year_entry, self.year_var, self._on_year_select, lang=self.lang)

    def _on_year_select(self, y: int):
        m = int(self.month_var.get())
        today = date.today()
        new_m = min(m, today.month) if y == today.year else m
        self._set_year_month(y, new_m)

    def _open_month_picker(self):
        _MonthPopup(self._month_entry, self.year_var, self.month_var, self._on_month_select, lang=self.lang)

    def _on_month_select(self, m: int):
        self._set_year_month(int(self.year_var.get()), m)

    def _set_year_month(self, y: int, m: int):
        max_day = calendar.monthrange(y, m)[1]
        try:
            d = min(int(self.day_var.get()), max_day)
        except ValueError:
            d = 1
        today = date.today()
        if y == today.year and m == today.month:
            d = min(d, today.day)
        self.year_var.set(str(y))
        self.month_var.set(f"{m:02d}")
        self.day_var.set(f"{d:02d}")
        self._notify()

    def _open_calendar(self):
        try:
            current = date(int(self.year_var.get()), int(self.month_var.get()), int(self.day_var.get()))
        except ValueError:
            current = date.today()
        dlg = CalendarDialog(self.winfo_toplevel(), current, self._on_cal_select, lang=self.lang)
        self.update_idletasks()
        x = self._day_entry.winfo_rootx()
        y_pos = self._day_entry.winfo_rooty() + self._day_entry.winfo_height() + 2
        dlg.geometry(f"310x300+{x}+{y_pos}")
        dlg.lift()
        dlg.focus_force()
        dlg.grab_set()

    def _on_cal_select(self, d: date):
        self.year_var.set(str(d.year))
        self.month_var.set(f"{d.month:02d}")
        self.day_var.set(f"{d.day:02d}")
        self._notify()
