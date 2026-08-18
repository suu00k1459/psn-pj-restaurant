import customtkinter as ctk
from utils import config_manager as cm
from utils import excel_manager as em
from utils.i18n import t as _t

VENDOR_CATEGORIES = ["식재료 및 판관비", "시설 및 운영 관리비"]


class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, role: str):
        super().__init__(master, fg_color="transparent")
        self.role = role
        self.lang = "en" if role != "admin" else "ko"
        self.t = lambda s: _t(s, self.lang)
        self._delete_mode = False
        self._delete_pending: set[str] = set()   # 삭제 표시됐지만 아직 저장 안된 것
        self._archived_expanded = False
        self._vendor_row_vars: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(hdr, text=self.t("설정"), font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        if self.role == "admin":
            tabs = ["환율 설정", "세금 설정", "업체 관리", "비밀번호 변경"]
        else:
            tabs = [self.t("세금 설정"), self.t("업체 관리")]
        for tab in tabs:
            self.tabview.add(tab)
        self._tab_tax = self.t("세금 설정")
        self._tab_vendor = self.t("업체 관리")

        if self.role == "admin":
            self._build_exchange_tab()
        self._build_tax_tab()
        self._build_vendor_tab()
        if self.role == "admin":
            self._build_password_tab()

    # ── 환율 설정 ─────────────────────────────────────────────────────

    def _build_exchange_tab(self):
        tab = self.tabview.tab("환율 설정")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="각 통화를 1ft으로 환산하는 비율을 설정합니다.",
                     font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w", pady=(12, 16))

        ctk.CTkLabel(scroll, text="예) 원 환율 = 4  →  160,000원 입력 시  40,000ft 환산",
                     font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w", pady=(0, 20))

        rates = cm.get_exchange_rates()
        self.rate_vars = {}
        labels = {"KRW": "원 (KRW) / ft", "USD": "달러 (USD) / ft", "EUR": "유로 (EUR) / ft"}

        card = ctk.CTkFrame(scroll, corner_radius=12)
        card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(card, text="환율 설정",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(16, 12))

        for key, label in labels.items():
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=6)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=14), width=180).pack(side="left")
            var = ctk.StringVar(value=str(rates.get(key, 1.0)))
            ctk.CTkEntry(row, textvariable=var, width=120, font=ctk.CTkFont(size=14)).pack(side="left", padx=8)
            ctk.CTkLabel(row, text="원 = 1 ft 기준", font=ctk.CTkFont(size=12), text_color="gray").pack(side="left")
            self.rate_vars[key] = var

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(8, 16))
        ctk.CTkButton(btn_row, text="저장", width=100, height=38,
                      font=ctk.CTkFont(size=14),
                      command=self._save_rates).pack(side="left")
        self.rate_msg = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=13))
        self.rate_msg.pack(side="left", padx=12)

    def _save_rates(self):
        try:
            rates = {k: float(v.get()) for k, v in self.rate_vars.items()}
        except ValueError:
            self.rate_msg.configure(text="숫자를 올바르게 입력하세요", text_color="red")
            return
        cm.set_exchange_rates(rates)
        self.rate_msg.configure(text="환율이 저장되었습니다", text_color="green")
        self.after(3000, lambda: self.rate_msg.configure(text=""))

    # ── 세금 설정 ─────────────────────────────────────────────────────

    def _build_tax_tab(self):
        tab = self.tabview.tab(self._tab_tax)
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text=self.t("스탭 월급 세금 항목과 세율(%)을 설정합니다."),
                     font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w", pady=(12, 20))

        taxes = cm.get_staff_taxes()
        self.tax_rows: list[dict] = []

        card = ctk.CTkFrame(scroll, corner_radius=12)
        card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(card, text=self.t("스탭 급여 세금 항목"),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(16, 8))

        # Header
        hrow = ctk.CTkFrame(card, fg_color="#1a56db", corner_radius=6)
        hrow.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(hrow, text=self.t("항목명"), font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="white", width=200).pack(side="left", padx=8, pady=8)
        ctk.CTkLabel(hrow, text=self.t("세율 (%)"), font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="white", width=120).pack(side="left", padx=8)

        self.tax_container = ctk.CTkFrame(card, fg_color="transparent")
        self.tax_container.pack(fill="x", padx=16)

        for t in taxes:
            self._add_tax_row(t["name"], t["rate"])

        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.pack(fill="x", padx=16, pady=(4, 0))
        ctk.CTkButton(add_row, text=self.t("+ 항목 추가"), width=110, height=32,
                      font=ctk.CTkFont(size=13),
                      command=lambda: self._add_tax_row()).pack(side="left")

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(8, 16))
        ctk.CTkButton(btn_row, text=self.t("저장"), width=100, height=38,
                      font=ctk.CTkFont(size=14),
                      command=self._save_taxes).pack(side="left")
        self.tax_msg = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=13))
        self.tax_msg.pack(side="left", padx=12)

    def _add_tax_row(self, name: str = "", rate: float = 0.0):
        row_frame = ctk.CTkFrame(self.tax_container, fg_color="transparent")
        row_frame.pack(fill="x", pady=3)
        name_var = ctk.StringVar(value=name)
        rate_var = ctk.StringVar(value=str(rate))
        entry = {"name": name_var, "rate": rate_var, "frame": row_frame}
        ctk.CTkEntry(row_frame, textvariable=name_var, width=200,
                     font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 8))
        ctk.CTkEntry(row_frame, textvariable=rate_var, width=120,
                     font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 8))

        def _remove(e=entry, f=row_frame):
            if e in self.tax_rows:
                self.tax_rows.remove(e)
            f.destroy()

        ctk.CTkButton(row_frame, text="×", width=32, height=32,
                      fg_color="#e53e3e", hover_color="#c53030",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=_remove).pack(side="left")
        self.tax_rows.append(entry)

    def _save_taxes(self):
        taxes = []
        for row in self.tax_rows:
            name = row["name"].get().strip()
            if not name:
                continue
            try:
                rate = float(row["rate"].get())
            except ValueError:
                self.tax_msg.configure(text=self.t("세율에 숫자를 입력하세요"), text_color="red")
                return
            taxes.append({"name": name, "rate": rate})
        cm.set_staff_taxes(taxes)
        self.tax_msg.configure(text=self.t("세금 항목이 저장되었습니다"), text_color="green")
        self.after(3000, lambda: self.tax_msg.configure(text=""))

    # ── 업체 관리 ─────────────────────────────────────────────────────

    def _build_vendor_tab(self):
        tab = self.tabview.tab(self._tab_vendor)
        outer = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        outer.pack(fill="both", expand=True)

        card = ctk.CTkFrame(outer, corner_radius=12)
        card.pack(fill="x", pady=(12, 0))

        # 헤더 (제목 + 버튼들)
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(hdr, text=self.t("업체 목록"),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        self.vendor_msg = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont(size=13))
        self.vendor_msg.pack(side="left", padx=12)

        # 우측 버튼 (오른쪽부터: 추가, 저장, 삭제)
        ctk.CTkButton(hdr, text=self.t("+ 추가"), width=76, height=34,
                      font=ctk.CTkFont(size=13),
                      command=self._add_vendor_row).pack(side="right", padx=(4, 0))
        ctk.CTkButton(hdr, text=self.t("저장"), width=60, height=34,
                      fg_color="#1a56db", hover_color="#1440a0",
                      font=ctk.CTkFont(size=13),
                      command=self._save_all_vendors).pack(side="right", padx=4)
        self._delete_btn = ctk.CTkButton(
            hdr, text=self.t("삭제"), width=60, height=34,
            fg_color=("gray75", "gray35"), hover_color="#e53e3e",
            font=ctk.CTkFont(size=13),
            command=self._toggle_delete_mode)
        self._delete_btn.pack(side="right", padx=4)

        # 컬럼 헤더
        hrow = ctk.CTkFrame(card, fg_color="#1a56db", corner_radius=6)
        hrow.pack(fill="x", padx=16, pady=(0, 2))
        for text, w in [(self.t("업체명"), 160), (self.t("비고"), 200), (self.t("분류"), 130)]:
            ctk.CTkLabel(hrow, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="white", width=w).pack(side="left", padx=8, pady=6)

        # 업체 목록
        self.vendor_scroll = ctk.CTkScrollableFrame(card, height=300, fg_color="transparent")
        self.vendor_scroll.pack(fill="x", padx=16, pady=(0, 4))

        # 삭제된 업체 섹션 (접힌 형태)
        self._archived_card = ctk.CTkFrame(card, fg_color="transparent")
        self._archived_card.pack(fill="x", padx=16, pady=(0, 16))

        self._refresh_vendors()

    def _refresh_vendors(self):
        for w in self.vendor_scroll.winfo_children():
            w.destroy()
        self._vendor_row_vars = []

        vendors = cm.get_vendors_full()

        if not vendors:
            ctk.CTkLabel(self.vendor_scroll,
                         text=self.t("업체가 없습니다. [+ 추가] 버튼을 눌러 등록하세요."),
                         text_color="gray", font=ctk.CTkFont(size=13)).pack(pady=16)
        else:
            for i, v in enumerate(vendors):
                is_pending = v["name"] in self._delete_pending
                bg_normal = ("#e8f0fe", "#f8faff") if i % 2 == 0 else ("white", "#1e1e2e")
                bg_del = ("#fde8e8", "#3d1a1a")
                row = ctk.CTkFrame(self.vendor_scroll,
                                   fg_color=bg_del if is_pending else bg_normal,
                                   corner_radius=4)
                row.pack(fill="x", pady=1)

                name_color = "gray50" if is_pending else None
                name_kw = {"text_color": name_color} if name_color else {}
                ctk.CTkLabel(row, text=v["name"], font=ctk.CTkFont(size=13),
                             width=160, anchor="w", **name_kw).pack(side="left", padx=10, pady=5)

                note_var = ctk.StringVar(value=v.get("note", ""))
                ctk.CTkEntry(row, textvariable=note_var, width=200, font=ctk.CTkFont(size=12),
                             placeholder_text="비고",
                             state="disabled" if is_pending else "normal"
                             ).pack(side="left", padx=(0, 4), pady=4)

                cur_cat = v.get("category", VENDOR_CATEGORIES[0])
                if cur_cat not in VENDOR_CATEGORIES:
                    cur_cat = VENDOR_CATEGORIES[0]
                cat_var = ctk.StringVar(value=cur_cat)
                ctk.CTkComboBox(row, values=VENDOR_CATEGORIES, variable=cat_var,
                                width=130, font=ctk.CTkFont(size=12),
                                state="disabled" if is_pending else "normal"
                                ).pack(side="left", padx=(0, 6), pady=4)

                self._vendor_row_vars.append({
                    "name": v["name"], "note_var": note_var, "cat_var": cat_var,
                })

                if self._delete_mode:
                    if is_pending:
                        # 이미 삭제 표시됨 → ↩ 버튼으로 취소
                        def _make_unmark(name=v["name"]):
                            def unmark():
                                self._delete_pending.discard(name)
                                self._refresh_vendors()
                            return unmark
                        ctk.CTkButton(row, text="↩", width=32, height=28,
                                      fg_color="#dd6b20", hover_color="#c05621",
                                      font=ctk.CTkFont(size=13),
                                      command=_make_unmark()).pack(side="right", padx=4)
                    else:
                        # 삭제 표시 버튼 (−)
                        def _make_mark(name=v["name"]):
                            def mark():
                                self._delete_pending.add(name)
                                self._refresh_vendors()
                            return mark
                        ctk.CTkButton(row, text="−", width=32, height=28,
                                      fg_color="#e53e3e", hover_color="#c53030",
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      command=_make_mark()).pack(side="right", padx=4)

        self._build_archived_section()

    def _toggle_delete_mode(self):
        if not self._delete_mode:
            self._delete_mode = True
            self._delete_pending.clear()
            self._archived_expanded = True
            self._delete_btn.configure(text=self.t("삭제 완료"),
                                       fg_color="#e53e3e", hover_color="#c53030")
            self._refresh_vendors()
        else:
            if self._delete_pending:
                vendors = cm.get_vendors_full()
                deleted = cm.get_deleted_vendors()
                to_archive = [v for v in vendors if v["name"] in self._delete_pending]
                vendors = [v for v in vendors if v["name"] not in self._delete_pending]
                deleted.extend(to_archive)
                cm.set_vendors_full(vendors)
                cm.set_deleted_vendors(deleted)
                n = len(self._delete_pending)
                self.vendor_msg.configure(text=f"{n}개 삭제됨 (아래에서 복원 가능)", text_color="orange")
                self.after(2500, lambda: self.vendor_msg.configure(text=""))
            self._delete_mode = False
            self._delete_pending.clear()
            self._delete_btn.configure(text=self.t("삭제"),
                                       fg_color=("gray75", "gray35"), hover_color="#e53e3e")
            self._refresh_vendors()

    def _save_all_vendors(self):
        if not self._vendor_row_vars:
            return
        vendors = cm.get_vendors_full()
        name_to_idx = {v["name"]: i for i, v in enumerate(vendors)}
        for rd in self._vendor_row_vars:
            name = rd["name"]
            if name in name_to_idx:
                vendors[name_to_idx[name]]["note"] = rd["note_var"].get().strip()
                vendors[name_to_idx[name]]["category"] = rd["cat_var"].get()
        cm.set_vendors_full(vendors)

        # 저장된 분류 기준으로 모든 매입 엑셀 기록 강제 동기화
        category_map = {rd["name"]: rd["cat_var"].get() for rd in self._vendor_row_vars}
        try:
            total = em.sync_vendor_categories_in_expenses(category_map)
        except Exception as exc:
            self.vendor_msg.configure(text=f"오류: {exc}", text_color="red")
            return

        if total:
            self.vendor_msg.configure(
                text=f"저장 완료 — 매입내역 {total}건 분류 업데이트됨", text_color="green")
        else:
            self.vendor_msg.configure(text="저장되었습니다", text_color="green")
        self.after(2500, lambda: self.vendor_msg.configure(text=""))

    def _add_vendor_row(self):
        row_frame = ctk.CTkFrame(self.vendor_scroll,
                                  fg_color=("#dbeafe", "#1e2d40"), corner_radius=4)
        row_frame.pack(fill="x", pady=2)
        name_var = ctk.StringVar()
        note_var = ctk.StringVar()
        cat_var = ctk.StringVar(value="전체")

        ctk.CTkEntry(row_frame, textvariable=name_var, width=160,
                     font=ctk.CTkFont(size=13),
                     placeholder_text=self.t("업체명을 입력하세요")).pack(side="left", padx=(8, 4), pady=6)
        ctk.CTkEntry(row_frame, textvariable=note_var, width=200,
                     font=ctk.CTkFont(size=12),
                     placeholder_text="비고").pack(side="left", padx=(0, 4), pady=6)
        ctk.CTkComboBox(row_frame, values=VENDOR_CATEGORIES, variable=cat_var,
                        width=130, font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 6), pady=6)

        def save_new():
            name = name_var.get().strip()
            if not name:
                self.vendor_msg.configure(text=self.t("업체명을 입력하세요"), text_color="orange")
                self.after(2000, lambda: self.vendor_msg.configure(text=""))
                return
            all_v = cm.get_vendors_full()
            if any(v["name"] == name for v in all_v):
                self.vendor_msg.configure(text=self.t("이미 존재합니다"), text_color="orange")
                self.after(2000, lambda: self.vendor_msg.configure(text=""))
                return
            all_v.append({"name": name, "note": note_var.get().strip(), "category": cat_var.get()})
            cm.set_vendors_full(all_v)
            row_frame.destroy()
            self._refresh_vendors()
            self.vendor_msg.configure(text=self.t("추가되었습니다"), text_color="green")
            self.after(2000, lambda: self.vendor_msg.configure(text=""))

        ctk.CTkButton(row_frame, text=self.t("저장"), width=52, height=28,
                      font=ctk.CTkFont(size=11), command=save_new).pack(side="left", padx=(0, 4))
        ctk.CTkButton(row_frame, text=self.t("취소"), width=52, height=28,
                      fg_color="gray60", font=ctk.CTkFont(size=11),
                      command=row_frame.destroy).pack(side="left")

    def _build_archived_section(self):
        for w in self._archived_card.winfo_children():
            w.destroy()
        deleted = cm.get_deleted_vendors()
        arrow = "▼" if self._archived_expanded else "▶"
        arch_label = f"{arrow} {'Deleted Vendors' if self.lang == 'en' else '삭제된 업체'} ({len(deleted)})"
        ctk.CTkButton(
            self._archived_card,
            text=arch_label,
            anchor="w", fg_color="transparent",
            text_color=("gray50", "gray60"),
            hover_color=("gray90", "gray20"),
            font=ctk.CTkFont(size=13),
            command=self._toggle_archived,
        ).pack(fill="x", pady=(4, 0))

        if self._archived_expanded and deleted:
            arch = ctk.CTkFrame(self._archived_card,
                                fg_color=("gray93", "gray15"), corner_radius=6)
            arch.pack(fill="x", pady=(2, 4))
            ah = ctk.CTkFrame(arch, fg_color="#6b46c1", corner_radius=4)
            ah.pack(fill="x", padx=8, pady=(8, 2))
            for text, w in [(self.t("업체명"), 160), (self.t("비고"), 180), (self.t("분류"), 120)]:
                ctk.CTkLabel(ah, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                             text_color="white", width=w).pack(side="left", padx=4, pady=4)
            ctk.CTkLabel(ah, text=self.t("복원"), font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="white").pack(side="right", padx=8)

            for v in deleted:
                dr = ctk.CTkFrame(arch, fg_color=("gray88", "gray20"), corner_radius=3)
                dr.pack(fill="x", padx=8, pady=1)
                for text, w in [(v["name"], 160), (v.get("note", ""), 180), (v.get("category", ""), 120)]:
                    ctk.CTkLabel(dr, text=text, font=ctk.CTkFont(size=12), width=w, anchor="w",
                                 text_color="gray50").pack(side="left", padx=6, pady=4)
                ctk.CTkButton(dr, text=self.t("복원"), width=52, height=24,
                              fg_color="#6b46c1", hover_color="#553c9a",
                              font=ctk.CTkFont(size=11),
                              command=lambda name=v["name"]: self._restore_vendor(name)).pack(side="right", padx=6)

    def _toggle_archived(self):
        self._archived_expanded = not self._archived_expanded
        self._build_archived_section()

    def _restore_vendor(self, name: str):
        deleted = cm.get_deleted_vendors()
        vendors = cm.get_vendors_full()
        to_restore = next((v for v in deleted if v["name"] == name), None)
        if to_restore:
            cm.set_deleted_vendors([v for v in deleted if v["name"] != name])
            vendors.append(to_restore)
            cm.set_vendors_full(vendors)
            self._refresh_vendors()
            self.vendor_msg.configure(text=f"'{name}' 복원됨", text_color="green")
            self.after(2000, lambda: self.vendor_msg.configure(text=""))

    # ── 비밀번호 변경 ─────────────────────────────────────────────────

    def _build_password_tab(self):
        tab = self.tabview.tab("비밀번호 변경")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for role_key, role_label in [("admin", "관리자"), ("employee", "직원")]:
            card = ctk.CTkFrame(scroll, corner_radius=12)
            card.pack(fill="x", pady=(12, 0))
            ctk.CTkLabel(card, text=f"{role_label} 비밀번호 변경",
                         font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(16, 12))

            new_var = ctk.StringVar()
            confirm_var = ctk.StringVar()
            msg_label = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=13))

            for label, var in [("새 비밀번호", new_var), ("비밀번호 확인", confirm_var)]:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=4)
                ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=14), width=130).pack(side="left")
                ctk.CTkEntry(row, textvariable=var, show="●", width=200,
                             font=ctk.CTkFont(size=14)).pack(side="left")

            msg_label.pack(anchor="w", padx=20, pady=2)

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=20, pady=(4, 16))
            ctk.CTkButton(
                btn_row, text="변경", width=100, height=38,
                font=ctk.CTkFont(size=14),
                command=lambda rk=role_key, nv=new_var, cv=confirm_var, ml=msg_label: (
                    self._change_pw(rk, nv, cv, ml)
                ),
            ).pack(side="left")

    def _change_pw(self, role: str, new_var, confirm_var, msg_label):
        new_pw = new_var.get()
        confirm_pw = confirm_var.get()
        if not new_pw:
            msg_label.configure(text="비밀번호를 입력하세요", text_color="orange")
            return
        if new_pw != confirm_pw:
            msg_label.configure(text="비밀번호가 일치하지 않습니다", text_color="red")
            return
        if len(new_pw) < 4:
            msg_label.configure(text="4자 이상 입력하세요", text_color="orange")
            return
        cm.change_password(role, new_pw)
        new_var.set("")
        confirm_var.set("")
        msg_label.configure(text="비밀번호가 변경되었습니다", text_color="green")
        self.after(3000, lambda: msg_label.configure(text=""))

    def refresh(self):
        self._refresh_vendors()
