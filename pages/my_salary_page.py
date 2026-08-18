import customtkinter as ctk
from utils import config_manager as cm
from utils import excel_manager as em


class MySalaryPage(ctk.CTkFrame):
    """직원 전용: 본인 급여 열람 + 파트타이머 세금 기입"""

    def __init__(self, master, role: str):
        super().__init__(master, fg_color="transparent")
        self.role = role
        self._build_ui()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(hdr, text="내 급여", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        employees = em.load_employees()
        if not employees:
            ctk.CTkLabel(scroll, text="등록된 직원 정보가 없습니다.\n관리자에게 문의하세요.",
                         font=ctk.CTkFont(size=15), text_color="gray").pack(pady=60)
            return

        # Employee selector
        sel_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        sel_frame.pack(fill="x", pady=(8, 16))
        ctk.CTkLabel(sel_frame, text="직원 선택", font=ctk.CTkFont(size=14), width=90).pack(side="left")
        names = [e["name"] for e in employees]
        self.emp_var = ctk.StringVar(value=names[0])
        cb = ctk.CTkComboBox(sel_frame, values=names, variable=self.emp_var,
                             width=180, font=ctk.CTkFont(size=14),
                             command=self._on_emp_change)
        cb.pack(side="left", padx=8)

        self.content = ctk.CTkFrame(scroll, fg_color="transparent")
        self.content.pack(fill="x")

        self._on_emp_change(names[0])

    def _on_emp_change(self, name: str):
        for w in self.content.winfo_children():
            w.destroy()

        employees = em.load_employees()
        emp = next((e for e in employees if e["name"] == name), None)
        if not emp:
            return

        if emp["position"] == "스탭":
            self._build_staff_view(name)
        else:
            self._build_part_view(name)

    def _build_staff_view(self, name: str):
        info = em.get_employee_salary(name)
        taxes = cm.get_staff_taxes()

        card = ctk.CTkFrame(self.content, corner_radius=12)
        card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(card, text="공식 급여 정보",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(16, 10))

        official = info.get("official_salary", 0)
        self._info_row(card, "공식 지급액", f"{official:,.0f} ft")

        # Tax breakdown
        tax_frame = ctk.CTkFrame(card, fg_color=("#f0f4f8", "#1e2030"), corner_radius=8)
        tax_frame.pack(fill="x", padx=16, pady=(4, 8))
        ctk.CTkLabel(tax_frame, text="세금 내역",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))

        total_tax = 0.0
        for t in taxes:
            tax_amt = round(official * t["rate"] / 100, 2)
            total_tax += tax_amt
            trow = ctk.CTkFrame(tax_frame, fg_color="transparent")
            trow.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(trow, text=f"{t['name']} ({t['rate']}%)",
                         font=ctk.CTkFont(size=13), width=200).pack(side="left")
            ctk.CTkLabel(trow, text=f"{tax_amt:,.0f} ft",
                         font=ctk.CTkFont(size=13), text_color="#e53e3e").pack(side="left")

        net = round(official - total_tax, 2)
        net_row = ctk.CTkFrame(card, fg_color="transparent")
        net_row.pack(fill="x", padx=16, pady=(4, 16))
        ctk.CTkLabel(net_row, text="세후 수령액",
                     font=ctk.CTkFont(size=15, weight="bold"), width=160).pack(side="left")
        ctk.CTkLabel(net_row, text=f"{net:,.0f} ft",
                     font=ctk.CTkFont(size=16, weight="bold"), text_color="#1a56db").pack(side="left")

    def _build_part_view(self, name: str):
        info = em.get_employee_salary(name)

        # Weekly wage view
        card = ctk.CTkFrame(self.content, corner_radius=12)
        card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(card, text="파트타이머 급여",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(16, 10))

        weekly = info.get("weekly_wage", 0)
        self._info_row(card, "주급", f"{weekly:,.0f} ft")

        # Tax input (part-timers fill this in themselves)
        tax_card = ctk.CTkFrame(self.content, corner_radius=12)
        tax_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(tax_card, text="세금 기입",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(16, 10))
        ctk.CTkLabel(tax_card, text="파트타이머는 본인이 세금을 직접 기입합니다.",
                     font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w", padx=20, pady=(0, 8))

        self.part_tax_var = ctk.StringVar(value=str(info.get("part_tax", 0)))
        row = ctk.CTkFrame(tax_card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(row, text="세금 (ft)", font=ctk.CTkFont(size=14), width=120).pack(side="left")
        ctk.CTkEntry(row, textvariable=self.part_tax_var, width=160,
                     font=ctk.CTkFont(size=14)).pack(side="left")

        btn_row = ctk.CTkFrame(tax_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(btn_row, text="세금 저장", width=110, height=38,
                      font=ctk.CTkFont(size=14),
                      command=lambda: self._save_tax(name)).pack(side="left")
        self.tax_msg = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=13))
        self.tax_msg.pack(side="left", padx=12)

    def _save_tax(self, name: str):
        try:
            tax = float(self.part_tax_var.get())
        except ValueError:
            self.tax_msg.configure(text="올바른 금액을 입력하세요", text_color="red")
            return
        info = em.get_employee_salary(name)
        info["part_tax"] = tax
        em.set_employee_salary(name, info)
        self.tax_msg.configure(text="저장되었습니다", text_color="green")
        self.after(3000, lambda: self.tax_msg.configure(text=""))

    def _info_row(self, parent, label: str, value: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=14),
                     width=160, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=14),
                     text_color="#1a56db").pack(side="left")

    def refresh(self):
        if hasattr(self, "emp_var"):
            self._on_emp_change(self.emp_var.get())
