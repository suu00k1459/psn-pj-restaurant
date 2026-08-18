import customtkinter as ctk
from utils.config_manager import verify_password


class LoginPage(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color="transparent")
        self.on_login_success = on_login_success
        self.selected_role = ctk.StringVar(value="")

        self._build_ui()

    def _build_ui(self):
        # Center container
        container = ctk.CTkFrame(self, corner_radius=16, fg_color=("white", "#1e1e2e"))
        container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.4, relheight=0.65)

        # Title
        title = ctk.CTkLabel(
            container,
            text="강식당 관리 시스템",
            font=ctk.CTkFont(family="Malgun Gothic", size=28, weight="bold"),
            text_color=("#1a56db", "#60a5fa"),
        )
        title.pack(pady=(40, 8))

        subtitle = ctk.CTkLabel(
            container,
            text="Gansikdang Management System",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        subtitle.pack(pady=(0, 30))

        # Role buttons
        role_frame = ctk.CTkFrame(container, fg_color="transparent")
        role_frame.pack(fill="x", padx=40, pady=(0, 20))

        self.admin_btn = ctk.CTkButton(
            role_frame,
            text="관리자 로그인",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=("gray85", "#2d2d3d"),
            text_color=("gray30", "gray70"),
            hover_color=("#dbeafe", "#1e3a5f"),
            command=lambda: self._select_role("admin"),
        )
        self.admin_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

        self.employee_btn = ctk.CTkButton(
            role_frame,
            text="직원 로그인",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=("gray85", "#2d2d3d"),
            text_color=("gray30", "gray70"),
            hover_color=("#dbeafe", "#1e3a5f"),
            command=lambda: self._select_role("employee"),
        )
        self.employee_btn.pack(side="left", expand=True, fill="x", padx=(8, 0))

        # Role label
        self.role_label = ctk.CTkLabel(
            container,
            text="역할을 선택하세요",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.role_label.pack(pady=(0, 10))

        # Password field
        pw_frame = ctk.CTkFrame(container, fg_color="transparent")
        pw_frame.pack(fill="x", padx=40, pady=(0, 8))

        ctk.CTkLabel(
            pw_frame,
            text="비밀번호",
            font=ctk.CTkFont(size=14),
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.pw_entry = ctk.CTkEntry(
            pw_frame,
            show="●",
            font=ctk.CTkFont(size=14),
            height=42,
            corner_radius=8,
            placeholder_text="비밀번호를 입력하세요",
        )
        self.pw_entry.pack(fill="x")
        self.pw_entry.bind("<Return>", lambda e: self._do_login())

        # Login button
        self.login_btn = ctk.CTkButton(
            container,
            text="로그인",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46,
            corner_radius=10,
            command=self._do_login,
        )
        self.login_btn.pack(fill="x", padx=40, pady=(12, 8))

        # Message label
        self.msg_label = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="red",
        )
        self.msg_label.pack(pady=(0, 20))

    def _select_role(self, role: str):
        self.selected_role.set(role)
        if role == "admin":
            self.admin_btn.configure(
                fg_color="#1a56db",
                text_color="white",
            )
            self.employee_btn.configure(
                fg_color=("gray85", "#2d2d3d"),
                text_color=("gray30", "gray70"),
            )
            self.role_label.configure(text="관리자로 로그인합니다", text_color="#1a56db")
        else:
            self.employee_btn.configure(
                fg_color="#1a56db",
                text_color="white",
            )
            self.admin_btn.configure(
                fg_color=("gray85", "#2d2d3d"),
                text_color=("gray30", "gray70"),
            )
            self.role_label.configure(text="직원으로 로그인합니다", text_color="#1a56db")
        self.msg_label.configure(text="")
        self.pw_entry.focus_set()

    def _do_login(self):
        role = self.selected_role.get()
        if not role:
            self.msg_label.configure(text="역할을 먼저 선택하세요", text_color="orange")
            return
        password = self.pw_entry.get()
        if not password:
            self.msg_label.configure(text="비밀번호를 입력하세요", text_color="orange")
            return
        if verify_password(role, password):
            self.msg_label.configure(text="로그인 성공!", text_color="green")
            self.after(300, lambda: self.on_login_success(role))
        else:
            self.msg_label.configure(text="비밀번호가 올바르지 않습니다", text_color="red")
            self.pw_entry.delete(0, "end")

    def reset(self):
        self.selected_role.set("")
        self.pw_entry.delete(0, "end")
        self.msg_label.configure(text="")
        self.role_label.configure(text="역할을 선택하세요", text_color="gray")
        for btn in [self.admin_btn, self.employee_btn]:
            btn.configure(fg_color=("gray85", "#2d2d3d"), text_color=("gray30", "gray70"))
