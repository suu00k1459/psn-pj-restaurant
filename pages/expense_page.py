import customtkinter as ctk
from datetime import date
from utils import config_manager as cm
from utils import excel_manager as em
from utils.date_widgets import DateRow, MIN_YEAR
from utils.i18n import t as _t

EXPENSE_CATEGORIES = ["식재료 및 판관비", "시설 및 운영 관리비"]
CAT_SHORT = {"식재료 및 판관비": "식재료", "시설 및 운영 관리비": "시설/운영"}
CAT_COLOR = {"식재료 및 판관비": "#276749", "시설 및 운영 관리비": "#1a56db"}
CAT_FILTER_LABELS = ["전체", "식재료/판관비", "시설/운영관리"]
CAT_FILTER_MAP = {"전체": None, "식재료/판관비": "식재료 및 판관비", "시설/운영관리": "시설 및 운영 관리비"}

TAX_OPTIONS = ["면세", "5%", "18%", "27%"]
TAX_KEY_MAP = {"면세": "none", "5%": "5", "18%": "18", "27%": "27"}
TAX_LABEL_MAP = {"none": "면세", "5": "5%", "18": "18%", "27": "27%"}


# ─────────────────────────────────────────────
# 자동완성 입력 위젯
# ─────────────────────────────────────────────

class AutocompleteEntry(ctk.CTkFrame):
    def __init__(self, master, suggestions: list[str], hints: dict[str, str] = None,
                 width=140, height=32, font=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._suggestions = suggestions
        self._hints = hints or {}
        self._popup = None
        self._font = font or ctk.CTkFont(size=13)

        self._click_bind_id = None
        self.var = ctk.StringVar()
        self._entry = ctk.CTkEntry(self, textvariable=self.var, width=width, height=height, font=self._font)
        self._entry.pack(fill="x")
        self._entry.bind("<KeyRelease>", self._on_key)
        self._entry.bind("<Escape>", lambda e: self._hide())
        try:
            _inner = self._entry._entry
            _inner.bind("<Button-1>", lambda e: self.after(50, self._show_all))
            _inner.bind("<FocusIn>",  lambda e: self.after(50, self._show_all))
        except AttributeError:
            self._entry.bind("<FocusIn>", lambda e: self.after(50, self._show_all))

    def _show_all(self):
        text = self.var.get().strip()
        if text:
            tl = text.lower()
            matches = [s for s in self._suggestions if tl in s.lower()][:15]
        else:
            matches = self._suggestions[:15]
        if matches:
            self._show(matches)

    def _on_key(self, event):
        if event.keysym in ("Up", "Down", "Return", "Tab", "Escape"):
            return
        text = self.var.get().strip()
        if text:
            tl = text.lower()
            matches = [s for s in self._suggestions if tl in s.lower()][:15]
            if matches:
                self._show(matches)
                return
        elif self._suggestions:
            self._show(self._suggestions[:15])
            return
        self._hide()

    def _show(self, items: list[str]):
        import tkinter as tk
        self._hide()
        root = self.winfo_toplevel()

        self._popup = tk.Toplevel(root)
        self._popup.overrideredirect(True)
        self._popup.attributes("-topmost", True)

        bg_normal = "#f5f5f5"
        bg_hover  = "#dbeafe"

        outer = tk.Frame(self._popup, bg="#999999")
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=bg_normal)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        for item in items:
            hint = self._hints.get(item, "")
            display = f"{item}  ({hint})" if hint else item
            row = tk.Frame(inner, bg=bg_normal)
            row.pack(fill="x")
            lbl = tk.Label(row, text=display, anchor="w", bg=bg_normal,
                           font=("Segoe UI", 14), padx=10, pady=5, cursor="hand2")
            lbl.pack(fill="x")
            for w in (row, lbl):
                w.bind("<Enter>",         lambda e, r=row, l=lbl: (r.config(bg=bg_hover), l.config(bg=bg_hover)))
                w.bind("<Leave>",         lambda e, r=row, l=lbl: (r.config(bg=bg_normal), l.config(bg=bg_normal)))
                w.bind("<ButtonPress-1>", lambda e, v=item: self._select(v))

        self._popup.update_idletasks()
        ex    = self._entry.winfo_rootx()
        ey    = self._entry.winfo_rooty() + self._entry.winfo_height() + 2
        ew    = max(self._entry.winfo_width(), 200)
        eh    = self._popup.winfo_reqheight()
        self._popup.geometry(f"{ew}x{eh}+{ex}+{ey}")
        self._click_bind_id = root.bind("<ButtonPress-1>", self._on_global_click, add="+")

    def _on_global_click(self, event):
        if not self._popup:
            return
        try:
            px, py = self._popup.winfo_rootx(), self._popup.winfo_rooty()
            pw, ph = self._popup.winfo_width(), self._popup.winfo_height()
            if px <= event.x_root <= px + pw and py <= event.y_root <= py + ph:
                return
        except Exception:
            pass
        self._hide()

    def _select(self, value: str):
        self.var.set(value)
        self._hide()

    def _hide(self):
        if self._click_bind_id:
            try:
                self.winfo_toplevel().unbind("<ButtonPress-1>", self._click_bind_id)
            except Exception:
                pass
            self._click_bind_id = None
        if self._popup:
            try:
                self._popup.destroy()
            except Exception:
                pass
            self._popup = None

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: str):
        self.var.set(value)

    def update_suggestions(self, suggestions: list[str], hints: dict[str, str] = None):
        self._suggestions = suggestions
        if hints is not None:
            self._hints = hints


# ─────────────────────────────────────────────
# 세율 한 줄 (드롭다운 + 금액 + 삭제)
# ─────────────────────────────────────────────

class TaxLine(ctk.CTkFrame):
    def __init__(self, master, on_change, show_del=True):
        super().__init__(master, fg_color="transparent")

        self.rate_var = ctk.StringVar(value="면세")
        ctk.CTkComboBox(self, values=TAX_OPTIONS, variable=self.rate_var,
                        width=82, height=30, font=ctk.CTkFont(size=13),
                        command=lambda _: on_change()).pack(side="left", padx=(0, 6))

        self.amount_var = ctk.StringVar(value="0")
        e = ctk.CTkEntry(self, textvariable=self.amount_var, width=110, height=30,
                         font=ctk.CTkFont(size=13))
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda ev: on_change())

        if show_del:
            self._del_btn = ctk.CTkButton(self, text="×", width=28, height=28,
                                           fg_color="#e53e3e", hover_color="#c53030",
                                           font=ctk.CTkFont(size=14, weight="bold"))
            self._del_btn.pack(side="left", padx=(4, 0))
        else:
            self._del_btn = None

    def set_remove_command(self, cmd):
        if self._del_btn:
            self._del_btn.configure(command=cmd)

    def show_remove(self, show: bool):
        if self._del_btn:
            if show:
                self._del_btn.pack(side="left", padx=(4, 0))
            else:
                self._del_btn.pack_forget()

    def get(self) -> tuple[str, float]:
        try:
            amount = float(self.amount_var.get())
        except (ValueError, TypeError):
            amount = 0.0
        return TAX_KEY_MAP.get(self.rate_var.get(), "none"), amount

    def set_rate_amount(self, rate_key: str, amount: float):
        self.rate_var.set(TAX_LABEL_MAP.get(rate_key, "면세"))
        v = int(amount) if amount == int(amount) else amount
        self.amount_var.set(str(v))


# ─────────────────────────────────────────────
# 매입 입력 행
# ─────────────────────────────────────────────

class ExpenseRow(ctk.CTkFrame):
    def __init__(self, master, vendors: list[str], hints: dict[str, str], on_remove):
        super().__init__(master, fg_color=("gray91", "gray18"), corner_radius=8)
        self.on_remove = on_remove
        self._tax_lines: list[TaxLine] = []

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="x", padx=8, pady=(2, 2))

        irow = ctk.CTkFrame(outer, fg_color="transparent")
        irow.pack(fill="x")

        self._vendor_ac = AutocompleteEntry(irow, vendors, hints=hints, width=150)
        self._vendor_ac.pack(side="left", padx=(0, 8))

        pf = ctk.CTkFrame(irow, fg_color="transparent")
        pf.pack(side="left", padx=(0, 8))
        self.payment_var = ctk.StringVar(value="카드")
        self._cash_btn = ctk.CTkButton(pf, text="현금", width=46, height=30,
                                       font=ctk.CTkFont(size=12),
                                       command=lambda: self._set_pay("현금"))
        self._cash_btn.pack(side="left", padx=(0, 2))
        self._card_btn = ctk.CTkButton(pf, text="카드", width=46, height=30,
                                       font=ctk.CTkFont(size=12),
                                       command=lambda: self._set_pay("카드"))
        self._card_btn.pack(side="left")
        self._update_pay()

        first_tf = ctk.CTkFrame(irow, fg_color="transparent")
        first_tf.pack(side="left", padx=(0, 8))
        first = TaxLine(first_tf, on_change=self._recalc, show_del=False)
        first.pack(side="left")
        self._tax_lines.append(first)

        self.note_var = ctk.StringVar()
        ctk.CTkEntry(irow, textvariable=self.note_var, width=130,
                     placeholder_text="선택사항",
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(irow, text="삭제", width=46, height=28, fg_color="#e53e3e",
                      hover_color="#c53030", font=ctk.CTkFont(size=12),
                      command=self._remove).pack(side="left", padx=(0, 4))
        ctk.CTkButton(irow, text="+ 세율", width=56, height=28,
                      font=ctk.CTkFont(size=12),
                      command=self._add_extra_tax).pack(side="left")

        self._extra_container = ctk.CTkFrame(outer, fg_color="transparent")
        self._extra_packed = False

        self._total_row = ctk.CTkFrame(outer, fg_color="transparent")
        self.total_var = ctk.StringVar(value="0 ft")
        ctk.CTkLabel(self._total_row, text="합계:",
                     font=ctk.CTkFont(size=12), text_color="gray50").pack(side="right", padx=(0, 4))
        ctk.CTkLabel(self._total_row, textvariable=self.total_var,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#1a56db", width=110).pack(side="right")

        self._recalc()

    # ── Extra tax lines ─────────────────────────────────────────────────

    def _add_extra_tax(self):
        if not self._extra_packed:
            self._extra_container.pack(fill="x")
            self._extra_packed = True

        erow = ctk.CTkFrame(self._extra_container, fg_color="transparent")
        erow.pack(fill="x", pady=1)

        ctk.CTkLabel(erow, text="", width=260, fg_color="transparent").pack(side="left")
        line = TaxLine(erow, on_change=self._recalc, show_del=False)
        line.pack(side="left")
        self._tax_lines.append(line)
        line.set_remove_command(lambda l=line, r=erow: self._remove_extra(l, r))
        line.show_remove(True)

        if len(self._tax_lines) > 1:
            self._total_row.pack(fill="x", pady=(1, 0))
        self._recalc()

    def _remove_extra(self, line: "TaxLine", row_frame):
        if line in self._tax_lines:
            self._tax_lines.remove(line)
        row_frame.destroy()
        if len(self._tax_lines) <= 1:
            self._total_row.pack_forget()
            self._extra_container.pack_forget()
            self._extra_packed = False
        self._recalc()

    # ── Payment ─────────────────────────────────────────────────────────

    def _set_pay(self, m: str):
        self.payment_var.set(m)
        self._update_pay()

    def _update_pay(self):
        m = self.payment_var.get()
        self._cash_btn.configure(
            fg_color="#1a56db" if m == "현금" else ("gray85", "#2d2d3d"),
            text_color="white" if m == "현금" else ("gray10", "white"),
        )
        self._card_btn.configure(
            fg_color="#1a56db" if m == "카드" else ("gray85", "#2d2d3d"),
            text_color="white" if m == "카드" else ("gray10", "white"),
        )

    def _recalc(self):
        total = sum(line.get()[1] for line in self._tax_lines)
        self.total_var.set(f"{total:,.0f} ft")

    def _remove(self):
        self.on_remove(self)
        self.destroy()

    def get_data(self) -> dict:
        amounts = {"none": 0.0, "5": 0.0, "18": 0.0, "27": 0.0}
        for line in self._tax_lines:
            key, amount = line.get()
            amounts[key] = amounts.get(key, 0.0) + amount
        return {
            "vendor":         self._vendor_ac.get(),
            "amount_ft":      sum(amounts.values()),
            "amount_none":    amounts["none"],
            "amount_5":       amounts["5"],
            "amount_18":      amounts["18"],
            "amount_27":      amounts["27"],
            "payment_method": self.payment_var.get(),
            "note":           self.note_var.get(),
        }


# ─────────────────────────────────────────────
# 매입 항목 수정 다이얼로그
# ─────────────────────────────────────────────

class EditExpenseDialog(ctk.CTkToplevel):
    def __init__(self, master, entry: dict, vendors: list[str], hints: dict[str, str], on_confirm):
        super().__init__(master)
        self.title("매입 항목 수정")
        self.geometry("500x520")
        self.resizable(False, True)
        self.grab_set()
        self._entry = entry
        self._on_confirm = on_confirm
        self._edit_tax_lines: list[TaxLine] = []
        self._build(vendors, hints)

    def _build(self, vendors: list[str], hints: dict[str, str]):
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(side="bottom", pady=(8, 18))
        ctk.CTkButton(bf, text="확인", width=110, height=36,
                      font=ctk.CTkFont(size=14), command=self._confirm).pack(side="left", padx=10)
        ctk.CTkButton(bf, text="취소", width=90, height=36, fg_color="gray60",
                      font=ctk.CTkFont(size=14), command=self.destroy).pack(side="left", padx=10)

        ctk.CTkLabel(self, text="매입 항목 수정",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(16, 8))

        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28)

        LW = 72

        def frow(label, top_align=False):
            r = ctk.CTkFrame(form, fg_color="transparent")
            r.pack(fill="x", pady=4)
            ctk.CTkLabel(r, text=label, width=LW, anchor="e",
                         font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 10),
                                                          anchor="n" if top_align else "center")
            return r

        ctk.CTkLabel(form, text="").pack()  # spacer

        r_date = frow("날짜")
        ctk.CTkLabel(r_date, text=self._entry.get("date", ""),
                     anchor="w", font=ctk.CTkFont(size=13)).pack(side="left")

        r_cat = frow("카테고리")
        self._cat_var = ctk.StringVar(value=self._entry.get("category", "식재료 및 판관비"))
        ctk.CTkComboBox(r_cat, values=EXPENSE_CATEGORIES,
                        variable=self._cat_var, width=280,
                        font=ctk.CTkFont(size=13)).pack(side="left")

        r_vendor = frow("구매처")
        self._vendor_ac = AutocompleteEntry(r_vendor, vendors, hints=hints, width=260)
        self._vendor_ac.set(self._entry.get("vendor", ""))
        self._vendor_ac.pack(side="left")

        r_pay = frow("결제방법")
        pf = ctk.CTkFrame(r_pay, fg_color="transparent")
        pf.pack(side="left")
        self._pay_var = ctk.StringVar(value=self._entry.get("payment_method", "카드"))
        self._cash_btn = ctk.CTkButton(pf, text="현금", width=58, height=30,
                                       font=ctk.CTkFont(size=13),
                                       command=lambda: self._set_pay("현금"))
        self._cash_btn.pack(side="left", padx=(0, 4))
        self._card_btn = ctk.CTkButton(pf, text="카드", width=58, height=30,
                                       font=ctk.CTkFont(size=13),
                                       command=lambda: self._set_pay("카드"))
        self._card_btn.pack(side="left")
        self._update_pay()

        # 세율 섹션
        r_tax = frow("세금", top_align=True)
        tax_outer = ctk.CTkFrame(r_tax, fg_color="transparent")
        tax_outer.pack(side="left")

        lbl_r = ctk.CTkFrame(tax_outer, fg_color="transparent")
        lbl_r.pack(fill="x")
        ctk.CTkLabel(lbl_r, text="세율", font=ctk.CTkFont(size=11),
                     text_color="gray50", width=88, anchor="w").pack(side="left")
        ctk.CTkLabel(lbl_r, text="금액(ft)", font=ctk.CTkFont(size=11),
                     text_color="gray50", width=116, anchor="w").pack(side="left")

        self._edit_tax_container = ctk.CTkFrame(tax_outer, fg_color="transparent")
        self._edit_tax_container.pack(fill="x")

        add_r = ctk.CTkFrame(tax_outer, fg_color="transparent")
        add_r.pack(fill="x", pady=(4, 0))
        ctk.CTkButton(add_r, text="+ 추가", width=68, height=26,
                      font=ctk.CTkFont(size=12),
                      command=self._add_edit_tax_line).pack(side="left")

        # 기존 데이터 로드
        for rate_key in ["none", "5", "18", "27"]:
            amt = float(self._entry.get(f"amount_{rate_key}", 0) or 0)
            if amt > 0:
                self._add_edit_tax_line(rate_key, amt)
        if not self._edit_tax_lines:
            self._add_edit_tax_line()

        r_note = frow("비고")
        self._note_var = ctk.StringVar(value=self._entry.get("note", ""))
        ctk.CTkEntry(r_note, textvariable=self._note_var, width=280,
                     font=ctk.CTkFont(size=13)).pack(side="left")

    def _add_edit_tax_line(self, rate_key: str = "none", amount: float = 0.0):
        line = TaxLine(self._edit_tax_container, on_change=lambda: None)
        line.pack(fill="x", pady=1)
        if amount:
            line.set_rate_amount(rate_key, amount)
        self._edit_tax_lines.append(line)
        line.set_remove_command(lambda l=line: self._remove_edit_tax_line(l))
        self._update_edit_remove_btns()

    def _remove_edit_tax_line(self, line: TaxLine):
        if len(self._edit_tax_lines) <= 1:
            return
        if line in self._edit_tax_lines:
            self._edit_tax_lines.remove(line)
        line.destroy()
        self._update_edit_remove_btns()

    def _update_edit_remove_btns(self):
        show = len(self._edit_tax_lines) > 1
        for line in self._edit_tax_lines:
            line.show_remove(show)

    def _set_pay(self, m: str):
        self._pay_var.set(m)
        self._update_pay()

    def _update_pay(self):
        m = self._pay_var.get()
        self._cash_btn.configure(
            fg_color="#1a56db" if m == "현금" else ("gray85", "#2d2d3d"),
            text_color="white" if m == "현금" else ("gray10", "white"),
        )
        self._card_btn.configure(
            fg_color="#1a56db" if m == "카드" else ("gray85", "#2d2d3d"),
            text_color="white" if m == "카드" else ("gray10", "white"),
        )

    def _confirm(self):
        amounts = {"none": 0.0, "5": 0.0, "18": 0.0, "27": 0.0}
        for line in self._edit_tax_lines:
            key, amount = line.get()
            amounts[key] = amounts.get(key, 0.0) + amount
        updated = {
            "date":           self._entry["date"],
            "category":       self._cat_var.get(),
            "vendor":         self._vendor_ac.get(),
            "amount_ft":      sum(amounts.values()),
            "amount_none":    amounts["none"],
            "amount_5":       amounts["5"],
            "amount_18":      amounts["18"],
            "amount_27":      amounts["27"],
            "payment_method": self._pay_var.get(),
            "note":           self._note_var.get(),
        }
        self._on_confirm(updated)
        self.destroy()


# ─────────────────────────────────────────────
# 메인 페이지
# ─────────────────────────────────────────────

class ExpensePage(ctk.CTkFrame):
    def __init__(self, master, role: str):
        super().__init__(master, fg_color="transparent")
        self.role = role
        self.lang = "en" if role != "admin" else "ko"
        self.t = lambda s: _t(s, self.lang)
        self._expense_rows_1: list[ExpenseRow] = []
        self._expense_rows_2: list[ExpenseRow] = []
        self._pay_filter = "전체"
        self._cat_filter = "전체"
        self._note_only_var = ctk.BooleanVar(value=False)
        self._filter_btns: dict[str, ctk.CTkButton] = {}
        self._cat_filter_btns: dict[str, ctk.CTkButton] = {}
        # display→internal mapping for categories (for SegmentedButton)
        if self.lang == "en":
            self._seg_display = [_t("식재료 및 판관비", "en"), _t("시설 및 운영 관리비", "en")]
            self._seg_to_internal = {_t("식재료 및 판관비", "en"): "식재료 및 판관비",
                                     _t("시설 및 운영 관리비", "en"): "시설 및 운영 관리비"}
        else:
            self._seg_display = ["식재료 및 판관비", "시설 및 운영 관리비"]
            self._seg_to_internal = {v: v for v in self._seg_display}
        self._build_ui()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(hdr, text=self.t("사용 금액 (매입)"),
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        self._date_row = DateRow(scroll, on_change=lambda ds: self._refresh_table(), lang=self.lang)
        self._date_row.pack(fill="x", pady=(8, 16))

        self._cat_switcher = ctk.CTkSegmentedButton(
            scroll,
            values=self._seg_display,
            command=self._on_cat_switch,
            font=ctk.CTkFont(size=14),
        )
        self._cat_switcher.set(self._seg_display[0])
        self._cat_switcher.pack(fill="x", pady=(0, 6))

        self._cat_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self._cat_container.pack(fill="x")

        self._cat_frame_1 = ctk.CTkFrame(self._cat_container, corner_radius=10,
                                          fg_color=("gray95", "gray17"))
        self._cat_frame_2 = ctk.CTkFrame(self._cat_container, corner_radius=10,
                                          fg_color=("gray95", "gray17"))

        self._input_container_1 = self._build_category_content(self._cat_frame_1, self._expense_rows_1, "식재료 및 판관비")
        self._input_container_2 = self._build_category_content(self._cat_frame_2, self._expense_rows_2, "시설 및 운영 관리비")
        self._cat_frame_1.pack(fill="x")

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(btn_frame, text=self.t("저장"), width=120, height=44,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      command=self._save).pack(side="left")
        self.msg_label = ctk.CTkLabel(btn_frame, text="", font=ctk.CTkFont(size=13))
        self.msg_label.pack(side="left", padx=16)

        table_card = ctk.CTkFrame(scroll, corner_radius=12)
        table_card.pack(fill="x", pady=(8, 0))

        th = ctk.CTkFrame(table_card, fg_color="transparent")
        th.pack(fill="x", padx=20, pady=(14, 4))
        ctk.CTkLabel(th, text=self.t("이번 달 매입 내역"),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        filter_row = ctk.CTkFrame(table_card, fg_color="transparent")
        filter_row.pack(fill="x", padx=20, pady=(0, 2))
        ctk.CTkLabel(filter_row, text=self.t("결제:"), font=ctk.CTkFont(size=12),
                     text_color="gray50", width=36).pack(side="left", padx=(0, 4))
        pay_filter_labels = [("전체", self.t("전체")), ("현금", self.t("현금")), ("카드", self.t("카드"))]
        for internal_val, display_lbl in pay_filter_labels:
            btn = ctk.CTkButton(filter_row, text=display_lbl, width=52, height=26,
                                font=ctk.CTkFont(size=12),
                                command=lambda v=internal_val: self._set_pay_filter(v))
            btn.pack(side="left", padx=2)
            self._filter_btns[internal_val] = btn
        ctk.CTkCheckBox(filter_row, text=self.t("비고 있는 항목만"),
                        variable=self._note_only_var,
                        font=ctk.CTkFont(size=12),
                        command=self._refresh_table).pack(side="left", padx=(14, 0))
        self._update_filter_btns()

        cat_filter_row = ctk.CTkFrame(table_card, fg_color="transparent")
        cat_filter_row.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(cat_filter_row, text=self.t("분류:"), font=ctk.CTkFont(size=12),
                     text_color="gray50", width=36).pack(side="left", padx=(0, 4))
        cat_filter_defs = [("전체", self.t("전체"), 52),
                           ("식재료/판관비", self.t("식재료/판관비"), 88),
                           ("시설/운영관리", self.t("시설/운영관리"), 88)]
        for internal_val, display_lbl, btn_w in cat_filter_defs:
            btn = ctk.CTkButton(cat_filter_row, text=display_lbl, width=btn_w, height=26,
                                font=ctk.CTkFont(size=12),
                                command=lambda v=internal_val: self._set_cat_filter(v))
            btn.pack(side="left", padx=2)
            self._cat_filter_btns[internal_val] = btn
        self._update_cat_filter_btns()

        self.table_inner = ctk.CTkScrollableFrame(table_card, height=240, fg_color="transparent")
        self.table_inner.pack(fill="x", padx=10, pady=(0, 4))

        self._summary_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        self._summary_frame.pack(fill="x", padx=10, pady=(0, 10))

        self._refresh_table()

    def _on_cat_switch(self, value: str):
        internal = self._seg_to_internal.get(value, value)
        if internal == "식재료 및 판관비":
            self._cat_frame_2.pack_forget()
            self._cat_frame_1.pack(fill="x")
        else:
            self._cat_frame_1.pack_forget()
            self._cat_frame_2.pack(fill="x")

    def _build_category_content(self, parent, rows_list: list, category: str):
        LF = ctk.CTkFont(size=12, weight="bold")
        LC = ("gray25", "gray65")
        # 라벨 + "행 추가" 버튼을 같은 줄에
        hdr_row = ctk.CTkFrame(parent, fg_color="transparent")
        hdr_row.pack(fill="x", padx=(24, 16), pady=(8, 2))
        container = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkButton(hdr_row, text="+ 행 추가", width=80, height=26,
                      font=ctk.CTkFont(size=12),
                      command=lambda: self._add_expense_row(rows_list, container, category)).pack(side="right")
        rate_hdr = "Rate" if self.lang == "en" else "세율"
        for text, w in [(self.t("구매처"), 158), (self.t("결제방법"), 102),
                        (rate_hdr, 88), (self.t("금액(ft)"), 118), (self.t("비고"), 136)]:
            ctk.CTkLabel(hdr_row, text=text, font=LF, text_color=LC,
                         width=w, anchor="w").pack(side="left")
        container.pack(fill="x", padx=16, pady=(0, 2))
        self._add_expense_row(rows_list, container, category)
        return container

    # ── Vendors ────────────────────────────────────────────────────────

    def _get_vendors(self, category: str = "전체") -> tuple[list[str], dict[str, str]]:
        full = cm.get_vendors_full()
        filtered = [v for v in full if v.get("category", "전체") in ("전체", category)]
        hints = {v["name"]: v["note"] for v in filtered if v.get("note")}
        names = [v["name"] for v in filtered if v.get("name")]
        seen = set(names)
        today = date.today()
        for offset in range(3):
            total_m = today.month - 1 - offset
            y = today.year + total_m // 12
            m = total_m % 12 + 1
            for rec in em.load_expenses(y, m):
                if rec.get("category", "식재료 및 판관비") != category:
                    continue
                v = rec.get("vendor", "").strip()
                if v and v not in seen:
                    names.append(v)
                    seen.add(v)
        return names, hints

    def _add_expense_row(self, rows_list: list, container, category: str = "전체"):
        names, hints = self._get_vendors(category)
        row = ExpenseRow(container, names, hints, lambda r: self._remove_expense_row(r, rows_list))
        row.pack(fill="x", pady=2)
        rows_list.append(row)

    def _remove_expense_row(self, row: ExpenseRow, rows_list: list):
        if row in rows_list:
            rows_list.remove(row)

    # ── Save ───────────────────────────────────────────────────────────

    def _save(self):
        date_str = self._date_row.get_date_str()
        if not date_str:
            self._show_msg("날짜 형식이 올바르지 않습니다", "red")
            return
        try:
            y, m, d = (int(x) for x in date_str.split("-"))
            d_obj = date(y, m, d)
        except Exception:
            self._show_msg("날짜 오류", "red")
            return
        if d_obj > date.today():
            self._show_msg("미래 날짜는 입력할 수 없습니다", "red")
            return
        if d_obj < date(MIN_YEAR, 1, 1):
            self._show_msg(f"{MIN_YEAR}년 이전 날짜는 입력할 수 없습니다", "red")
            return

        entries = []
        for cat, rows_list in [("식재료 및 판관비", self._expense_rows_1),
                                ("시설 및 운영 관리비", self._expense_rows_2)]:
            for row in rows_list:
                data = row.get_data()
                if not data["vendor"]:
                    continue
                data["date"] = date_str
                data["category"] = cat
                entries.append(data)

        if not entries:
            self._show_msg("구매처를 입력하세요", "orange")
            return

        vendors_cat = {v["name"]: v.get("category", "전체") for v in cm.get_vendors_full()}
        for entry in entries:
            v_name = entry["vendor"]
            e_cat = entry["category"]
            reg_cat = vendors_cat.get(v_name, "전체")
            if reg_cat != "전체" and reg_cat != e_cat:
                self._show_msg(f"'{v_name}'은(는) [{reg_cat}] 업체입니다", "red")
                return

        existing_full = cm.get_vendors_full()
        existing_names = {v["name"] for v in existing_full}
        added = False
        for cat_name, rows_list in [("식재료 및 판관비", self._expense_rows_1),
                                     ("시설 및 운영 관리비", self._expense_rows_2)]:
            for row in rows_list:
                v = row.get_data()["vendor"]
                if v and v not in existing_names:
                    existing_full.append({"name": v, "note": "", "category": cat_name})
                    existing_names.add(v)
                    added = True
        if added:
            cm.set_vendors_full(existing_full)

        em.save_expense(y, m, entries)
        self._reset_input_rows()
        self._show_msg(self.t("저장되었습니다"), "green")
        self._refresh_table()

    # ── Filters ────────────────────────────────────────────────────────

    def _set_pay_filter(self, val: str):
        self._pay_filter = val
        self._update_filter_btns()
        self._refresh_table()

    def _update_filter_btns(self):
        for label, btn in self._filter_btns.items():
            active = (label == self._pay_filter)
            btn.configure(
                fg_color="#1a56db" if active else ("gray85", "#2d2d3d"),
                text_color="white" if active else ("gray10", "white"),
            )

    def _set_cat_filter(self, val: str):
        self._cat_filter = val
        self._update_cat_filter_btns()
        self._refresh_table()

    def _update_cat_filter_btns(self):
        for label, btn in self._cat_filter_btns.items():
            active = (label == self._cat_filter)
            cat_color = CAT_COLOR.get(CAT_FILTER_MAP.get(label, ""), "#1a56db")
            btn.configure(
                fg_color=(cat_color if active else ("gray85", "#2d2d3d")),
                text_color="white" if active else ("gray10", "white"),
            )

    # ── Edit / Delete entry ────────────────────────────────────────────

    def _delete_entry(self, entry: dict):
        ym = self._date_row.get_year_month()
        if not ym:
            return

        import tkinter.messagebox as mb
        vendor = entry.get("vendor", "")
        amount = entry.get("amount_ft", 0)
        msg = f"{entry.get('date', '')}  {vendor}  {amount:,.0f} ft\n\n삭제할까요?"
        if not mb.askyesno("삭제 확인", msg):
            return

        y, m = ym
        all_records = em.load_expenses(y, m)
        all_records = [r for r in all_records if not (
            r.get("date") == entry.get("date") and
            r.get("vendor") == entry.get("vendor") and
            abs(r.get("amount_ft", 0) - entry.get("amount_ft", 0)) < 0.01
        )]
        em.replace_expenses(y, m, all_records)
        self._refresh_table()
        self._show_msg(self.t("삭제 완료"), "orange")

    def _open_edit(self, entry: dict):
        ym = self._date_row.get_year_month()
        if not ym:
            return

        def on_confirm(updated: dict):
            y, m = ym
            all_records = em.load_expenses(y, m)
            for i, r in enumerate(all_records):
                if (r.get("date") == entry.get("date") and
                        r.get("vendor") == entry.get("vendor") and
                        abs(r.get("amount_ft", 0) - entry.get("amount_ft", 0)) < 0.01):
                    all_records[i] = updated
                    break
            em.replace_expenses(y, m, all_records)
            self._refresh_table()
            self._show_msg(self.t("수정되었습니다"), "green")

        names, hints = self._get_vendors()
        EditExpenseDialog(self, entry, names, hints, on_confirm)

    # ── Table ──────────────────────────────────────────────────────────

    def _refresh_table(self):
        for w in self.table_inner.winfo_children():
            w.destroy()
        for w in self._summary_frame.winfo_children():
            w.destroy()

        ym = self._date_row.get_year_month()
        if not ym:
            return
        y, m = ym
        all_records = em.load_expenses(y, m)

        all_cash = sum(r["amount_ft"] for r in all_records if r.get("payment_method", "현금") != "카드")
        all_card = sum(r["amount_ft"] for r in all_records if r.get("payment_method") == "카드")
        all_none = sum(r.get("amount_none", 0) for r in all_records)
        all_5    = sum(r.get("amount_5",    0) for r in all_records)
        all_18   = sum(r.get("amount_18",   0) for r in all_records)
        all_27   = sum(r.get("amount_27",   0) for r in all_records)

        records = list(all_records)
        if self._pay_filter != "전체":
            records = [r for r in records if r.get("payment_method", "현금") == self._pay_filter]
        cat_value = CAT_FILTER_MAP.get(self._cat_filter)
        if cat_value:
            records = [r for r in records if r.get("category", "식재료 및 판관비") == cat_value]
        if self._note_only_var.get():
            records = [r for r in records if r.get("note", "").strip()]

        headers = [self.t("날짜"), self.t("분류"), self.t("구매처"), self.t("결제"),
                   self.t("합계(ft)"), self.t("면세(ft)"), "5%(ft)", "18%(ft)", "27%(ft)",
                   self.t("비고"), ""]
        widths  = [82, 62, 108, 46, 82, 70, 58, 62, 62, 80, 44]

        hrow = ctk.CTkFrame(self.table_inner, fg_color="#1a56db", corner_radius=6)
        hrow.pack(fill="x", pady=(0, 2))
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hrow, text=h, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="white", width=w).pack(side="left", padx=2, pady=6)

        if not records:
            msg = self.t("기록이 없습니다") if not all_records else self.t("필터 조건에 맞는 항목이 없습니다")
            ctk.CTkLabel(self.table_inner, text=msg, text_color="gray",
                         font=ctk.CTkFont(size=13)).pack(pady=20)
            self._render_summary(all_cash, all_card, 0, 0, all_none, all_5, all_18, all_27,
                                 0, 0, 0, 0)
            return

        f_cash = f_card = 0.0
        f_none = f_5 = f_18 = f_27 = 0.0

        for i, rec in enumerate(records):
            bg = ("#e8f0fe", "#f8faff") if i % 2 == 0 else ("white", "#1e1e2e")
            drow = ctk.CTkFrame(self.table_inner, fg_color=bg, corner_radius=4)
            drow.pack(fill="x", pady=1)
            pm = rec.get("payment_method", "현금")
            pm_color = "#1a56db" if pm == "카드" else "#276749"
            cat = rec.get("category", "식재료 및 판관비")
            cat_short = CAT_SHORT.get(cat, cat)
            cat_color = CAT_COLOR.get(cat, "gray")

            def _fmt(v): return f"{v:,.0f}" if v else ""

            vals = [
                (rec["date"],                              None,      widths[0]),
                (cat_short,                                cat_color, widths[1]),
                (rec["vendor"],                            None,      widths[2]),
                (pm,                                       pm_color,  widths[3]),
                (f"{rec['amount_ft']:,.0f}",               None,      widths[4]),
                (_fmt(rec.get("amount_none")),             None,      widths[5]),
                (_fmt(rec.get("amount_5")),                None,      widths[6]),
                (_fmt(rec.get("amount_18")),               None,      widths[7]),
                (_fmt(rec.get("amount_27")),               None,      widths[8]),
                (rec.get("note", ""),                      None,      widths[9]),
            ]
            for text, color, w in vals:
                kw = {"font": ctk.CTkFont(size=12, weight="bold"), "text_color": color} if color \
                     else {"font": ctk.CTkFont(size=12)}
                ctk.CTkLabel(drow, text=str(text), width=w, **kw).pack(side="left", padx=2, pady=4)

            ctk.CTkButton(drow, text="수정", width=44, height=24,
                          font=ctk.CTkFont(size=11),
                          command=lambda e=rec: self._open_edit(e)).pack(side="left", padx=2)
            ctk.CTkButton(drow, text="삭제", width=44, height=24,
                          fg_color="#e53e3e", hover_color="#c53030",
                          font=ctk.CTkFont(size=11),
                          command=lambda e=rec: self._delete_entry(e)).pack(side="left", padx=(0, 2))

            if pm == "카드":
                f_card += rec["amount_ft"]
            else:
                f_cash += rec["amount_ft"]
            f_none += rec.get("amount_none", 0)
            f_5    += rec.get("amount_5",    0)
            f_18   += rec.get("amount_18",   0)
            f_27   += rec.get("amount_27",   0)

        # 세율별 합계 행
        tot_row = ctk.CTkFrame(self.table_inner, fg_color=("#f0f4f8", "#1e2535"), corner_radius=4)
        tot_row.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(tot_row, text=self.t("세율별 합계"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray50",
                     width=widths[0] + widths[1] + widths[2] + widths[3] + widths[4] + 10
                     ).pack(side="left", padx=4, pady=4)
        for label, val, w in [("면세", f_none, widths[5]),
                               ("5%",  f_5,    widths[6]),
                               ("18%", f_18,   widths[7]),
                               ("27%", f_27,   widths[8])]:
            ctk.CTkLabel(tot_row,
                         text=f"{val:,.0f}" if val else "—",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#1a56db" if val else "gray60",
                         width=w).pack(side="left", padx=2, pady=4)

        self._render_summary(all_cash, all_card, f_cash, f_card,
                             all_none, all_5, all_18, all_27,
                             f_none, f_5, f_18, f_27)

    def _render_summary(self, all_cash: float, all_card: float,
                        f_cash: float, f_card: float,
                        all_none: float, all_5: float, all_18: float, all_27: float,
                        f_none: float, f_5: float, f_18: float, f_27: float):
        is_filtered = self._pay_filter != "전체" or self._cat_filter != "전체" or self._note_only_var.get()

        def _pair(parent, label, amount, color, sep=""):
            if sep:
                ctk.CTkLabel(parent, text=sep, font=ctk.CTkFont(size=11),
                             text_color="gray50").pack(side="left", padx=2)
            ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11),
                         text_color=color).pack(side="left", padx=(4, 1))
            ctk.CTkLabel(parent, text=f"{amount:,.0f} ft",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=color).pack(side="left", padx=(0, 6))

        # 결제방법별 합계 행
        s1 = ctk.CTkFrame(self._summary_frame, fg_color="#dbeafe", corner_radius=6)
        s1.pack(fill="x", pady=(2, 1))
        ctk.CTkLabel(s1, text=self.t("결제합계") if not is_filtered else self.t("선택/전체"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     width=70).pack(side="left", padx=(6, 0), pady=5)
        if is_filtered:
            _pair(s1, self.t("현금"), f_cash, "#276749")
            _pair(s1, self.t("카드"), f_card, "#1a56db", "/")
            _pair(s1, self.t("소계"), f_cash + f_card, "gray30", "|")
            ctk.CTkLabel(s1, text="▏전체:", font=ctk.CTkFont(size=11),
                         text_color="gray50").pack(side="left", padx=(8, 2))
            _pair(s1, self.t("현금"), all_cash, "#276749")
            _pair(s1, self.t("카드"), all_card, "#1a56db", "/")
            _pair(s1, self.t("합계"), all_cash + all_card, "gray30", "/")
        else:
            _pair(s1, self.t("현금"), all_cash, "#276749")
            _pair(s1, self.t("카드"), all_card, "#1a56db", "|")
            _pair(s1, self.t("총합"), all_cash + all_card, "gray30", "|")

        # 세율별 합계 행
        n, f5, f18, f27 = (f_none, f_5, f_18, f_27) if is_filtered else (all_none, all_5, all_18, all_27)
        s2 = ctk.CTkFrame(self._summary_frame, fg_color=("#e8f5e9", "#1b2e1b"), corner_radius=6)
        s2.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(s2, text=self.t("세율합계"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     width=70).pack(side="left", padx=(6, 0), pady=5)
        for label, val in [(self.t("면세"), n), ("5%", f5), ("18%", f18), ("27%", f27)]:
            if val:
                _pair(s2, label, val, "#276749", "|" if label != "면세" else "")

    def _show_msg(self, text: str, color: str):
        self.msg_label.configure(text=text, text_color=color)
        self.after(3000, lambda: self.msg_label.configure(text=""))

    def _reset_input_rows(self):
        for row in list(self._expense_rows_1):
            row.destroy()
        self._expense_rows_1.clear()
        self._add_expense_row(self._expense_rows_1, self._input_container_1, "식재료 및 판관비")

        for row in list(self._expense_rows_2):
            row.destroy()
        self._expense_rows_2.clear()
        self._add_expense_row(self._expense_rows_2, self._input_container_2, "시설 및 운영 관리비")

    def refresh(self):
        self._reset_input_rows()
        self._refresh_table()
