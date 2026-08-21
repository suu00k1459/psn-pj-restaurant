import customtkinter as ctk
from datetime import date
from utils import config_manager as cm
from utils import excel_manager as em
from utils.date_widgets import DateRow
from utils.i18n import t as _t

SALARY_CATS = ("주급", "주급정산", "월급정산", "주급(직원간)", "공식급여", "실질지급")


class AddEmployeeDialog(ctk.CTkToplevel):
    def __init__(self, master, on_add, lang="ko"):
        super().__init__(master)
        self.on_add = on_add
        self.lang = lang
        self.t = lambda s: _t(s, lang)
        self.title(self.t("직원 추가"))
        self.geometry("400x520")
        self.resizable(False, False)
        self.grab_set()
        self._bank_vars = []
        self._build()

    def _build(self):
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=30, pady=(8, 16))
        self.msg = ctk.CTkLabel(bottom, text="", font=ctk.CTkFont(size=13), text_color="red")
        self.msg.pack(pady=(0, 4))
        ctk.CTkButton(bottom, text=self.t("추가"), height=40, font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._confirm).pack(fill="x")

        ctk.CTkLabel(self, text=self.t("직원 추가"), font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 12))

        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)

        self.name_var = ctk.StringVar()
        self.english_name_var = ctk.StringVar()
        self.official_account_var = ctk.StringVar()
        self.pos_var = ctk.StringVar(value="스탭")

        ctk.CTkLabel(form, text=self.t("이름 (한국어)"), font=ctk.CTkFont(size=14), anchor="w").pack(fill="x", pady=(6, 2))
        ctk.CTkEntry(form, textvariable=self.name_var, font=ctk.CTkFont(size=14), height=36).pack(fill="x")

        ctk.CTkLabel(form, text=self.t("이름 (영어)"), font=ctk.CTkFont(size=14), anchor="w").pack(fill="x", pady=(8, 2))
        ctk.CTkEntry(form, textvariable=self.english_name_var, font=ctk.CTkFont(size=14), height=36,
                     placeholder_text="예) Kim Suyoung").pack(fill="x")

        ctk.CTkLabel(form, text=self.t("공식 계좌번호"), font=ctk.CTkFont(size=14), anchor="w").pack(fill="x", pady=(8, 2))
        ctk.CTkEntry(form, textvariable=self.official_account_var, font=ctk.CTkFont(size=14), height=36,
                     placeholder_text="Official Account No.").pack(fill="x")

        pos_opts = ["스탭", "파트타이머"]
        ctk.CTkLabel(form, text=self.t("직급"), font=ctk.CTkFont(size=14), anchor="w").pack(fill="x", pady=(10, 2))
        ctk.CTkComboBox(form, values=pos_opts, variable=self.pos_var,
                        font=ctk.CTkFont(size=14), height=36).pack(fill="x")

        bank_hdr = ctk.CTkFrame(form, fg_color="transparent")
        bank_hdr.pack(fill="x", pady=(10, 2))
        ctk.CTkLabel(bank_hdr, text=self.t("은행 (이름 + 통화)"), font=ctk.CTkFont(size=14), anchor="w").pack(side="left")
        ctk.CTkButton(bank_hdr, text=self.t("+ 은행 추가"), width=90, height=28,
                      font=ctk.CTkFont(size=12), command=self._add_bank_field).pack(side="right")

        col_lbl = ctk.CTkFrame(form, fg_color="transparent")
        col_lbl.pack(fill="x")
        ctk.CTkLabel(col_lbl, text=self.t("은행명"), font=ctk.CTkFont(size=11),
                     text_color="gray50").pack(side="left")
        ctk.CTkLabel(col_lbl, text=self.t("계좌번호"), font=ctk.CTkFont(size=11),
                     text_color="gray50", width=110).pack(side="right", padx=(0, 122))

        self._bank_container = ctk.CTkFrame(form, fg_color="transparent")
        self._bank_container.pack(fill="x")
        self._add_bank_field()

    def _add_bank_field(self, value=None):
        if isinstance(value, dict):
            bank_name = value.get("name", "")
            bank_currency = value.get("currency", "ft")
            bank_account = value.get("account", "")
        else:
            bank_name, bank_currency, bank_account = value or "", "ft", ""
        name_var = ctk.StringVar(value=bank_name)
        curr_var = ctk.StringVar(value=bank_currency)
        acc_var = ctk.StringVar(value=bank_account)
        self._bank_vars.append((name_var, curr_var, acc_var))
        row = ctk.CTkFrame(self._bank_container, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkEntry(row, textvariable=name_var, font=ctk.CTkFont(size=13), height=34,
                     placeholder_text=self.t("은행명")).pack(side="left", fill="x", expand=True)
        ctk.CTkEntry(row, textvariable=acc_var, font=ctk.CTkFont(size=13), height=34,
                     width=110, placeholder_text=self.t("계좌번호")).pack(side="left", padx=(4, 0))
        ctk.CTkComboBox(row, values=["ft", "KRW", "USD", "EUR"], variable=curr_var,
                        width=80, height=34, font=ctk.CTkFont(size=13)).pack(side="left", padx=(4, 0))

        def remove(r=row, nv=name_var, cv=curr_var, av=acc_var):
            if len(self._bank_vars) > 1:
                self._bank_vars.remove((nv, cv, av))
                r.destroy()

        ctk.CTkButton(row, text="×", width=36, height=34, fg_color="#e53e3e", hover_color="#c53030",
                      font=ctk.CTkFont(size=16), command=remove).pack(side="left", padx=(4, 0))

    def _confirm(self):
        name = self.name_var.get().strip()
        if not name:
            self.msg.configure(text=self.t("이름을 입력하세요"))
            return
        english_name = self.english_name_var.get().strip()
        official_account = self.official_account_var.get().strip()
        banks = [{"name": nv.get().strip(), "currency": cv.get(), "account": av.get().strip()}
                 for nv, cv, av in self._bank_vars if nv.get().strip()]
        em.add_employee(name, self.pos_var.get(), banks, english_name=english_name,
                        official_account=official_account)
        self.on_add()
        self.destroy()


class EditEmployeeDialog(ctk.CTkToplevel):
    def __init__(self, master, emp: dict, on_save, lang="ko"):
        super().__init__(master)
        self.emp = emp
        self.on_save = on_save
        self.lang = lang
        self.t = lambda s: _t(s, lang)
        self.title(f"{self.t('직원 수정')} - {emp['name']}")
        self.geometry("400x520")
        self.resizable(False, True)
        self.grab_set()
        self._bank_vars = []
        self._build()

    def _build(self):
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=30, pady=(0, 16))
        self.msg = ctk.CTkLabel(bottom, text="", font=ctk.CTkFont(size=13), text_color="red")
        self.msg.pack(pady=(0, 4))
        ctk.CTkButton(bottom, text=self.t("저장"), height=40, font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._save).pack(fill="x")

        ctk.CTkLabel(self, text=self.t("직원 수정"), font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(self, text=self.emp["name"], font=ctk.CTkFont(size=15), text_color="gray").pack(pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=30)

        self.pos_var = ctk.StringVar(value=self.emp.get("position", "스탭"))
        self.english_name_var = ctk.StringVar(value=self.emp.get("english_name", ""))
        self.official_account_var = ctk.StringVar(value=self.emp.get("official_account", ""))

        ctk.CTkLabel(scroll, text=self.t("영어 이름"), font=ctk.CTkFont(size=14), anchor="w").pack(fill="x", pady=(4, 2))
        ctk.CTkEntry(scroll, textvariable=self.english_name_var, font=ctk.CTkFont(size=14), height=36,
                     placeholder_text="예) Kim Suyoung").pack(fill="x")

        ctk.CTkLabel(scroll, text=self.t("공식 계좌번호"), font=ctk.CTkFont(size=14), anchor="w").pack(fill="x", pady=(8, 2))
        ctk.CTkEntry(scroll, textvariable=self.official_account_var, font=ctk.CTkFont(size=14), height=36,
                     placeholder_text="Official Account No.").pack(fill="x")

        ctk.CTkLabel(scroll, text=self.t("직급"), font=ctk.CTkFont(size=14), anchor="w").pack(fill="x", pady=(10, 2))
        ctk.CTkComboBox(scroll, values=["스탭", "파트타이머"], variable=self.pos_var,
                        font=ctk.CTkFont(size=14), height=36).pack(fill="x")

        bank_hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        bank_hdr.pack(fill="x", pady=(12, 2))
        ctk.CTkLabel(bank_hdr, text=self.t("은행 (이름 + 통화)"), font=ctk.CTkFont(size=14), anchor="w").pack(side="left")
        ctk.CTkButton(bank_hdr, text=self.t("+ 은행 추가"), width=90, height=28,
                      font=ctk.CTkFont(size=12), command=self._add_bank_field).pack(side="right")

        col_lbl = ctk.CTkFrame(scroll, fg_color="transparent")
        col_lbl.pack(fill="x")
        ctk.CTkLabel(col_lbl, text=self.t("은행명"), font=ctk.CTkFont(size=11),
                     text_color="gray50").pack(side="left")
        ctk.CTkLabel(col_lbl, text=self.t("계좌번호"), font=ctk.CTkFont(size=11),
                     text_color="gray50", width=110).pack(side="right", padx=(0, 122))

        self._bank_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self._bank_container.pack(fill="x")

        for bank in self.emp.get("banks", []):
            self._add_bank_field(bank)
        if not self.emp.get("banks"):
            self._add_bank_field()

    def _add_bank_field(self, value=None):
        if isinstance(value, dict):
            bank_name = value.get("name", "")
            bank_currency = value.get("currency", "ft")
            bank_account = value.get("account", "")
        else:
            bank_name, bank_currency, bank_account = value or "", "ft", ""
        name_var = ctk.StringVar(value=bank_name)
        curr_var = ctk.StringVar(value=bank_currency)
        acc_var = ctk.StringVar(value=bank_account)
        self._bank_vars.append((name_var, curr_var, acc_var))
        row = ctk.CTkFrame(self._bank_container, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkEntry(row, textvariable=name_var, font=ctk.CTkFont(size=13), height=34,
                     placeholder_text=self.t("은행명")).pack(side="left", fill="x", expand=True)
        ctk.CTkEntry(row, textvariable=acc_var, font=ctk.CTkFont(size=13), height=34,
                     width=110, placeholder_text=self.t("계좌번호")).pack(side="left", padx=(4, 0))
        ctk.CTkComboBox(row, values=["ft", "KRW", "USD", "EUR"], variable=curr_var,
                        width=80, height=34, font=ctk.CTkFont(size=13)).pack(side="left", padx=(4, 0))

        def remove(r=row, nv=name_var, cv=curr_var, av=acc_var):
            self._bank_vars.remove((nv, cv, av))
            r.destroy()

        ctk.CTkButton(row, text="×", width=36, height=34, fg_color="#e53e3e", hover_color="#c53030",
                      font=ctk.CTkFont(size=16), command=remove).pack(side="left", padx=(4, 0))

    def _save(self):
        english_name = self.english_name_var.get().strip()
        official_account = self.official_account_var.get().strip()
        banks = [{"name": nv.get().strip(), "currency": cv.get(), "account": av.get().strip()}
                 for nv, cv, av in self._bank_vars if nv.get().strip()]
        em.update_employee(self.emp["name"], {
            "english_name": english_name,
            "official_account": official_account,
            "position": self.pos_var.get(),
            "banks": banks,
        })
        self.on_save()
        self.destroy()


class TransferDialog(ctk.CTkToplevel):
    def __init__(self, master, employees: list[str], on_confirm, from_name: str = "", lang="ko"):
        super().__init__(master)
        self.on_confirm = on_confirm
        self._from_name = from_name
        self.lang = lang
        self.t = lambda s: _t(s, lang)
        self.title(self.t("직원 간 선지급 이동"))
        self.geometry("400x360")
        self.resizable(False, False)
        self.grab_set()
        self._build(employees)

    def _build(self, employees: list[str]):
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=30, pady=(8, 16))
        self.msg = ctk.CTkLabel(bottom, text="", font=ctk.CTkFont(size=13), text_color="red")
        self.msg.pack(pady=(0, 4))
        ctk.CTkButton(bottom, text=self.t("처리"), height=40, font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._confirm).pack(fill="x")

        ctk.CTkLabel(self, text=self.t("직원 간 선지급 이동"),
                     font=ctk.CTkFont(size=17, weight="bold")).pack(pady=(16, 10))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=30)

        self._date_row = DateRow(form, lang=self.lang)
        self._date_row.pack(fill="x", pady=(0, 10))

        a_row = ctk.CTkFrame(form, fg_color="transparent")
        a_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(a_row, text=self.t("지급 직원:"), font=ctk.CTkFont(size=13), width=80, anchor="w").pack(side="left")
        if self._from_name:
            ctk.CTkLabel(a_row, text=self._from_name,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="#1a56db").pack(side="left")
        else:
            self.from_var = ctk.StringVar(value=employees[0] if employees else "")
            ctk.CTkComboBox(a_row, values=employees, variable=self.from_var,
                            font=ctk.CTkFont(size=13), height=32).pack(side="left", fill="x", expand=True)

        b_row = ctk.CTkFrame(form, fg_color="transparent")
        b_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(b_row, text=self.t("수령 직원:"), font=ctk.CTkFont(size=13), width=80, anchor="w").pack(side="left")
        other = [e for e in employees if e != self._from_name] if self._from_name else employees
        self.to_var = ctk.StringVar(value=other[0] if other else "")
        ctk.CTkComboBox(b_row, values=other if other else employees, variable=self.to_var,
                        font=ctk.CTkFont(size=13), height=32).pack(side="left", fill="x", expand=True)

        amt_row = ctk.CTkFrame(form, fg_color="transparent")
        amt_row.pack(fill="x")
        ctk.CTkLabel(amt_row, text=self.t("금액 (ft):"), font=ctk.CTkFont(size=13), width=80, anchor="w").pack(side="left")
        self.amount_var = ctk.StringVar(value="0")
        ctk.CTkEntry(amt_row, textvariable=self.amount_var, font=ctk.CTkFont(size=13), height=32).pack(
            side="left", fill="x", expand=True)

    def _confirm(self):
        from_name = self._from_name or getattr(self, "from_var", ctk.StringVar()).get()
        to_name = self.to_var.get()
        date_str = self._date_row.get_date_str()
        if not date_str:
            self.msg.configure(text=self.t("날짜를 입력하세요"))
            return
        if from_name == to_name or not to_name:
            self.msg.configure(text=self.t("다른 직원을 선택하세요"))
            return
        try:
            amt = float(self.amount_var.get())
        except ValueError:
            self.msg.configure(text=self.t("금액을 올바르게 입력하세요"))
            return
        if amt <= 0:
            self.msg.configure(text=self.t("금액은 0보다 커야 합니다"))
            return
        em.transfer_prepay(from_name, to_name, amt, date_str)
        self.on_confirm()
        self.destroy()


class EditWageDialog(ctk.CTkToplevel):
    def __init__(self, master, h: dict, name: str, on_save, lang="ko"):
        super().__init__(master)
        self.h = h
        self.name = name
        self.on_save = on_save
        self.lang = lang
        self.t = lambda s: _t(s, lang)
        self.title(self.t("주급 수정"))
        self.geometry("360x230")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text=self.t("주급 수정"),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(16, 8))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24)

        self._date_row = DateRow(form, lang=self.lang)
        date_str = self.h.get("date", "")
        if date_str and len(date_str) == 10:
            self._date_row.year_var.set(date_str[:4])
            self._date_row.month_var.set(date_str[5:7])
            self._date_row.day_var.set(date_str[8:10])
        self._date_row.pack(fill="x", pady=(0, 8))

        amt_row = ctk.CTkFrame(form, fg_color="transparent")
        amt_row.pack(fill="x")
        ctk.CTkLabel(amt_row, text=self.t("금액 (ft):"), font=ctk.CTkFont(size=13), width=80, anchor="w").pack(side="left")
        self.amount_var = ctk.StringVar(value=str(self.h.get("amount", 0)))
        ctk.CTkEntry(amt_row, textvariable=self.amount_var, font=ctk.CTkFont(size=13), height=32).pack(
            side="left", fill="x", expand=True)

        self.msg = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12), text_color="red")
        self.msg.pack(pady=6)

        ctk.CTkButton(self, text=self.t("저장"), height=36, font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._save).pack(padx=24, fill="x", pady=(0, 12))

    def _save(self):
        date_str = self._date_row.get_date_str()
        if not date_str:
            self.msg.configure(text=self.t("날짜를 입력하세요"))
            return
        try:
            amount = float(self.amount_var.get())
        except ValueError:
            self.msg.configure(text=self.t("금액을 올바르게 입력하세요"))
            return
        if amount <= 0:
            self.msg.configure(text=self.t("금액은 0보다 커야 합니다"))
            return
        self.on_save(date_str, amount)
        self.destroy()


class BalanceEditDialog(ctk.CTkToplevel):
    def __init__(self, master, name: str, current: float, on_save, lang="ko"):
        super().__init__(master)
        self.lang = lang
        self.t = lambda s: _t(s, lang)
        self.title(self.t("선지급 잔액 수정") if lang == "ko" else "Edit Prepay Balance")
        self.geometry("340x200")
        self.resizable(False, False)
        self.grab_set()

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=24, pady=(8, 16))
        self.msg = ctk.CTkLabel(bottom, text="", font=ctk.CTkFont(size=12), text_color="red")
        self.msg.pack(pady=(0, 4))
        ctk.CTkButton(bottom, text=self.t("저장"), height=36, font=ctk.CTkFont(size=13, weight="bold"),
                      command=lambda: self._save(name, on_save)).pack(fill="x")

        ctk.CTkLabel(self, text=self.t("선지급 잔액 직접 수정"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(16, 4))
        ctk.CTkLabel(self, text=self.t("히스토리와 실제 잔액이 맞지 않을 때 사용"),
                     font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(0, 12))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=24)
        new_bal_lbl = "New Balance (ft):" if lang == "en" else "새 잔액 (ft):"
        ctk.CTkLabel(row, text=new_bal_lbl, font=ctk.CTkFont(size=13), width=100, anchor="w").pack(side="left")
        self.amount_var = ctk.StringVar(value=str(current))
        ctk.CTkEntry(row, textvariable=self.amount_var, font=ctk.CTkFont(size=13), height=32).pack(
            side="left", fill="x", expand=True)

    def _save(self, name: str, on_save):
        try:
            new_bal = float(self.amount_var.get())
        except ValueError:
            self.msg.configure(text="Enter a number" if self.lang == "en" else "숫자를 입력하세요")
            return
        data = em.load_prepay()
        if name not in data:
            data[name] = {"balance": 0.0, "history": []}
        old_bal = data[name]["balance"]
        data[name]["balance"] = round(new_bal, 2)
        data[name]["history"].append({
            "date": date.today().strftime("%Y-%m-%d"),
            "method": "잔액수정",
            "amount": round(new_bal - old_bal, 2),
        })
        em.save_prepay(data)
        on_save()
        self.destroy()


# ─────────────────────────────────────────────
# 직원 관리 메인 페이지
# ─────────────────────────────────────────────

class EmployeePage(ctk.CTkFrame):
    def __init__(self, master, role: str):
        super().__init__(master, fg_color="transparent")
        self.role = role
        self.lang = "en" if role != "admin" else "ko"
        self.t = lambda s: _t(s, self.lang)
        self._selected_name: str | None = None
        self._view_mode = "list"
        self._hist_selected_h: dict | None = None
        self._hist_row_refs: list = []
        self._build_ui()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(hdr, text=self.t("직원 관리"),
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        self.hdr_msg = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont(size=13))
        self.hdr_msg.pack(side="right")
        ctk.CTkButton(hdr, text=self.t("삭제"), width=70, height=32,
                      fg_color="#e53e3e", hover_color="#c53030",
                      font=ctk.CTkFont(size=13),
                      command=self._delete_employee).pack(side="right", padx=(8, 0))
        ctk.CTkButton(hdr, text=self.t("+ 직원 추가"), width=100, height=32,
                      font=ctk.CTkFont(size=13),
                      command=self._add_employee).pack(side="right", padx=(0, 4))

        # 콘텐츠 컨테이너 (스크롤 없음, 나머지 공간 채움)
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        self._content.bind("<Configure>", self._on_content_resize, add=True)

        # ── 리스트 뷰 (기본: CTkScrollableFrame) — 고정 높이로 생성
        self._list_scroll = ctk.CTkScrollableFrame(self._content, height=400, fg_color="transparent")

        # ── 분할 뷰 (상세 모드에서 표시)
        self._split_frame = ctk.CTkFrame(self._content, fg_color="transparent")

        # 왼쪽 패널: 좁은 이름 목록
        self._left_scroll = ctk.CTkScrollableFrame(
            self._split_frame, width=190,
            fg_color=("gray95", "gray17"), corner_radius=10
        )
        self._left_scroll.pack(side="left", fill="both", padx=(0, 8))

        # 오른쪽 패널: 상세 정보
        self._right_scroll = ctk.CTkScrollableFrame(self._split_frame, fg_color="transparent")
        self._right_scroll.pack(side="left", fill="both", expand=True)

        self._show_list_mode()
        self._refresh_list()

    def _on_content_resize(self, event):
        if self._view_mode == "list":
            self._list_scroll.configure(height=event.height)

    # ── 뷰 모드 전환 ─────────────────────────────────────────────────

    def _show_list_mode(self):
        self._view_mode = "list"
        self._split_frame.pack_forget()
        h = self._content.winfo_height()
        if h > 1:
            self._list_scroll.configure(height=h)
        self._list_scroll.pack(fill="x")

    def _show_detail_mode(self, name: str):
        self._view_mode = "detail"
        self._list_scroll.pack_forget()
        self._split_frame.pack(fill="both", expand=True)
        self._selected_name = name
        self._refresh_left_panel()
        self._build_detail(name)

    # ── 전체 직원 목록 (리스트 뷰) ───────────────────────────────────

    def _refresh_list(self):
        for w in self._list_scroll.winfo_children():
            w.destroy()

        employees = em.load_employees()
        staff = [e for e in employees if e.get("position") == "스탭"]
        parts = [e for e in employees if e.get("position") != "스탭"]
        taxes = cm.get_staff_taxes()
        total_tax_rate = sum(t["rate"] for t in taxes)

        if not employees:
            no_emp_msg = "No staff registered. Click [+ Add Staff] to add." if self.lang == "en" \
                else "등록된 직원이 없습니다. [+ 직원 추가] 버튼으로 등록하세요."
            ctk.CTkLabel(self._list_scroll, text=no_emp_msg,
                         text_color="gray", font=ctk.CTkFont(size=13)).pack(pady=20)
            return

        hrow = ctk.CTkFrame(self._list_scroll, fg_color="#1a56db", corner_radius=6)
        hrow.pack(fill="x", padx=4, pady=(0, 2))
        list_cols = [(self.t("이름 / 계좌"), 180), (self.t("직급"), 90),
                     (self.t("공식급여 / 시급"), 150), (self.t("세후 급여"), 120)]
        if self.role == "admin":
            list_cols.insert(2, (self.t("선지급 잔액"), 120))
        for text, w in list_cols:
            ctk.CTkLabel(hrow, text=text, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="white", width=w, height=26).pack(side="left", padx=4, pady=1)

        # 스탭: 초록, 파트타이머: 주황
        GROUP_COLOR = {"스탭": "#276749", "파트타이머": "#c05000"}
        GROUP_BG    = {"스탭": ("#d1fae5", "#14291f"), "파트타이머": ("#ffedd5", "#2a1500")}

        def _make_section(label, emps, display_label=None):
            if not emps:
                return
            display_label = display_label or label
            gc = GROUP_COLOR.get(label, "#1a56db")
            gb = GROUP_BG.get(label, ("gray85", "gray25"))

            sec = ctk.CTkFrame(self._list_scroll, fg_color=gb, corner_radius=6)
            sec.pack(fill="x", padx=4, pady=(3, 1))
            ctk.CTkFrame(sec, width=5, height=1, fg_color=gc, corner_radius=2).pack(
                side="left", fill="y", padx=(5, 0), pady=1)
            ctk.CTkLabel(sec, text=display_label, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=gc, height=20).pack(side="left", padx=(5, 0), pady=1)
            count_txt = f"({len(emps)})" if self.lang == "en" else f"({len(emps)}명)"
            ctk.CTkLabel(sec, text=count_txt, font=ctk.CTkFont(size=11),
                         text_color=gc, height=20).pack(side="left", padx=(3, 0), pady=1)

            for i, emp in enumerate(emps):
                is_sel = emp["name"] == self._selected_name
                if is_sel:
                    bg = ("#c7d8f5", "#2a3a5c")
                else:
                    bg = ("#e8f0fe", "#1f2937") if i % 2 == 0 else ("white", "#1e1e2e")

                row = ctk.CTkFrame(self._list_scroll, fg_color=bg, corner_radius=4)
                row.pack(fill="x", padx=4, pady=1)

                # 그룹 색 좌측 인디케이터
                ctk.CTkFrame(row, width=4, height=1, fg_color=gc, corner_radius=2).pack(
                    side="left", fill="y", padx=(3, 4), pady=0)

                info = em.get_employee_salary(emp["name"])
                balance = em.get_prepay_balance(emp["name"])
                is_part = emp.get("position") != "스탭"
                official = info.get("official_salary", 0)
                weekly = info.get("weekly_wage", 0)
                hourly = info.get("hourly_wage", 0)
                tax_amt = round(official * total_tax_rate / 100, 2)
                net = round(official - tax_amt, 2)

                def _lbl(parent, text, width, **kw):
                    l = ctk.CTkLabel(parent, text=text, width=width, height=24,
                                     font=ctk.CTkFont(size=12), **kw)
                    l.pack(side="left", padx=3, pady=0)
                    return l

                # 이름 셀: 한국어 이름 + 영어 이름 + 계좌 정보
                name_frame = ctk.CTkFrame(row, fg_color="transparent")
                name_frame.pack(side="left", padx=(0, 3), pady=1)
                name_lbl = ctk.CTkLabel(name_frame, text=emp["name"], anchor="w", width=175, height=20,
                                        font=ctk.CTkFont(size=12, weight="bold"))
                name_lbl.pack(anchor="w")
                eng = emp.get("english_name", "")
                if eng:
                    ctk.CTkLabel(name_frame, text=eng, anchor="w", width=175, height=14,
                                 font=ctk.CTkFont(size=10), text_color="gray50").pack(anchor="w")
                for bank in emp.get("banks", []):
                    b_name = bank.get("name", "")
                    b_acc = bank.get("account", "")
                    b_txt = f"{b_name}  {b_acc}" if b_acc else b_name
                    if b_txt:
                        ctk.CTkLabel(name_frame, text=b_txt, anchor="w", width=175, height=14,
                                     font=ctk.CTkFont(size=10), text_color="gray50").pack(anchor="w")

                pos_lbl  = _lbl(row, self.t(emp.get("position", "")), 90,
                                 text_color="#dd6b20" if is_part else "#276749")
                bal_lbl = None
                if self.role == "admin":
                    bal_lbl = _lbl(row, f"{balance:,.0f} ft", 120,
                                   text_color="#1a56db" if balance > 0 else "gray50")
                if is_part:
                    salary_txt = f"{hourly:,.0f} ft/h" if hourly else "—"
                else:
                    salary_txt = f"{official:,.0f} ft"
                sal_lbl  = _lbl(row, salary_txt, 150,
                                 text_color="#c05000" if is_part and hourly else ("gray50" if is_part else None) or "gray10")
                net_txt  = f"{net:,.0f} ft" if not is_part and official else \
                           (f"{round(weekly*(1-total_tax_rate/100),2):,.0f} ft" if is_part and weekly else "—")
                net_lbl  = _lbl(row, net_txt, 120,
                                 text_color="#276749" if net_txt != "—" else "gray50")

                ctk.CTkButton(row, text=self.t("▼ 상세"), width=64, height=24,
                              font=ctk.CTkFont(size=11),
                              fg_color="#1a56db" if is_sel else ("gray80", "gray35"),
                              hover_color="#1440a0" if is_sel else ("gray70", "gray25"),
                              command=lambda n=emp["name"]: self._show_detail_mode(n)).pack(side="right", padx=6)

                # 행 및 레이블 클릭 → 선택
                click_fn = lambda e, n=emp["name"]: self._select_in_list(n)
                row.bind("<Button-1>", click_fn)
                for w in [lbl for lbl in (name_frame, pos_lbl, bal_lbl, sal_lbl, net_lbl) if lbl is not None]:
                    w.bind("<Button-1>", click_fn)
                for child in name_frame.winfo_children():
                    child.bind("<Button-1>", click_fn)

        _make_section("스탭", staff, self.t("스탭"))
        if staff and parts:
            ctk.CTkFrame(self._list_scroll, height=2, fg_color=("gray75", "gray35"),
                         corner_radius=0).pack(fill="x", padx=8, pady=(8, 4))
        _make_section("파트타이머", parts, self.t("파트타이머"))
        ctk.CTkFrame(self._list_scroll, height=8, fg_color="transparent").pack()

    def _select_in_list(self, name: str):
        self._selected_name = name
        self._refresh_list()

    # ── 왼쪽 패널 (상세 모드) ────────────────────────────────────────

    def _refresh_left_panel(self):
        for w in self._left_scroll.winfo_children():
            w.destroy()

        GROUP_COLOR = {"스탭": "#276749", "파트타이머": "#c05000"}
        GROUP_BG    = {"스탭": ("#d1fae5", "#14291f"), "파트타이머": ("#ffedd5", "#2a1500")}

        # 상단: 리스트 보기 버튼
        top_row = ctk.CTkFrame(self._left_scroll, fg_color="transparent")
        top_row.pack(fill="x", pady=(4, 6), padx=4)
        ctk.CTkLabel(top_row, text=self.t("직원"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(top_row, text=self.t("리스트 보기"), width=82, height=24,
                      font=ctk.CTkFont(size=11),
                      fg_color=("gray80", "gray35"), hover_color=("gray70", "gray25"),
                      command=self._on_back_to_list).pack(side="right")

        employees = em.load_employees()
        staff = [e for e in employees if e.get("position") == "스탭"]
        parts = [e for e in employees if e.get("position") != "스탭"]

        def _make_left_section(label, emps, display_label=None):
            if not emps:
                return
            display_label = display_label or label
            gc = GROUP_COLOR.get(label, "#1a56db")
            gb = GROUP_BG.get(label, ("gray85", "gray25"))

            sec = ctk.CTkFrame(self._left_scroll, fg_color=gb, corner_radius=4)
            sec.pack(fill="x", padx=4, pady=(3, 1))
            ctk.CTkFrame(sec, width=3, height=1, fg_color=gc, corner_radius=1).pack(
                side="left", fill="y", padx=(4, 0), pady=1)
            ctk.CTkLabel(sec, text=display_label, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=gc).pack(side="left", padx=(4, 0), pady=1)

            for emp in emps:
                is_sel = emp["name"] == self._selected_name
                row = ctk.CTkFrame(self._left_scroll,
                                   fg_color=("#c7d8f5", "#2a3a5c") if is_sel else "transparent",
                                   corner_radius=4)
                row.pack(fill="x", padx=4, pady=1)

                # 그룹 색 좌측 인디케이터
                ctk.CTkFrame(row, width=3, height=1, fg_color=gc, corner_radius=1).pack(
                    side="left", fill="y", padx=(3, 3), pady=1)

                btn = ctk.CTkButton(
                    row, text=emp["name"], height=24,
                    font=ctk.CTkFont(size=12, weight="bold" if is_sel else "normal"),
                    fg_color="transparent",
                    text_color=("#1440a0" if is_sel else ("gray10", "white")),
                    hover_color=("gray85", "gray25"),
                    anchor="w",
                    command=lambda n=emp["name"]: self._on_left_name_click(n)
                )
                btn.pack(side="left", fill="x", expand=True)

        _make_left_section("스탭", staff, self.t("스탭"))
        _make_left_section("파트타이머", parts, self.t("파트타이머"))

    def _on_left_name_click(self, name: str):
        self._selected_name = name
        self._refresh_left_panel()
        for w in self._right_scroll.winfo_children():
            w.destroy()
        self._build_detail(name)

    def _on_back_to_list(self):
        self._selected_name = None
        self._show_list_mode()
        self._refresh_list()

    # ── 상세 패널 ────────────────────────────────────────────────────

    def _build_detail(self, name: str):
        for w in self._right_scroll.winfo_children():
            w.destroy()

        employees = em.load_employees()
        emp = next((e for e in employees if e["name"] == name), None)
        if not emp:
            return

        # 이름 + 영어 이름 + 직급 + 수정 버튼
        hdr = ctk.CTkFrame(self._right_scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text=name, font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        eng_name = emp.get("english_name", "")
        if eng_name:
            ctk.CTkLabel(hdr, text=f"· {eng_name}",
                         font=ctk.CTkFont(size=14), text_color="gray50").pack(side="left", padx=(6, 0))
        ctk.CTkLabel(hdr, text=emp.get("position", ""),
                     font=ctk.CTkFont(size=13), text_color="gray").pack(side="left", padx=(8, 0))
        ctk.CTkButton(hdr, text=self.t("수정"), width=60, height=28, font=ctk.CTkFont(size=12),
                      command=lambda: self._edit_employee(emp)).pack(side="right")

        banks = emp.get("banks", [])
        official_account = emp.get("official_account", "")
        if banks:
            banks_str = ", ".join(
                f"{b['name']}({b.get('currency', 'ft')})" if isinstance(b, dict) else b
                for b in banks)
            ctk.CTkLabel(self._right_scroll, text=f"{self.t('계좌:')} {banks_str}",
                         font=ctk.CTkFont(size=12), text_color="gray",
                         anchor="w").pack(fill="x", pady=(0, 2))
        if official_account:
            acc_lbl = f"Official Acct: {official_account}" if self.lang == "en" else f"공식계좌: {official_account}"
            ctk.CTkLabel(self._right_scroll, text=acc_lbl,
                         font=ctk.CTkFont(size=12), text_color="gray",
                         anchor="w").pack(fill="x", pady=(0, 8))
        elif banks:
            ctk.CTkFrame(self._right_scroll, height=6, fg_color="transparent").pack()

        if self.role == "admin":
            balance = em.get_prepay_balance(name)
            bal_card = ctk.CTkFrame(self._right_scroll, corner_radius=10)
            bal_card.pack(fill="x", pady=(0, 10))
            bal_row = ctk.CTkFrame(bal_card, fg_color="transparent")
            bal_row.pack(fill="x", padx=16, pady=12)
            ctk.CTkLabel(bal_row, text=self.t("선지급 잔액"),
                         font=ctk.CTkFont(size=14)).pack(side="left")
            ctk.CTkLabel(bal_row, text=f"{balance:,.0f} ft",
                         font=ctk.CTkFont(size=16, weight="bold"),
                         text_color="#1a56db" if balance > 0 else ("gray" if balance == 0 else "#e53e3e")
                         ).pack(side="left", padx=(12, 0))
            ctk.CTkButton(bal_row, text=self.t("초기화"), width=60, height=28,
                          fg_color="#e53e3e", hover_color="#c53030", font=ctk.CTkFont(size=11),
                          command=lambda: self._reset_prepay(name)).pack(side="right")
            ctk.CTkButton(bal_row, text=self.t("잔액수정"), width=66, height=28,
                          fg_color=("gray60", "gray40"), hover_color=("gray50", "gray30"),
                          font=ctk.CTkFont(size=11),
                          command=lambda: BalanceEditDialog(
                              self, name, balance, lambda: self._build_detail(name), lang=self.lang
                          )).pack(side="right", padx=(0, 6))

        # 급여 섹션 (스탭 / 파트타이머 공통 — 세금 모두 적용)
        if emp.get("position") == "스탭":
            self._build_salary_staff(self._right_scroll, name)
        else:
            self._build_salary_part(self._right_scroll, name)

        if self.role == "admin" and len(employees) > 1:
            ctk.CTkButton(self._right_scroll, text=self.t("직원 간 선지급 이동"), width=160, height=36,
                          fg_color="#6b46c1", hover_color="#553c9a", font=ctk.CTkFont(size=13),
                          command=lambda: self._open_transfer_dialog(name)).pack(anchor="w", pady=(0, 10))

        # 내역
        hist_card = ctk.CTkFrame(self._right_scroll, corner_radius=10)
        hist_card.pack(fill="x", pady=(0, 10))
        self._build_pay_history(hist_card, name)

    # ── 스탭 급여 ────────────────────────────────────────────────────

    def _build_salary_staff(self, parent, name: str):
        info = em.get_employee_salary(name)
        taxes = cm.get_staff_taxes()

        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(card, text=self.t("급여 정보 (스탭)"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=16, pady=(12, 8))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(0, 12))

        off_row = ctk.CTkFrame(inner, fg_color="transparent")
        off_row.pack(fill="x", pady=2)
        ctk.CTkLabel(off_row, text=self.t("공식 지급액 (ft)"),
                     font=ctk.CTkFont(size=13), width=160).pack(side="left")
        self.official_var = ctk.StringVar(value=str(info.get("official_salary", 0)))
        off_e = ctk.CTkEntry(off_row, textvariable=self.official_var, width=140, font=ctk.CTkFont(size=13))
        off_e.pack(side="left")
        off_e.bind("<KeyRelease>", lambda e: self._recalc_salary(name, taxes))

        # 세금 항목
        tax_f = ctk.CTkFrame(inner, fg_color=("#f0f4f8", "#1e1e2e"), corner_radius=6)
        tax_f.pack(fill="x", pady=(4, 4))
        self.tax_labels: dict = {}
        for t in taxes:
            trow = ctk.CTkFrame(tax_f, fg_color="transparent")
            trow.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(trow, text=f"{t['name']} ({t['rate']}%)",
                         font=ctk.CTkFont(size=12), width=220, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(trow, text="0 ft", font=ctk.CTkFont(size=12),
                               text_color="#e53e3e", width=100, anchor="w")
            lbl.pack(side="left", padx=(12, 0))
            self.tax_labels[t["name"]] = lbl

        net_row = ctk.CTkFrame(inner, fg_color="transparent")
        net_row.pack(fill="x", pady=2)
        ctk.CTkLabel(net_row, text=self.t("세후 공식 급여"),
                     font=ctk.CTkFont(size=13, weight="bold"), width=160).pack(side="left")
        self.net_salary_label = ctk.CTkLabel(net_row, text="0 ft",
                                             font=ctk.CTkFont(size=14, weight="bold"),
                                             text_color="#1a56db")
        self.net_salary_label.pack(side="left")

        self.actual_var = ctk.StringVar(value=str(info.get("actual_salary", 0)))
        if self.role == "admin":
            act_row = ctk.CTkFrame(inner, fg_color="transparent")
            act_row.pack(fill="x", pady=2)
            ctk.CTkLabel(act_row, text=self.t("실질 지급액 (ft)"),
                         font=ctk.CTkFont(size=13), width=160).pack(side="left")
            ctk.CTkEntry(act_row, textvariable=self.actual_var, width=140, font=ctk.CTkFont(size=13)).pack(side="left")

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(6, 0))
        ctk.CTkButton(btn_row, text=self.t("저장"), width=90, height=34, font=ctk.CTkFont(size=13),
                      command=lambda: self._save_staff_salary(name, taxes)).pack(side="left", padx=(0, 8))
        if self.role == "admin":
            ctk.CTkButton(btn_row, text=self.t("월급 정산"), width=100, height=34,
                          fg_color="#38a169", hover_color="#276749", font=ctk.CTkFont(size=13),
                          command=lambda: self._settle_staff(name)).pack(side="left")
        self.salary_msg = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=12))
        self.salary_msg.pack(side="left", padx=8)

        self._recalc_salary(name, taxes)

    # ── 파트타이머 급여 (세금 포함) ───────────────────────────────────

    def _build_salary_part(self, parent, name: str):
        info = em.get_employee_salary(name)
        taxes = cm.get_staff_taxes()

        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(card, text=self.t("급여 정보 (파트타이머)"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=16, pady=(12, 8))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(0, 12))

        hw_row = ctk.CTkFrame(inner, fg_color="transparent")
        hw_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(hw_row, text=self.t("시급 (ft/h)"),
                     font=ctk.CTkFont(size=13, weight="bold"), width=160).pack(side="left")
        self.hourly_var = ctk.StringVar(value=str(info.get("hourly_wage", 0)))
        ctk.CTkEntry(hw_row, textvariable=self.hourly_var, width=140, font=ctk.CTkFont(size=13)).pack(side="left")

        ctk.CTkFrame(inner, height=1, fg_color=("gray80", "gray40"), corner_radius=0).pack(fill="x", pady=(4, 8))

        self.part_date_row = DateRow(inner, lang=self.lang)
        self.part_date_row.pack(fill="x", pady=(0, 8))

        off_row = ctk.CTkFrame(inner, fg_color="transparent")
        off_row.pack(fill="x", pady=2)
        ctk.CTkLabel(off_row, text=self.t("공식 지급액 (ft)"),
                     font=ctk.CTkFont(size=13), width=160).pack(side="left")
        self.official_var = ctk.StringVar(value=str(info.get("official_salary", 0)))
        off_e = ctk.CTkEntry(off_row, textvariable=self.official_var, width=140, font=ctk.CTkFont(size=13))
        off_e.pack(side="left")
        off_e.bind("<KeyRelease>", lambda e: self._recalc_salary(name, taxes))

        # 세금 항목
        tax_f = ctk.CTkFrame(inner, fg_color=("#f0f4f8", "#1e1e2e"), corner_radius=6)
        tax_f.pack(fill="x", pady=(4, 4))
        self.tax_labels: dict = {}
        for t in taxes:
            trow = ctk.CTkFrame(tax_f, fg_color="transparent")
            trow.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(trow, text=f"{t['name']} ({t['rate']}%)",
                         font=ctk.CTkFont(size=12), width=220, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(trow, text="0 ft", font=ctk.CTkFont(size=12),
                               text_color="#e53e3e", width=100, anchor="w")
            lbl.pack(side="left", padx=(12, 0))
            self.tax_labels[t["name"]] = lbl

        net_row = ctk.CTkFrame(inner, fg_color="transparent")
        net_row.pack(fill="x", pady=2)
        ctk.CTkLabel(net_row, text=self.t("세후 급여"),
                     font=ctk.CTkFont(size=13, weight="bold"), width=160).pack(side="left")
        self.net_salary_label = ctk.CTkLabel(net_row, text="0 ft",
                                             font=ctk.CTkFont(size=14, weight="bold"),
                                             text_color="#1a56db")
        self.net_salary_label.pack(side="left")

        self.actual_var = ctk.StringVar(value=str(info.get("actual_salary", 0)))
        if self.role == "admin":
            act_row = ctk.CTkFrame(inner, fg_color="transparent")
            act_row.pack(fill="x", pady=2)
            ctk.CTkLabel(act_row, text=self.t("실질 지급액 (ft)"),
                         font=ctk.CTkFont(size=13), width=160).pack(side="left")
            ctk.CTkEntry(act_row, textvariable=self.actual_var, width=140, font=ctk.CTkFont(size=13)).pack(side="left")

        balance = em.get_prepay_balance(name)
        self.weekly_var = ctk.StringVar(value="0")
        w_row = ctk.CTkFrame(inner, fg_color="transparent")
        w_row.pack(fill="x", pady=(4, 10))
        ctk.CTkLabel(w_row, text=self.t("이번 주급 (ft)"), font=ctk.CTkFont(size=13), width=160).pack(side="left")
        ctk.CTkEntry(w_row, textvariable=self.weekly_var, width=140, font=ctk.CTkFont(size=13)).pack(side="left")

        if self.role == "admin":
            net2_row = ctk.CTkFrame(inner, fg_color="transparent")
            net2_row.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(net2_row, text=self.t("정산 후 상태"), font=ctk.CTkFont(size=12),
                         text_color="gray50", width=160).pack(side="left")
            self.part_net_label = ctk.CTkLabel(net2_row, text="", font=ctk.CTkFont(size=13, weight="bold"))
            self.part_net_label.pack(side="left")

            def _update_net(*_):
                try:
                    w = float(self.weekly_var.get())
                except ValueError:
                    w = 0.0
                b = em.get_prepay_balance(name)
                diff = round(w - b, 2)
                if self.lang == "en":
                    if b == 0:
                        self.part_net_label.configure(text=f"Pay {w:,.0f} ft", text_color="#1a56db")
                    elif diff > 0:
                        self.part_net_label.configure(text=f"Additional {diff:,.0f} ft", text_color="#38a169")
                    elif diff < 0:
                        self.part_net_label.configure(text=f"Prepay {-diff:,.0f} ft remaining", text_color="#c05000")
                    else:
                        self.part_net_label.configure(text="Prepay settled", text_color="#38a169")
                else:
                    if b == 0:
                        self.part_net_label.configure(text=f"지급 {w:,.0f} ft", text_color="#1a56db")
                    elif diff > 0:
                        self.part_net_label.configure(text=f"추가 지급 {diff:,.0f} ft", text_color="#38a169")
                    elif diff < 0:
                        self.part_net_label.configure(text=f"선지급 {-diff:,.0f} ft 남음", text_color="#c05000")
                    else:
                        self.part_net_label.configure(text="선지급 완납", text_color="#38a169")

            self.weekly_var.trace_add("write", _update_net)
            _update_net()

        self.part_tax_var = ctk.StringVar(value="0")

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x")
        ctk.CTkButton(btn_row, text=self.t("저장"), width=90, height=34, font=ctk.CTkFont(size=13),
                      command=lambda: self._save_part_salary(name, taxes)).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text=self.t("주급 정산"), width=100, height=34,
                      fg_color="#38a169", hover_color="#276749", font=ctk.CTkFont(size=13),
                      command=lambda: self._settle_part(name)).pack(side="left")
        self.salary_msg = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=12))
        self.salary_msg.pack(side="left", padx=8)

        self._recalc_salary(name, taxes)

    # ── 세금 계산 ────────────────────────────────────────────────────

    def _recalc_salary(self, name: str, taxes: list):
        try:
            official = float(self.official_var.get())
        except (ValueError, AttributeError):
            official = 0.0
        total_tax = 0.0
        for t in taxes:
            amt = round(official * t["rate"] / 100, 2)
            total_tax += amt
            if t["name"] in self.tax_labels:
                self.tax_labels[t["name"]].configure(text=f"{amt:,.0f} ft")
        self.net_salary_label.configure(text=f"{round(official - total_tax, 2):,.0f} ft")

    # ── 저장 (급여 설정 + Excel 내역 기록) ───────────────────────────

    def _save_staff_salary(self, name: str, taxes: list):
        try:
            official = float(self.official_var.get())
        except (ValueError, AttributeError):
            official = 0.0
        try:
            actual = float(self.actual_var.get())
        except (ValueError, AttributeError):
            actual = 0.0

        info = em.get_employee_salary(name)
        info["official_salary"] = official
        info["actual_salary"] = actual
        em.set_employee_salary(name, info)

        self._record_salary_to_excel(name, "스탭", official, actual)
        self._apply_official_salary_to_prepay(name, official)
        self._refresh_list()
        self._build_detail(name)
        self._show_hdr_msg(self.t("급여 저장됨"), "green")

    def _save_part_salary(self, name: str, taxes: list):
        try:
            official = float(self.official_var.get())
        except (ValueError, AttributeError):
            official = 0.0
        try:
            actual = float(self.actual_var.get())
        except (ValueError, AttributeError):
            actual = 0.0
        try:
            hourly = float(self.hourly_var.get())
        except (ValueError, AttributeError):
            hourly = 0.0

        info = em.get_employee_salary(name)
        old_hourly = info.get("hourly_wage", 0.0)
        info["official_salary"] = official
        info["actual_salary"] = actual
        info["hourly_wage"] = hourly
        em.set_employee_salary(name, info)

        self._record_salary_to_excel(name, "파트타이머", official, actual)
        # 파트타이머 공식급여는 선지급금으로 추가 (나중에 주급 지급 시 차감)
        today_str = date.today().strftime("%Y-%m-%d")
        cur_ym = today_str[:7]
        em.delete_prepay_entries_by_method(name, "공식급여", cur_ym)
        if official > 0:
            em.add_prepay(name, official, "공식급여", today_str)
        # 시급이 변경됐을 때만 Excel에 기록 (그래프용 이력)
        if hourly > 0 and abs(hourly - old_hourly) > 0.01:
            today = date.today()
            em.save_salary(today.year, today.month, {
                "date": today.strftime("%Y-%m-%d"), "name": name,
                "position": "파트타이머", "category": "시급", "amount_ft": hourly,
            })
        self._refresh_list()
        self._build_detail(name)
        self._show_hdr_msg(self.t("급여 저장됨"), "green")

    def _record_salary_to_excel(self, name: str, position: str, official: float, actual: float):
        today = date.today()
        y, m = today.year, today.month
        date_str = today.strftime("%Y-%m-%d")
        em.delete_salary_records_by_category(y, m, name, "공식급여")
        em.delete_salary_records_by_category(y, m, name, "실질지급")
        if official > 0:
            em.save_salary(y, m, {"date": date_str, "name": name, "position": position,
                                   "category": "공식급여", "amount_ft": official})
        if actual > 0:
            em.save_salary(y, m, {"date": date_str, "name": name, "position": position,
                                   "category": "실질지급", "amount_ft": actual})

    def _apply_official_salary_to_prepay(self, name: str, official: float):
        """공식급여 지급 시 선지급 잔액에서 차감 (이달 기존 항목 교체)."""
        today_str = date.today().strftime("%Y-%m-%d")
        cur_ym = today_str[:7]
        em.delete_prepay_entries_by_method(name, "공식급여", cur_ym)
        if official > 0:
            balance = em.get_prepay_balance(name)
            deduct = min(official, balance)
            if deduct > 0:
                em.add_prepay(name, -deduct, "공식급여", today_str)

    # ── 정산 ─────────────────────────────────────────────────────────

    def _reset_prepay(self, name: str):
        balance = em.get_prepay_balance(name)
        if balance == 0:
            return
        data = em.load_prepay()
        if name not in data:
            data[name] = {"balance": 0.0, "history": []}
        data[name]["history"].append({
            "date": date.today().strftime("%Y-%m-%d"), "method": "수동 초기화", "amount": -balance,
        })
        data[name]["balance"] = 0.0
        em.save_prepay(data)
        self._build_detail(name)
        self._refresh_list()

    def _settle_staff(self, name: str):
        try:
            actual = float(self.actual_var.get())
        except (ValueError, AttributeError):
            actual = 0.0
        balance = em.get_prepay_balance(name)
        net_pay = round(actual - balance, 2)
        today = date.today().strftime("%Y-%m-%d")
        y, m, _ = (int(x) for x in today.split("-"))
        em.save_salary(y, m, {"date": today, "name": name, "position": "스탭",
                               "category": "월급정산", "amount_ft": net_pay})
        em.reset_prepay(name)
        done_msg = f"Settlement done! Pay: {net_pay:,.0f} ft" if self.lang == "en" else f"정산 완료! 지급액: {net_pay:,.0f} ft"
        self.salary_msg.configure(text=done_msg, text_color="green")
        self.after(2000, lambda: self._build_detail(name))

    def _settle_part(self, name: str):
        date_str = self.part_date_row.get_date_str()
        if not date_str:
            self.salary_msg.configure(text=self.t("날짜를 입력하세요"), text_color="red")
            return
        try:
            weekly = float(self.weekly_var.get())
        except (ValueError, AttributeError):
            weekly = 0.0
        if weekly <= 0:
            weekly_err = "Enter weekly wage" if self.lang == "en" else "주급을 입력하세요"
            self.salary_msg.configure(text=weekly_err, text_color="red")
            return
        try:
            tax = float(self.part_tax_var.get())
        except (ValueError, AttributeError):
            tax = 0.0

        info = em.get_employee_salary(name)
        info["weekly_wage"] = weekly
        info["part_tax"] = tax
        em.set_employee_salary(name, info)

        y, m, _ = (int(x) for x in date_str.split("-"))
        em.save_salary(y, m, {"date": date_str, "name": name, "position": "파트타이머",
                               "category": "주급", "amount_ft": weekly})

        balance = em.get_prepay_balance(name)
        prepay_used = min(weekly, balance)
        if prepay_used > 0:
            data = em.load_prepay()
            if name not in data:
                data[name] = {"balance": 0.0, "history": []}
            data[name]["history"].append({"date": date_str, "method": "주급차감", "amount": -prepay_used})
            data[name]["balance"] = round(balance - prepay_used, 2)
            em.save_prepay(data)

        cash_out = round(weekly - balance, 2)
        if self.lang == "en":
            msg = f"Done! Extra {cash_out:,.0f} ft" if cash_out > 0 else \
                  (f"Done! Pay {weekly:,.0f} ft" if balance == 0 else f"Done! Prepay left {-cash_out:,.0f} ft")
        else:
            msg = f"완료! 추가지급 {cash_out:,.0f} ft" if cash_out > 0 else \
                  (f"완료! 지급 {weekly:,.0f} ft" if balance == 0 else f"완료! 남은선지급 {-cash_out:,.0f} ft")
        self.salary_msg.configure(text=msg, text_color="green")
        self.after(2000, lambda: self._build_detail(name))

    # ── CRUD ─────────────────────────────────────────────────────────

    def _add_employee(self):
        AddEmployeeDialog(self, on_add=self._on_employee_changed, lang=self.lang)

    def _edit_employee(self, emp: dict):
        EditEmployeeDialog(self, emp, on_save=self._on_employee_changed, lang=self.lang)

    def _delete_employee(self):
        if not self._selected_name:
            self._show_hdr_msg(self.t("삭제할 직원을 클릭하여 선택하세요"), "orange")
            return
        name = self._selected_name

        dlg = ctk.CTkToplevel(self)
        dlg.title(self.t("직원 삭제 확인"))
        dlg.geometry("320x170")
        dlg.resizable(False, False)
        dlg.grab_set()
        confirm_txt = f"Delete '{name}'?" if self.lang == "en" else f"'{name}'를 삭제하시겠습니까?"
        ctk.CTkLabel(dlg, text=confirm_txt,
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(24, 6))
        ctk.CTkLabel(dlg, text=self.t("삭제된 직원 정보는 복구할 수 없습니다."),
                     font=ctk.CTkFont(size=12), text_color="gray").pack()
        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(pady=20)
        ctk.CTkButton(btn_row, text=self.t("삭제"), width=90, height=36,
                      fg_color="#e53e3e", hover_color="#c53030",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=lambda: self._confirm_delete(name, dlg)).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text=self.t("취소"), width=80, height=36,
                      fg_color=("gray70", "gray40"), font=ctk.CTkFont(size=13),
                      command=dlg.destroy).pack(side="left", padx=8)

    def _confirm_delete(self, name: str, dlg):
        dlg.destroy()
        em.remove_employee(name)
        self._selected_name = None
        self._show_list_mode()
        self._refresh_list()
        del_msg = f"{name} deleted" if self.lang == "en" else f"{name} 삭제됨"
        self._show_hdr_msg(del_msg, "green")

    def _on_employee_changed(self):
        self._refresh_list()
        if self._selected_name:
            self._build_detail(self._selected_name)

    def _show_hdr_msg(self, text: str, color: str):
        self.hdr_msg.configure(text=text, text_color=color)
        self.after(3000, lambda: self.hdr_msg.configure(text=""))

    def _open_transfer_dialog(self, from_name: str):
        employees = [e["name"] for e in em.load_employees()]
        TransferDialog(self, employees, on_confirm=self._on_transfer_done, from_name=from_name, lang=self.lang)

    def _on_transfer_done(self):
        self._refresh_list()
        if self._selected_name:
            self._build_detail(self._selected_name)

    # ── 내역 ─────────────────────────────────────────────────────────

    def _build_pay_history(self, parent, name: str):
        all_prepay = [dict(h) for h in em.get_prepay_history(name)]
        deduction_dates = {h["date"] for h in all_prepay if h.get("method") == "주급차감"}

        history: list[dict] = []
        for h in all_prepay:
            entry = dict(h)
            entry["_source"] = "prepay"
            history.append(entry)

        today = date.today()
        seen: set = set()
        for offset in range(12):
            total_m = today.month - 1 - offset
            y = today.year + total_m // 12
            m = total_m % 12 + 1
            for rec in em.load_salaries(y, m):
                if rec.get("name") != name:
                    continue
                cat = rec.get("category", "")
                if cat not in SALARY_CATS:
                    continue
                key = (rec["date"], cat, rec.get("amount_ft", 0))
                if key in seen:
                    continue
                seen.add(key)
                if self.role == "admin" and cat == "주급" and rec["date"] in deduction_dates:
                    continue
                history.append({
                    "date": rec["date"],
                    "method": cat,
                    "amount": rec.get("amount_ft", 0),
                    "_source": "excel",
                })

        history.sort(key=lambda x: x.get("date", ""), reverse=True)
        if self.role != "admin":
            history = [h for h in history
                       if h.get("_source") != "prepay"
                       and h.get("method") in ("공식급여", "주급")]

        title_row = ctk.CTkFrame(parent, fg_color="transparent")
        title_row.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(title_row, text=self.t("내역"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        if self.role == "admin":
            self._hist_delete_btn = ctk.CTkButton(
                title_row, text=self.t("선택 삭제"), width=70, height=26,
                fg_color="#e53e3e", hover_color="#c53030",
                state="disabled", font=ctk.CTkFont(size=11),
                command=lambda: self._do_hist_delete(name))
            self._hist_delete_btn.pack(side="right")

        self._hist_selected_h = None
        self._hist_row_refs = []

        cur_ym = f"{today.year}-{today.month:02d}"
        if self.role == "admin":
            month_wage = sum(abs(h.get("amount", 0)) for h in history
                             if h.get("method") == "주급차감" and h.get("date", "")[:7] == cur_ym)
            wage_label_text = f"{self.t('이번 달 주급')}: {month_wage:,.0f} ft"
        else:
            month_total = sum(h.get("amount", 0) for h in history if h.get("date", "")[:7] == cur_ym)
            wage_label_text = f"이번 달 수령: {month_total:,.0f} ft"
        balance = em.get_prepay_balance(name)

        smry = ctk.CTkFrame(parent, fg_color=("gray92", "gray18"), corner_radius=6)
        smry.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(smry, text=wage_label_text,
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#1a56db").pack(side="left", padx=12, pady=6)
        if self.role == "admin":
            bal_lbl_txt = f"{self.t('선지급 잔액:')} {balance:,.0f} ft"
            ctk.CTkLabel(smry, text=bal_lbl_txt,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#1a56db" if balance > 0 else "gray").pack(side="right", padx=12, pady=6)

        hrow = ctk.CTkFrame(parent, fg_color="#1a56db", corner_radius=6)
        hrow.pack(fill="x", padx=16, pady=(0, 2))
        if self.role == "admin":
            hist_cols = [(self.t("날짜"), 90), (self.t("구분"), 130),
                         ("선지급/공식(ft)", 115), ("주급(ft)", 100)]
        else:
            hist_cols = [(self.t("날짜"), 88), (self.t("구분"), 130), (self.t("금액(ft)"), 96)]
        for h_text, w in hist_cols:
            ctk.CTkLabel(hrow, text=h_text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="white", width=w, height=24).pack(side="left", padx=4, pady=1)
        if self.role == "admin":
            ctk.CTkLabel(hrow, text=self.t("수정"), font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="white", width=44).pack(side="left", padx=2)

        scroll = ctk.CTkScrollableFrame(parent, height=200, fg_color="transparent")
        scroll.pack(fill="x", padx=16, pady=(0, 12))

        if not history:
            ctk.CTkLabel(scroll, text=self.t("내역이 없습니다"), text_color="gray",
                         font=ctk.CTkFont(size=13)).pack(pady=10)
            return

        for i, h in enumerate(history[:60]):
            normal_bg = ("#e8f0fe", "#272736") if i % 2 == 0 else ("white", "#1e1e2e")
            method = h.get("method", "")
            amount = h.get("amount", 0)
            src = h.get("_source", "")

            drow = ctk.CTkFrame(scroll, fg_color=normal_bg, corner_radius=4)
            drow.pack(fill="x", pady=1)
            self._hist_row_refs.append((h, drow, normal_bg))

            if self.role == "admin":
                # ── 두 열 분리: 선지급/공식(파랑) | 주급(빨강) ──────────────
                is_wage = (
                    (src == "prepay" and method == "주급차감") or
                    (src == "excel" and method in ("주급", "주급정산", "주급(직원간)"))
                )
                display_method = self.t(method)
                if is_wage:
                    blue_text, red_text = "", f"{abs(amount):,.0f}"
                else:
                    sign = "+" if amount > 0 else ""
                    blue_text = f"{sign}{amount:,.0f}"
                    red_text = ""

                ctk.CTkLabel(drow, text=h.get("date", ""), width=90, height=22,
                             font=ctk.CTkFont(size=12)).pack(side="left", padx=4, pady=0)
                ctk.CTkLabel(drow, text=display_method, width=130, height=22,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color="#1a56db" if not is_wage else "#e53e3e"
                             ).pack(side="left", padx=4, pady=0)
                ctk.CTkLabel(drow, text=blue_text, width=115, height=22,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color="#1a56db").pack(side="left", padx=4, pady=0)
                ctk.CTkLabel(drow, text=red_text, width=100, height=22,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color="#e53e3e").pack(side="left", padx=4, pady=0)
            else:
                # ── 직원 뷰: 단일 금액 열 ──────────────────────────────────
                if method == "주급":
                    try:
                        month_num = int(h.get("date", "")[5:7])
                    except (ValueError, IndexError):
                        month_num = 0
                    display_method = f"{month_num}월 주급"
                    color = "#38a169"
                    display_amount = f"{amount:,.0f} ft"
                elif method == "공식급여":
                    display_method = self.t("공식급여")
                    color = "#1a56db"
                    display_amount = f"{amount:,.0f} ft"
                else:
                    display_method = self.t(method)
                    color = "#1a56db"
                    display_amount = f"{amount:,.0f} ft"

                ctk.CTkLabel(drow, text=h.get("date", ""), width=88, height=22,
                             font=ctk.CTkFont(size=12)).pack(side="left", padx=4, pady=0)
                ctk.CTkLabel(drow, text=display_method, width=130, height=22,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=color).pack(side="left", padx=4, pady=0)
                ctk.CTkLabel(drow, text=display_amount, width=96, height=22,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=color).pack(side="left", padx=4, pady=0)

                if method == "주급" and src == "excel":
                    ctk.CTkButton(drow, text=self.t("수정"), width=40, height=22,
                                  font=ctk.CTkFont(size=10),
                                  command=lambda hh=h: self._edit_wage_entry(hh, name)
                                  ).pack(side="left", padx=(2, 0))
                    ctk.CTkButton(drow, text="✕", width=28, height=22,
                                  font=ctk.CTkFont(size=10),
                                  fg_color="#e53e3e", hover_color="#c53030",
                                  command=lambda hh=h: self._inline_delete_wage(hh, name)
                                  ).pack(side="left", padx=2)

            is_editable = self.role == "admin" and (
                (method == "주급차감") or (src == "excel" and method in ("주급", "주급정산"))
            )
            if is_editable:
                ctk.CTkButton(drow, text=self.t("수정"), width=44, height=22, font=ctk.CTkFont(size=10),
                              command=lambda hh=h: self._edit_wage_entry(hh, name)).pack(side="left", padx=2)

            def on_row_click(event, hh=h, frame=drow, nbg=normal_bg):
                self._hist_selected_h = hh
                for _, f, bg in self._hist_row_refs:
                    f.configure(fg_color=bg)
                frame.configure(fg_color=("#c7d8f5", "#2a3a5c"))
                if self.role == "admin":
                    hh_method = hh.get("method", "")
                    hh_src = hh.get("_source", "")
                    can_del = (hh_method in ("주급차감", "수동 초기화", "공식급여", "실질지급")
                               or (hh_src == "excel" and hh_method in ("주급", "주급정산")))
                    self._hist_delete_btn.configure(state="normal" if can_del else "disabled")

            drow.bind("<Button-1>", on_row_click)
            for child in drow.winfo_children():
                child.bind("<Button-1>", on_row_click)

    def _do_hist_delete(self, name: str):
        h = self._hist_selected_h
        if not h:
            return
        method = h.get("method", "")
        src = h.get("_source", "")

        if method == "주급차감":
            old_date = h["date"]
            old_abs = abs(h["amount"])
            old_y, old_m = int(old_date[:4]), int(old_date[5:7])
            em.delete_salary_record(old_y, old_m, name, old_date, "주급", old_abs)
            em.delete_salary_record(old_y, old_m, name, old_date, "주급정산", old_abs)
            data = em.load_prepay()
            if name in data:
                for i, entry in enumerate(data[name]["history"]):
                    if (entry.get("date") == old_date and entry.get("method") == "주급차감"
                            and abs(entry.get("amount", 0) - h["amount"]) < 0.01):
                        data[name]["balance"] = round(data[name]["balance"] - entry["amount"], 2)
                        data[name]["history"].pop(i)
                        break
                em.save_prepay(data)

        elif method == "수동 초기화":
            self._cancel_prepay_entry(h, name)
            return

        elif method in ("공식급여", "실질지급"):
            old_date = h["date"]
            old_y, old_m = int(old_date[:4]), int(old_date[5:7])
            em.delete_salary_record(old_y, old_m, name, old_date, method, h["amount"])

        elif src == "excel" and method in ("주급", "주급정산"):
            old_date = h["date"]
            old_y, old_m = int(old_date[:4]), int(old_date[5:7])
            em.delete_salary_record(old_y, old_m, name, old_date, method, h["amount"])
            self._reverse_prepay_deduction(name, old_date)

        self._build_detail(name)

    def _edit_wage_entry(self, h: dict, name: str):
        method = h.get("method", "")
        src = h.get("_source", "")
        is_prepay_wage = method == "주급차감"

        display_h = dict(h)
        if is_prepay_wage:
            display_h["amount"] = abs(h["amount"])

        def on_save(new_date_str: str, new_amount: float):
            old_date = h["date"]
            old_y, old_m = int(old_date[:4]), int(old_date[5:7])

            if is_prepay_wage:
                old_abs = abs(h["amount"])
                em.delete_salary_record(old_y, old_m, name, old_date, "주급", old_abs)
                em.delete_salary_record(old_y, old_m, name, old_date, "주급정산", old_abs)
                data = em.load_prepay()
                if name in data:
                    for i, entry in enumerate(data[name]["history"]):
                        if (entry.get("date") == old_date and entry.get("method") == "주급차감"
                                and abs(entry.get("amount", 0) - h["amount"]) < 0.01):
                            data[name]["balance"] = round(data[name]["balance"] - entry["amount"], 2)
                            data[name]["history"].pop(i)
                            break
                    em.save_prepay(data)
            else:
                em.delete_salary_record(old_y, old_m, name, old_date, method, h["amount"])
                self._reverse_prepay_deduction(name, old_date)

            new_y, new_m = int(new_date_str[:4]), int(new_date_str[5:7])
            em.save_salary(new_y, new_m, {"date": new_date_str, "name": name,
                                           "position": "파트타이머", "category": "주급",
                                           "amount_ft": new_amount})

            balance = em.get_prepay_balance(name)
            prepay_used = min(new_amount, balance)
            if prepay_used > 0:
                data2 = em.load_prepay()
                if name not in data2:
                    data2[name] = {"balance": 0.0, "history": []}
                data2[name]["history"].append({"date": new_date_str, "method": "주급차감",
                                               "amount": -prepay_used})
                data2[name]["balance"] = round(data2[name]["balance"] - prepay_used, 2)
                em.save_prepay(data2)

            self._build_detail(name)

        EditWageDialog(self, display_h, name, on_save, lang=self.lang)

    def _inline_delete_wage(self, h: dict, name: str):
        """직원 뷰에서 주급 항목 직접 삭제."""
        old_date = h["date"]
        old_y, old_m = int(old_date[:4]), int(old_date[5:7])
        em.delete_salary_record(old_y, old_m, name, old_date, "주급", h["amount"])
        self._reverse_prepay_deduction(name, old_date)
        self._build_detail(name)

    def _reverse_prepay_deduction(self, name: str, date_str: str):
        data = em.load_prepay()
        if name not in data:
            return
        for i, entry in enumerate(data[name]["history"]):
            if entry.get("date") == date_str and entry.get("method") == "주급차감":
                data[name]["balance"] = round(data[name]["balance"] - entry["amount"], 2)
                data[name]["history"].pop(i)
                em.save_prepay(data)
                return

    def _cancel_prepay_entry(self, h: dict, name: str):
        data = em.load_prepay()
        if name not in data:
            return
        for i, entry in enumerate(data[name]["history"]):
            if (entry.get("date") == h.get("date") and
                    entry.get("method") == h.get("method") and
                    abs(entry.get("amount", 0) - h.get("amount", 0)) < 0.01):
                data[name]["balance"] = round(data[name]["balance"] - entry["amount"], 2)
                data[name]["history"].pop(i)
                em.save_prepay(data)
                break
        self._build_detail(name)

    def refresh(self):
        if self._view_mode == "list":
            self._refresh_list()
        else:
            self._refresh_left_panel()
            if self._selected_name:
                self._build_detail(self._selected_name)
