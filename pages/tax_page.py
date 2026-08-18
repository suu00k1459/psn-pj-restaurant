import customtkinter as ctk
from datetime import date
from utils import config_manager as cm
from utils import excel_manager as em
from utils.date_widgets import DateRow, MIN_YEAR
from utils.i18n import t as _t

CURRENCIES = ["ft", "KRW", "USD", "EUR"]


class TaxRow(ctk.CTkFrame):
    def __init__(self, master, on_remove):
        super().__init__(master, fg_color="transparent")
        self.on_remove = on_remove

        self.name_var = ctk.StringVar(value="")
        self.amount_var = ctk.StringVar(value="0")
        self.currency_var = ctk.StringVar(value="ft")
        self.ft_var = ctk.StringVar(value="0 ft")

        ctk.CTkEntry(self, textvariable=self.name_var, width=160,
                     placeholder_text="세금 종류", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 6))

        amt_entry = ctk.CTkEntry(self, textvariable=self.amount_var, width=120,
                                 font=ctk.CTkFont(size=13))
        amt_entry.pack(side="left", padx=(0, 6))
        amt_entry.bind("<KeyRelease>", lambda e: self._recalc())

        cur_cb = ctk.CTkComboBox(self, values=CURRENCIES, variable=self.currency_var,
                                 width=75, font=ctk.CTkFont(size=13),
                                 command=lambda v: self._recalc())
        cur_cb.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(self, textvariable=self.ft_var, width=100, anchor="w",
                     font=ctk.CTkFont(size=13), text_color="#1a56db").pack(side="left", padx=(0, 6))

        ctk.CTkButton(self, text="삭제", width=50, height=28, fg_color="#e53e3e",
                      hover_color="#c53030", font=ctk.CTkFont(size=12),
                      command=self._remove).pack(side="left")

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
            original = float(self.amount_var.get())
        except ValueError:
            original = 0.0
        ft = cm.convert_to_ft(original, self.currency_var.get())
        return {"tax_name": self.name_var.get(), "amount_ft": ft}


class TaxPage(ctk.CTkFrame):
    def __init__(self, master, role: str):
        super().__init__(master, fg_color="transparent")
        self.role = role
        self.lang = "en" if role != "admin" else "ko"
        self.t = lambda s: _t(s, self.lang)
        self._tax_rows: list[TaxRow] = []
        self._build_ui()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(hdr, text=self.t("세금 내역 입력"), font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkLabel(hdr, text=self.t("(관리자 전용)"), font=ctk.CTkFont(size=13),
                     text_color="gray").pack(side="left", padx=8)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # Date
        self._date_row = DateRow(scroll, on_change=lambda ds: self._refresh_table(), lang=self.lang)
        self._date_row.pack(fill="x", pady=(8, 16))

        # Input card
        card = ctk.CTkFrame(scroll, corner_radius=12)
        card.pack(fill="x", pady=(0, 16))

        card_hdr = ctk.CTkFrame(card, fg_color="transparent")
        card_hdr.pack(fill="x", padx=20, pady=(14, 6))
        ctk.CTkLabel(card_hdr, text=self.t("세금 항목 입력"), font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(card_hdr, text=self.t("+ 행 추가"), width=80, height=30,
                      font=ctk.CTkFont(size=13), command=self._add_row).pack(side="right")

        # Col headers
        col_hdr = ctk.CTkFrame(card, fg_color="#e2e8f0", corner_radius=6)
        col_hdr.pack(fill="x", padx=20, pady=(0, 4))
        for label, width in [(self.t("세금 종류"), 160), (self.t("금액"), 120),
                             (self.t("통화"), 75), (self.t("ft 환산"), 100), ("", 50)]:
            ctk.CTkLabel(col_hdr, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                         width=width).pack(side="left", padx=4, pady=4)

        self.rows_container = ctk.CTkFrame(card, fg_color="transparent")
        self.rows_container.pack(fill="x", padx=20, pady=(0, 14))
        self._add_row()

        # Save + message
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(btn_frame, text=self.t("저장"), width=120, height=44,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      command=self._save).pack(side="left")
        self.msg_label = ctk.CTkLabel(btn_frame, text="", font=ctk.CTkFont(size=13))
        self.msg_label.pack(side="left", padx=16)

        # Table
        table_card = ctk.CTkFrame(scroll, corner_radius=12)
        table_card.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(table_card, text=self.t("세금 내역"), font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(14, 8))
        self.table_inner = ctk.CTkScrollableFrame(table_card, height=220, fg_color="transparent")
        self.table_inner.pack(fill="x", padx=10, pady=(0, 14))
        self._refresh_table()

    def _add_row(self):
        row = TaxRow(self.rows_container, self._remove_row)
        row.pack(fill="x", pady=3)
        self._tax_rows.append(row)

    def _remove_row(self, row):
        if row in self._tax_rows:
            self._tax_rows.remove(row)

    def _get_date_str(self) -> str | None:
        return self._date_row.get_date_str()

    def _save(self):
        date_str = self._get_date_str()
        if not date_str:
            self._show_msg("날짜 형식이 올바르지 않습니다", "red")
            return
        try:
            y, m, _ = (int(x) for x in date_str.split("-"))
        except Exception:
            return

        entries = []
        for row in self._tax_rows:
            d = row.get_data()
            if not d["tax_name"]:
                continue
            d["date"] = date_str
            entries.append(d)

        if not entries:
            self._show_msg(self.t("입력된 항목이 없습니다"), "orange")
            return

        em.save_tax(y, m, entries)
        self._show_msg(self.t("저장되었습니다"), "green")
        self._refresh_table()

    def _refresh_table(self):
        for w in self.table_inner.winfo_children():
            w.destroy()

        ym = self._date_row.get_year_month()
        if not ym:
            return
        y, m = ym

        records = em.load_taxes(y, m)
        headers = [self.t("날짜"), self.t("세금 종류"), self.t("금액(ft)")]
        widths = [100, 200, 120]

        hrow = ctk.CTkFrame(self.table_inner, fg_color="#1a56db", corner_radius=6)
        hrow.pack(fill="x", pady=(0, 2))
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hrow, text=h, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="white", width=w).pack(side="left", padx=4, pady=6)

        if not records:
            ctk.CTkLabel(self.table_inner, text=self.t("기록이 없습니다"), text_color="gray",
                         font=ctk.CTkFont(size=13)).pack(pady=20)
            return

        total = 0.0
        for i, rec in enumerate(records):
            bg = ("#e8f0fe", "#f8faff") if i % 2 == 0 else ("white", "#1e1e2e")
            drow = ctk.CTkFrame(self.table_inner, fg_color=bg, corner_radius=4)
            drow.pack(fill="x", pady=1)
            for val, w in zip([rec["date"], rec["tax_name"], f"{rec['amount_ft']:,.0f}"], widths):
                ctk.CTkLabel(drow, text=str(val), font=ctk.CTkFont(size=12),
                             width=w).pack(side="left", padx=4, pady=5)
            ctk.CTkButton(drow, text="삭제", width=44, height=24,
                          fg_color="#e53e3e", hover_color="#c53030",
                          font=ctk.CTkFont(size=11),
                          command=lambda r=rec, ym=(y, m): self._delete_entry(r, ym)).pack(side="left", padx=2)
            total += rec["amount_ft"]

        trow = ctk.CTkFrame(self.table_inner, fg_color="#dbeafe", corner_radius=4)
        trow.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(trow, text=self.t("합계"), font=ctk.CTkFont(size=12, weight="bold"), width=100).pack(side="left", padx=4)
        ctk.CTkLabel(trow, text="", width=200).pack(side="left")
        ctk.CTkLabel(trow, text=f"{total:,.0f} ft", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#1a56db", width=120).pack(side="left", padx=4, pady=6)

    def _delete_entry(self, entry: dict, ym: tuple):
        import tkinter.messagebox as mb
        msg = f"{entry['date']}  {entry['tax_name']}  {entry['amount_ft']:,.0f} ft\n\n삭제할까요?"
        if not mb.askyesno("삭제 확인", msg):
            return
        y, m = ym
        records = em.load_taxes(y, m)
        records = [r for r in records if not (
            r["date"] == entry["date"] and
            r["tax_name"] == entry["tax_name"] and
            abs(r["amount_ft"] - entry["amount_ft"]) < 0.01
        )]
        em.replace_taxes(y, m, records)
        self._refresh_table()
        self._show_msg(self.t("삭제 완료"), "orange")

    def _show_msg(self, text: str, color: str):
        self.msg_label.configure(text=text, text_color=color)
        self.after(3000, lambda: self.msg_label.configure(text=""))

    def refresh(self):
        self._refresh_table()
