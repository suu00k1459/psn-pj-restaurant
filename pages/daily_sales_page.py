import customtkinter as ctk
from datetime import date
from utils import config_manager as cm
from utils import excel_manager as em
from utils.date_widgets import DateRow, MIN_YEAR
from utils.i18n import t as _t

CURRENCIES = ["ft", "KRW", "USD", "EUR"]


class TransferRow(ctk.CTkFrame):
    def __init__(self, master, employee_data: list[dict], on_remove):
        super().__init__(master, fg_color="transparent")
        self.on_remove = on_remove
        self._emp_banks = {e["name"]: e.get("banks", []) for e in employee_data}
        employees = list(self._emp_banks.keys()) or ["직원 없음"]

        self.name_var = ctk.StringVar(value=employees[0] if employees else "")
        self.bank_var = ctk.StringVar()
        self.amount_var = ctk.StringVar(value="0")
        self.currency_var = ctk.StringVar(value="ft")
        self.ft_var = ctk.StringVar(value="0 ft")

        self._name_cb = ctk.CTkComboBox(self, values=employees, variable=self.name_var,
                                        width=110, font=ctk.CTkFont(size=13),
                                        command=self._on_name_change)
        self._name_cb.pack(side="left", padx=(0, 4))

        self._bank_cb = ctk.CTkComboBox(self, values=[], variable=self.bank_var, width=100,
                                        font=ctk.CTkFont(size=13),
                                        command=self._on_bank_change)
        self._bank_cb.pack(side="left", padx=(0, 4))

        amt = ctk.CTkEntry(self, textvariable=self.amount_var, width=100, font=ctk.CTkFont(size=13))
        amt.pack(side="left", padx=(0, 4))
        amt.bind("<KeyRelease>", lambda e: self._recalc())

        self._currency_cb = ctk.CTkComboBox(self, values=CURRENCIES, variable=self.currency_var,
                                            width=70, font=ctk.CTkFont(size=13),
                                            command=lambda v: self._recalc())
        self._currency_cb.pack(side="left", padx=(0, 4))

        ctk.CTkLabel(self, textvariable=self.ft_var, width=90, font=ctk.CTkFont(size=13),
                     text_color="#1a56db").pack(side="left", padx=(0, 4))

        ctk.CTkButton(self, text="삭제", width=50, height=28, fg_color="#e53e3e",
                      hover_color="#c53030", font=ctk.CTkFont(size=12),
                      command=self._remove).pack(side="left")

        self._on_name_change(employees[0] if employees else "")

    def update_employees(self, employee_data: list[dict]):
        self._emp_banks = {e["name"]: e.get("banks", []) for e in employee_data}
        names = list(self._emp_banks.keys()) or ["직원 없음"]
        self._name_cb.configure(values=names)

    def _on_name_change(self, name: str):
        banks = self._emp_banks.get(name, [])
        bank_names = [b["name"] if isinstance(b, dict) else b for b in banks]
        self._bank_cb.configure(values=bank_names if bank_names else [""])
        if bank_names:
            self.bank_var.set(bank_names[0])
            self._bank_cb.set(bank_names[0])
            first = banks[0]
            currency = first.get("currency", "ft") if isinstance(first, dict) else "ft"
            self.currency_var.set(currency)
            self._currency_cb.set(currency)
        else:
            self.bank_var.set("")
            self._bank_cb.set("")
        self._recalc()

    def _on_bank_change(self, bank_name: str):
        name = self.name_var.get()
        for b in self._emp_banks.get(name, []):
            bname = b["name"] if isinstance(b, dict) else b
            if bname == bank_name:
                currency = b.get("currency", "ft") if isinstance(b, dict) else "ft"
                self.currency_var.set(currency)
                self._currency_cb.set(currency)
                self._recalc()
                break

    def _recalc(self):
        try:
            amt = float(self.amount_var.get())
        except ValueError:
            amt = 0.0
        ft = cm.convert_to_ft(amt, self.currency_var.get())
        self.ft_var.set(f"{ft:,.0f} ft")

    def _remove(self):
        self.on_remove(self)
        self.destroy()

    def get_data(self) -> dict:
        try:
            amt = float(self.amount_var.get())
        except ValueError:
            amt = 0.0
        ft = cm.convert_to_ft(amt, self.currency_var.get())
        return {"name": self.name_var.get(), "bank": self.bank_var.get(), "amount": ft}


class SalesField(ctk.CTkFrame):
    def __init__(self, master, label: str, row: int, show_count: bool = False, lang: str = "ko"):
        super().__init__(master, fg_color="transparent")
        self.amount_var = ctk.StringVar(value="0")
        self.currency_var = ctk.StringVar(value="ft")
        self.ft_var = ctk.StringVar(value="0 ft")
        self._show_count = show_count
        if show_count:
            self.count_var = ctk.StringVar(value="0")

        ctk.CTkLabel(self, text=label, width=130, anchor="e",
                     font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(0, 8))
        entry = ctk.CTkEntry(self, textvariable=self.amount_var, width=130,
                             font=ctk.CTkFont(size=14))
        entry.grid(row=0, column=1, padx=(0, 6))
        entry.bind("<KeyRelease>", lambda e: self._recalc())
        ctk.CTkComboBox(self, values=CURRENCIES, variable=self.currency_var, width=80,
                        font=ctk.CTkFont(size=13),
                        command=lambda v: self._recalc()).grid(row=0, column=2, padx=(0, 8))
        ctk.CTkLabel(self, textvariable=self.ft_var, width=100, anchor="w",
                     font=ctk.CTkFont(size=13), text_color="#1a56db").grid(row=0, column=3)
        if show_count:
            count_lbl = "Count" if lang == "en" else "건수"
            ctk.CTkLabel(self, text=count_lbl, width=36, anchor="e",
                         font=ctk.CTkFont(size=13), text_color="gray50").grid(row=0, column=4, padx=(16, 4))
            ctk.CTkEntry(self, textvariable=self.count_var, width=60,
                         font=ctk.CTkFont(size=13)).grid(row=0, column=5)

    def _recalc(self):
        try:
            amt = float(self.amount_var.get())
        except ValueError:
            amt = 0.0
        ft = cm.convert_to_ft(amt, self.currency_var.get())
        self.ft_var.set(f"{ft:,.0f} ft")

    def get_ft(self) -> float:
        try:
            amt = float(self.amount_var.get())
        except ValueError:
            return 0.0
        return cm.convert_to_ft(amt, self.currency_var.get())

    def get_count(self) -> int:
        if not self._show_count:
            return 0
        try:
            return int(self.count_var.get())
        except ValueError:
            return 0

    def set_value(self, ft_val: float, count: int = 0):
        self.currency_var.set("ft")
        self.amount_var.set(str(ft_val))
        self.ft_var.set(f"{ft_val:,.0f} ft")
        if self._show_count:
            self.count_var.set(str(count))


class DailySalesPage(ctk.CTkFrame):
    def __init__(self, master, role: str):
        super().__init__(master, fg_color="transparent")
        self.role = role
        self.lang = "en" if role != "admin" else "ko"
        self.t = lambda s: _t(s, self.lang)
        self._transfer_rows: list[TransferRow] = []
        self._build_ui()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(hdr, text=self.t("일일 매출 기록"), font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # Date row + 불러오기 button
        date_wrapper = ctk.CTkFrame(scroll, fg_color="transparent")
        date_wrapper.pack(fill="x", pady=(8, 12))
        self._date_row = DateRow(date_wrapper, on_change=lambda ds: self._load_date(silent=True), lang=self.lang)
        self._date_row.pack(side="left")
        ctk.CTkButton(date_wrapper, text=self.t("불러오기"), width=90, height=32,
                      font=ctk.CTkFont(size=13),
                      command=self._load_date).pack(side="left", padx=(12, 0))

        # Input card
        card = ctk.CTkFrame(scroll, corner_radius=12)
        card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(card, text=self.t("매출 입력"),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(14, 10))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=(0, 16))

        self.card_field = SalesField(inner, self.t("카드"), 0, show_count=True, lang=self.lang)
        self.card_field.pack(fill="x", pady=6)
        self.nav_field = SalesField(inner, "NAV Cash", 1, show_count=True, lang=self.lang)
        self.nav_field.pack(fill="x", pady=6)
        self.invoice_field = SalesField(inner, "Invoice", 2, lang=self.lang)
        self.invoice_field.pack(fill="x", pady=6)

        if self.role == "admin":
            self.cash_field = SalesField(inner, self.t("현금"), 3, lang=self.lang)
            self.cash_field.pack(fill="x", pady=6)

            transfer_card = ctk.CTkFrame(scroll, corner_radius=12)
            transfer_card.pack(fill="x", pady=(0, 16))
            tf_hdr = ctk.CTkFrame(transfer_card, fg_color="transparent")
            tf_hdr.pack(fill="x", padx=20, pady=(14, 6))
            ctk.CTkLabel(tf_hdr, text=self.t("계좌이체"),
                         font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
            ctk.CTkButton(tf_hdr, text=self.t("+ 행 추가"), width=80, height=30,
                          font=ctk.CTkFont(size=13),
                          command=self._add_transfer_row).pack(side="right")
            self.transfer_container = ctk.CTkFrame(transfer_card, fg_color="transparent")
            self.transfer_container.pack(fill="x", padx=20, pady=(0, 14))
        else:
            self.cash_field = None

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(btn_frame, text=self.t("저장"), width=120, height=44,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      command=self._save).pack(side="left")
        self.msg_label = ctk.CTkLabel(btn_frame, text="", font=ctk.CTkFont(size=13))
        self.msg_label.pack(side="left", padx=16)

        self.table_frame = ctk.CTkFrame(scroll, corner_radius=12)
        self.table_frame.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(self.table_frame, text=self.t("이번 달 일별 기록"),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(14, 8))
        self.table_inner = ctk.CTkScrollableFrame(self.table_frame, height=220, fg_color="transparent")
        self.table_inner.pack(fill="x", padx=10, pady=(0, 14))

        self._load_date(silent=True)
        self._refresh_table()

    # ── Validation ─────────────────────────────────────────────────────

    def _validate_date(self, date_str: str):
        try:
            y, m, d = (int(x) for x in date_str.split("-"))
            d_obj = date(y, m, d)
        except (ValueError, TypeError):
            return None, "날짜 형식이 올바르지 않습니다"
        if d_obj > date.today():
            return None, "미래 날짜는 입력할 수 없습니다"
        if d_obj < date(MIN_YEAR, 1, 1):
            return None, f"{MIN_YEAR}년 이전 날짜는 입력할 수 없습니다"
        return d_obj, None

    # ── Transfer rows ──────────────────────────────────────────────────

    def _add_transfer_row(self):
        employee_data = em.load_employees() or [{"name": "직원 없음", "banks": []}]
        row = TransferRow(self.transfer_container, employee_data, self._remove_transfer_row)
        row.pack(fill="x", pady=3)
        self._transfer_rows.append(row)

    def _remove_transfer_row(self, row: "TransferRow"):
        if row in self._transfer_rows:
            self._transfer_rows.remove(row)

    # ── Save ───────────────────────────────────────────────────────────

    def _save(self):
        date_str = self._date_row.get_date_str()
        if not date_str:
            self._show_msg("날짜 형식이 올바르지 않습니다", "red")
            return
        d_obj, err = self._validate_date(date_str)
        if err:
            self._show_msg(err, "red")
            return
        y, m = d_obj.year, d_obj.month
        existing = next((r for r in em.load_daily_sales(y, m) if r["date"] == date_str), {})

        if self.role == "admin":
            details = [row.get_data() for row in self._transfer_rows]
            data = {
                "card": self.card_field.get_ft(),
                "card_count": self.card_field.get_count(),
                "nav_cash": self.nav_field.get_ft(),
                "nav_count": self.nav_field.get_count(),
                "invoice": self.invoice_field.get_ft(),
                "cash": self.cash_field.get_ft(),
                "transfer_detail": details,
                "transfer_total": sum(d["amount"] for d in details),
            }
        else:
            data = {
                "card": self.card_field.get_ft(),
                "card_count": self.card_field.get_count(),
                "nav_cash": self.nav_field.get_ft(),
                "nav_count": self.nav_field.get_count(),
                "invoice": self.invoice_field.get_ft(),
                "cash": existing.get("cash", 0.0),
                "transfer_detail": existing.get("transfer_detail", []),
                "transfer_total": existing.get("transfer_total", 0.0),
            }

        em.save_daily_sales(y, m, date_str, data)

        # 계좌이체 → 선지급 잔액 자동 연결
        if self.role == "admin":
            try:
                em.update_transfer_prepay(
                    date_str,
                    existing.get("transfer_detail", []),
                    data["transfer_detail"],
                )
            except Exception as exc:
                self._show_msg(f"선지급 연동 오류: {exc}", "red")
                return

        self._show_msg(self.t("저장되었습니다"), "green")
        self._refresh_table()

    # ── Load date ──────────────────────────────────────────────────────

    def _load_date(self, silent: bool = False):
        date_str = self._date_row.get_date_str()
        if not date_str:
            if not silent:
                self._show_msg("날짜 형식이 올바르지 않습니다", "red")
            return
        d_obj, err = self._validate_date(date_str)
        if err:
            if not silent:
                self._show_msg(err, "red")
            return
        y, m = d_obj.year, d_obj.month
        records = em.load_daily_sales(y, m)
        rec = next((r for r in records if r["date"] == date_str), None)
        if rec:
            self.card_field.set_value(rec.get("card", 0), rec.get("card_count", 0))
            self.nav_field.set_value(rec.get("nav_cash", 0), rec.get("nav_count", 0))
            self.invoice_field.set_value(rec.get("invoice", 0))
            if self.cash_field:
                self.cash_field.set_value(rec.get("cash", 0))
            if self.role == "admin":
                for row in self._transfer_rows:
                    row.destroy()
                self._transfer_rows.clear()
                employee_data = em.load_employees() or [{"name": "직원 없음", "banks": []}]
                for detail in rec.get("transfer_detail", []):
                    row = TransferRow(self.transfer_container, employee_data, self._remove_transfer_row)
                    row.pack(fill="x", pady=3)
                    name = detail.get("name", "")
                    row.name_var.set(name)
                    row._on_name_change(name)
                    if detail.get("bank"):
                        row.bank_var.set(detail["bank"])
                        row._on_bank_change(detail["bank"])
                    row.amount_var.set(str(detail.get("amount", 0)))
                    row.currency_var.set("ft")
                    row._recalc()
                    self._transfer_rows.append(row)
            if not silent:
                self._show_msg(self.t("불러왔습니다"), "green")
        else:
            # 기록 없으면 입력 필드 초기화
            self.card_field.set_value(0, 0)
            self.nav_field.set_value(0, 0)
            self.invoice_field.set_value(0)
            if self.cash_field:
                self.cash_field.set_value(0)
            if self.role == "admin":
                for row in self._transfer_rows:
                    row.destroy()
                self._transfer_rows.clear()
            if not silent:
                self._show_msg(self.t("해당 날짜의 기록이 없습니다"), "orange")
        self._refresh_table()

    # ── Table ──────────────────────────────────────────────────────────

    def _refresh_table(self):
        for w in self.table_inner.winfo_children():
            w.destroy()
        ym = self._date_row.get_year_month()
        if not ym:
            return
        y, m = ym
        records = em.load_daily_sales(y, m)

        headers = [self.t("날짜"), self.t("카드건수"), self.t("NAV건수"),
                   self.t("카드(ft)"), "NAV Cash(ft)", "Invoice(ft)"]
        widths  = [90, 56, 56, 100, 100, 90]
        if self.role == "admin":
            headers += [self.t("현금(ft)"), self.t("계좌이체(ft)")]
            widths  += [90, 90]

        hrow = ctk.CTkFrame(self.table_inner, fg_color="#1a56db", corner_radius=6)
        hrow.pack(fill="x", pady=(0, 2))
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hrow, text=h, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="white", width=w).pack(side="left", padx=4, pady=6)

        if not records:
            ctk.CTkLabel(self.table_inner, text=self.t("기록이 없습니다"), text_color="gray",
                         font=ctk.CTkFont(size=13)).pack(pady=20)
            return

        for i, rec in enumerate(records):
            bg = ("#e8f0fe", "#f8faff") if i % 2 == 0 else ("white", "#1e1e2e")
            drow = ctk.CTkFrame(self.table_inner, fg_color=bg, corner_radius=4)
            drow.pack(fill="x", pady=1)
            cols_vals = [
                (rec["date"],                        widths[0]),
                (str(rec.get("card_count", 0)),      widths[1]),
                (str(rec.get("nav_count", 0)),       widths[2]),
                (f"{rec['card']:,.0f}",              widths[3]),
                (f"{rec['nav_cash']:,.0f}",          widths[4]),
                (f"{rec['invoice']:,.0f}",           widths[5]),
            ]
            if self.role == "admin":
                cols_vals += [
                    (f"{rec['cash']:,.0f}",              widths[6]),
                    (f"{rec['transfer_total']:,.0f}",    widths[7]),
                ]
            for val, w in cols_vals:
                ctk.CTkLabel(drow, text=val, font=ctk.CTkFont(size=12),
                             width=w).pack(side="left", padx=4, pady=5)

    def _show_msg(self, text: str, color: str):
        self.msg_label.configure(text=text, text_color=color)
        self.after(3000, lambda: self.msg_label.configure(text=""))

    def refresh(self):
        self._refresh_table()
        if self.role == "admin" and self._transfer_rows:
            employee_data = em.load_employees() or [{"name": "직원 없음", "banks": []}]
            for row in self._transfer_rows:
                row.update_employees(employee_data)
