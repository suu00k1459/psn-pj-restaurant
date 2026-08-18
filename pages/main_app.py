import customtkinter as ctk
from datetime import date
from pages.daily_sales_page import DailySalesPage
from pages.expense_page import ExpensePage
from pages.tax_page import TaxPage
from pages.employee_page import EmployeePage
from pages.report_page import ReportPage
from pages.settings_page import SettingsPage
from pages.my_salary_page import MySalaryPage
from utils import config_manager as cm
from utils import excel_manager as em
from utils.i18n import t as _t


class MainApp(ctk.CTkFrame):
    def __init__(self, master, role: str, on_logout):
        super().__init__(master, fg_color="transparent")
        self.role = role
        self.lang = "en" if role != "admin" else "ko"
        self.on_logout = on_logout
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._active_btn = None

        self._build_ui()
        if role == "admin":
            self.after(1500, self._check_auto_csv_export)

    def _build_ui(self):
        # ── Sidebar ──────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0, fg_color=("#1e3a5f", "#0f1f35"))
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Brand
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=10, pady=(20, 4))
        ctk.CTkLabel(
            brand_frame,
            text=_t("강식당", self.lang),
            font=ctk.CTkFont(family="Malgun Gothic", size=22, weight="bold"),
            text_color="white",
        ).pack()
        ctk.CTkLabel(
            brand_frame,
            text=_t("관리 시스템", self.lang),
            font=ctk.CTkFont(size=12),
            text_color=("#90cdf4", "#60a5fa"),
        ).pack()

        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color=("#2d5a8e", "#1e3a5f")).pack(fill="x", padx=10, pady=10)

        # Account info
        role_text = _t("관리자", self.lang) if self.role == "admin" else _t("직원", self.lang)
        role_icon = "👑" if self.role == "admin" else "👤"
        ctk.CTkLabel(
            self.sidebar,
            text=f"{role_icon}  {role_text}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white",
        ).pack(pady=(0, 12))

        # Menu buttons
        menu_items = self._get_menu_items()
        self._nav_buttons = {}
        for key, label in menu_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=ctk.CTkFont(size=14),
                height=50,
                width=160,
                corner_radius=8,
                fg_color="transparent",
                text_color="white",
                hover_color=("#2d5a8e", "#1e4d7a"),
                anchor="w",
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(padx=10, pady=3)
            self._nav_buttons[key] = btn

        # Logout button at bottom
        ctk.CTkFrame(self.sidebar, height=1, fg_color=("#2d5a8e", "#1e3a5f")).pack(fill="x", padx=10, pady=10, side="bottom")
        ctk.CTkButton(
            self.sidebar,
            text=_t("로그아웃", self.lang),
            font=ctk.CTkFont(size=13),
            height=44,
            width=160,
            corner_radius=8,
            fg_color=("#c53030", "#7f1d1d"),
            hover_color=("#9b2c2c", "#631616"),
            text_color="white",
            command=self._logout,
        ).pack(side="bottom", padx=10, pady=(0, 12))

        # ── Content area ─────────────────────────────────
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=("#f0f4f8", "#161b27"))
        self.content.pack(side="left", fill="both", expand=True)

        # Navigate to first page
        first_key = menu_items[0][0]
        self._navigate(first_key)

    def _get_menu_items(self) -> list[tuple[str, str]]:
        return [
            ("daily",    _t("  일일기록", self.lang)),
            ("expense",  _t("  사용금액", self.lang)),
            ("tax",      _t("  세금",    self.lang)),
            ("employee", _t("  직원관리", self.lang)),
            ("report",   _t("  보고서",  self.lang)),
            ("settings", _t("  설정",    self.lang)),
        ]

    def _get_or_create_page(self, key: str) -> ctk.CTkFrame:
        if key in self._pages:
            return self._pages[key]
        page = self._create_page(key)
        self._pages[key] = page
        return page

    def _create_page(self, key: str) -> ctk.CTkFrame:
        kwargs = dict(master=self.content, role=self.role)
        if key == "daily":
            return DailySalesPage(**kwargs)
        elif key == "expense":
            return ExpensePage(**kwargs)
        elif key == "tax":
            return TaxPage(**kwargs)
        elif key == "employee":
            return EmployeePage(**kwargs)
        elif key == "report":
            return ReportPage(**kwargs)
        elif key == "settings":
            return SettingsPage(**kwargs)
        elif key == "my_salary":
            return MySalaryPage(**kwargs)
        raise ValueError(f"Unknown page key: {key}")

    def _navigate(self, key: str):
        # Hide all
        for page in self._pages.values():
            page.pack_forget()

        # Show selected
        page = self._get_or_create_page(key)
        page.pack(fill="both", expand=True)

        # Refresh if available
        if hasattr(page, "refresh"):
            page.refresh()

        # Update button styles
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=("#2d5a8e", "#1e4d7a"), font=ctk.CTkFont(size=14, weight="bold"))
            else:
                btn.configure(fg_color="transparent", font=ctk.CTkFont(size=14))
        self._active_btn = key

    def _check_auto_csv_export(self):
        folder = cm.get_csv_export_folder()
        if not folder:
            return
        import os
        if not os.path.isdir(folder):
            return
        today = date.today()
        if today.month == 1:
            prev_y, prev_m = today.year - 1, 12
        else:
            prev_y, prev_m = today.year, today.month - 1
        prev_ym = f"{prev_y:04d}-{prev_m:02d}"
        if cm.get_csv_last_auto_export() == prev_ym:
            return
        try:
            created = em.export_month_csv(prev_y, prev_m, folder)
            if created:
                cm.set_csv_last_auto_export(prev_ym)
        except Exception:
            pass

    def _logout(self):
        for page in self._pages.values():
            page.destroy()
        self._pages.clear()
        self.on_logout()
