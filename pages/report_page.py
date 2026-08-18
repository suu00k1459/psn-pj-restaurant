import customtkinter as ctk
from datetime import date
from tkinter import filedialog
from utils import excel_manager as em
from utils import config_manager as cm
from utils.i18n import t as _t

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.font_manager as fm
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False


def _set_korean_font():
    """Set a Korean-compatible font for matplotlib."""
    import os
    # Windows 폰트 직접 로드 (가장 확실한 방법)
    win_fonts_dir = "C:/Windows/Fonts"
    win_candidates = [
        ("malgun.ttf",           "Malgun Gothic"),
        ("malgunbd.ttf",         "Malgun Gothic Bold"),
        ("NanumGothic.ttf",      "NanumGothic"),
        ("NanumBarunGothic.ttf", "NanumBarunGothic"),
    ]
    for fname, family in win_candidates:
        fpath = os.path.join(win_fonts_dir, fname)
        if os.path.exists(fpath):
            fm.fontManager.addfont(fpath)
            plt.rcParams["font.family"] = family
            plt.rcParams["axes.unicode_minus"] = False
            return

    # 이름으로 찾기 (macOS / 기타)
    available = {f.name for f in fm.fontManager.ttflist}
    for name in ["Malgun Gothic", "NanumGothic", "AppleGothic", "Apple SD Gothic Neo",
                 "Arial Unicode MS"]:
        if name in available:
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return

    plt.rcParams["axes.unicode_minus"] = False


class ReportPage(ctk.CTkFrame):
    def __init__(self, master, role: str):
        super().__init__(master, fg_color="transparent")
        self.role = role
        self.lang = "en" if role != "admin" else "ko"
        self.t = lambda s: _t(s, self.lang)
        self._canvas_widget = None
        self._build_ui()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(hdr, text=self.t("월별 보고서"), font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        # Controls
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=24, pady=(0, 4))

        today = date.today()
        self.year_var = ctk.StringVar(value=str(today.year))
        self.month_var = ctk.StringVar(value=f"{today.month:02d}")

        ctk.CTkLabel(ctrl, text=self.t("년도"), font=ctk.CTkFont(size=14)).pack(side="left")
        ctk.CTkEntry(ctrl, textvariable=self.year_var, width=70,
                     font=ctk.CTkFont(size=14)).pack(side="left", padx=(4, 12))
        ctk.CTkLabel(ctrl, text=self.t("월"), font=ctk.CTkFont(size=14)).pack(side="left")
        months = [f"{i:02d}" for i in range(1, 13)]
        ctk.CTkComboBox(ctrl, values=months, variable=self.month_var,
                        width=70, font=ctk.CTkFont(size=14)).pack(side="left", padx=(4, 12))
        ctk.CTkButton(ctrl, text=self.t("조회"), width=80, height=36,
                      font=ctk.CTkFont(size=14),
                      command=self._load_report).pack(side="left", padx=(0, 16))
        ctk.CTkButton(ctrl, text=self.t("CSV 저장"), width=100, height=36,
                      fg_color="#38a169", hover_color="#276749",
                      font=ctk.CTkFont(size=14),
                      command=self._export_csv).pack(side="left", padx=(0, 8))

        # CSV folder row
        csv_row = ctk.CTkFrame(self, fg_color="transparent")
        csv_row.pack(fill="x", padx=24, pady=(0, 10))
        ctk.CTkLabel(csv_row, text=self.t("저장 폴더:"), font=ctk.CTkFont(size=12),
                     text_color="gray50").pack(side="left")
        self._folder_label = ctk.CTkLabel(csv_row, text=self._get_folder_display(),
                                           font=ctk.CTkFont(size=12), text_color="gray40",
                                           anchor="w")
        self._folder_label.pack(side="left", padx=(6, 8))
        ctk.CTkButton(csv_row, text=self.t("폴더 변경"), width=80, height=26,
                      fg_color=("gray70", "gray35"), font=ctk.CTkFont(size=11),
                      command=self._change_folder).pack(side="left")
        self._csv_msg = ctk.CTkLabel(csv_row, text="", font=ctk.CTkFont(size=12))
        self._csv_msg.pack(side="left", padx=10)

        # Scrollable content
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        self._load_report()

    def _get_folder_display(self) -> str:
        folder = cm.get_csv_export_folder()
        return folder if folder else self.t("(미설정 — CSV 저장 시 선택)")

    def _change_folder(self):
        folder = filedialog.askdirectory(title="CSV 저장 폴더 선택")
        if folder:
            cm.set_csv_export_folder(folder)
            self._folder_label.configure(text=folder)

    def _export_csv(self):
        try:
            y = int(self.year_var.get())
            m = int(self.month_var.get())
        except ValueError:
            self._show_csv_msg("년도/월을 올바르게 입력하세요", "red")
            return
        folder = cm.get_csv_export_folder()
        if not folder:
            folder = filedialog.askdirectory(title="CSV 저장 폴더 선택")
            if not folder:
                return
            cm.set_csv_export_folder(folder)
            self._folder_label.configure(text=folder)
        try:
            created = em.export_month_csv(y, m, folder)
        except Exception as e:
            self._show_csv_msg(f"오류: {e}", "red")
            return
        if created:
            self._show_csv_msg(f"{y}년 {m}월 CSV {len(created)}개 저장 완료", "green")
        else:
            self._show_csv_msg("저장할 데이터가 없습니다", "orange")

    def _show_csv_msg(self, text: str, color: str):
        self._csv_msg.configure(text=text, text_color=color)
        self.after(4000, lambda: self._csv_msg.configure(text=""))

    def _load_report(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._canvas_widget = None

        try:
            y = int(self.year_var.get())
            m = int(self.month_var.get())
        except ValueError:
            ctk.CTkLabel(self.scroll, text="년도와 월을 올바르게 입력하세요",
                         text_color="red", font=ctk.CTkFont(size=14)).pack(pady=20)
            return

        sales = em.load_daily_sales(y, m)
        expenses = em.load_expenses(y, m)
        salaries = em.load_salaries(y, m)
        taxes = em.load_taxes(y, m)

        # ── Summary card ─────────────────────────────────────────────
        summary_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        summary_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(summary_card, text=f"{y}년 {m}월 요약",
                     font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w", padx=20, pady=(16, 12))

        total_card = sum(r["card"] for r in sales)
        total_nav = sum(r["nav_cash"] for r in sales)
        total_invoice = sum(r["invoice"] for r in sales)
        total_cash = sum(r["cash"] for r in sales)
        total_transfer = sum(r["transfer_total"] for r in sales)
        total_sales = total_card + total_nav + total_invoice + total_cash + total_transfer

        total_expense = sum(e["amount_ft"] for e in expenses)
        total_salary = sum(s["amount_ft"] for s in salaries)
        total_tax = sum(t["amount_ft"] for t in taxes)
        total_out = total_expense + total_salary + total_tax

        if self.role == "admin":
            items = [
                (self.t("총 카드 매출"), total_card, "#1a56db"),
                (self.t("총 NAV Cash"), total_nav, "#1a56db"),
                (self.t("총 Invoice"), total_invoice, "#1a56db"),
                (self.t("총 현금"), total_cash, "#1a56db"),
                (self.t("총 계좌이체"), total_transfer, "#1a56db"),
                ("─────────────", None, "gray"),
                (self.t("전체 매출 합계"), total_sales, "#38a169"),
                (self.t("총 매입 지출"), total_expense, "#e53e3e"),
                (self.t("총 급여 지출"), total_salary, "#e53e3e"),
                (self.t("총 세금 지출"), total_tax, "#e53e3e"),
                ("─────────────", None, "gray"),
                (self.t("순이익 (매출 - 지출)"), total_sales - total_out, "#6b46c1"),
            ]
        else:
            items = [
                (self.t("총 카드 매출"), total_card, "#1a56db"),
                (self.t("총 NAV Cash"), total_nav, "#1a56db"),
                (self.t("총 Invoice"), total_invoice, "#1a56db"),
                ("─────────────", None, "gray"),
                (self.t("총 매입 지출"), total_expense, "#e53e3e"),
            ]

        grid = ctk.CTkFrame(summary_card, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 16))
        for i, (label, val, color) in enumerate(items):
            row = ctk.CTkFrame(grid, fg_color=("#f0f4f8" if i % 2 == 0 else "white", "#1a1a2e"),
                               corner_radius=4)
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=14), width=220,
                         anchor="w").pack(side="left", padx=12, pady=6)
            if val is not None:
                ctk.CTkLabel(row, text=f"{val:,.0f} ft",
                             font=ctk.CTkFont(size=14, weight="bold"),
                             text_color=color).pack(side="right", padx=16)

        # ── Charts ───────────────────────────────────────────────────
        if not MATPLOTLIB_OK:
            ctk.CTkLabel(self.scroll,
                         text="그래프 표시를 위해 matplotlib을 설치하세요: pip install matplotlib",
                         text_color="orange", font=ctk.CTkFont(size=13)).pack(pady=12)
            return

        if self.role == "admin":
            if not sales and not expenses:
                ctk.CTkLabel(self.scroll, text=self.t("데이터가 없습니다"),
                             text_color="gray", font=ctk.CTkFont(size=14)).pack(pady=20)
                return
            _set_korean_font()
            self._draw_charts(y, m, sales, expenses, salaries)
        else:
            if not expenses:
                ctk.CTkLabel(self.scroll, text=self.t("매입 데이터가 없습니다"),
                             text_color="gray", font=ctk.CTkFont(size=14)).pack(pady=20)
                return
            _set_korean_font()
            self._draw_employee_charts(y)

    def _draw_charts(self, y, m, sales, expenses, salaries):
        chart_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        chart_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(chart_card, text="차트",
                     font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w", padx=20, pady=(16, 8))

        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        fig.patch.set_facecolor("#f8faff")

        # ── Bar chart: monthly totals ─────────────────────────────
        ax1 = axes[0]
        labels = ["카드", "NAV Cash", "Invoice", "현금", "계좌이체", "매입", "급여"]
        values = [
            sum(r["card"] for r in sales),
            sum(r["nav_cash"] for r in sales),
            sum(r["invoice"] for r in sales),
            sum(r["cash"] for r in sales),
            sum(r["transfer_total"] for r in sales),
            sum(e["amount_ft"] for e in expenses),
            sum(s["amount_ft"] for s in salaries),
        ]
        colors = ["#4299e1", "#48bb78", "#ed8936", "#9f7aea", "#fc8181", "#f6ad55", "#68d391"]
        bars = ax1.bar(labels, values, color=colors, edgecolor="white", linewidth=0.8, width=0.5)
        ax1.set_title(f"{y}년 {m}월 항목별 집계", fontsize=19, pad=16, fontweight="bold")
        ax1.set_ylabel("금액 (ft)", fontsize=16)
        ax1.tick_params(axis="x", labelsize=16)
        ax1.tick_params(axis="y", labelsize=14)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax1.set_facecolor("#fafafa")
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        mv = max(values) if values else 1
        for bar, val in zip(bars, values):
            if val > 0:
                ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + mv * 0.012,
                         f"{val:,.0f}", ha="center", va="bottom", fontsize=13)

        # ── Line chart: daily sales trend ─────────────────────────
        ax2 = axes[1]
        if sales:
            days = [r["date"][-2:] for r in sales]
            daily_total = [r["card"] + r["nav_cash"] + r["invoice"] + r["cash"] + r["transfer_total"]
                           for r in sales]
            ax2.plot(days, daily_total, marker="o", color="#1a56db", linewidth=2.5,
                     markersize=8, markerfacecolor="white", markeredgewidth=2.5,
                     label="일별 매출")
            ax2.fill_between(range(len(days)), daily_total, alpha=0.1, color="#1a56db")
            ax2.set_xticks(range(len(days)))
            ax2.set_xticklabels(days, rotation=45, fontsize=14)
            ax2.tick_params(axis="y", labelsize=14)
            ax2.set_title(f"{y}년 {m}월 일별 매출 추이", fontsize=19, pad=16, fontweight="bold")
            ax2.set_xlabel("일(日)", fontsize=16)
            ax2.set_ylabel("금액 (ft)", fontsize=16)
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
            ax2.legend(fontsize=14, loc="upper left")
            ax2.set_facecolor("#fafafa")
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)
        else:
            ax2.text(0.5, 0.5, "매출 데이터 없음", ha="center", va="center",
                     transform=ax2.transAxes, fontsize=14, color="gray")
            ax2.set_facecolor("#fafafa")

        fig.tight_layout(pad=3.0)

        canvas = FigureCanvasTkAgg(fig, master=chart_card)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(fill="x", padx=16, pady=(0, 16))
        self._canvas_widget = canvas
        plt.close(fig)

    def _draw_employee_charts(self, y):
        chart_card = ctk.CTkFrame(self.scroll, corner_radius=12)
        chart_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(chart_card, text=self.t("월별 매입 추이"),
                     font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w", padx=20, pady=(16, 8))

        if self.lang == "en":
            from utils.date_widgets import _MONTH_ABBR_EN
            month_labels = _MONTH_ABBR_EN
        else:
            month_labels = [f"{i}월" for i in range(1, 13)]
        values = []
        for m in range(1, 13):
            month_expenses = em.load_expenses(y, m)
            values.append(sum(e.get("amount_ft", 0) for e in month_expenses))

        if all(v == 0 for v in values):
            ctk.CTkLabel(chart_card, text=self.t("매입 데이터 없음"), text_color="gray",
                         font=ctk.CTkFont(size=13)).pack(pady=20)
            return

        fig, ax = plt.subplots(figsize=(12, 5))
        fig.patch.set_facecolor("#f8faff")
        chart_legend = self.t("월별 매입")
        ax.plot(month_labels, values, marker="o", color="#e53e3e", linewidth=2.5,
                markersize=8, markerfacecolor="white", markeredgewidth=2.5,
                label=chart_legend)
        ax.fill_between(range(12), values, alpha=0.08, color="#e53e3e")
        ax.set_xticks(range(12))
        ax.set_xticklabels(month_labels, fontsize=14)
        ax.tick_params(axis="y", labelsize=14)
        title = f"Monthly Purchase Trend {y}" if self.lang == "en" else f"{y}년 월별 매입 추이"
        ax.set_title(title, fontsize=19, pad=16, fontweight="bold")
        ax.set_ylabel(self.t("금액 (ft)"), fontsize=16)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.legend(fontsize=14, loc="upper left")
        ax.set_facecolor("#fafafa")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout(pad=3.0)

        canvas = FigureCanvasTkAgg(fig, master=chart_card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=16, pady=(0, 16))
        self._canvas_widget = canvas
        plt.close(fig)

    def refresh(self):
        self._load_report()
