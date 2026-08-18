import customtkinter as ctk
from pages.login_page import LoginPage
from pages.main_app import MainApp

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("강식당 관리 시스템")
        self.geometry("1200x750")
        self.minsize(900, 600)
        self._center()
        self._current_frame = None

        from utils.local_settings import get_data_dir
        if get_data_dir():
            self._show_login()
        else:
            self._show_setup()

        # 업데이트 확인 (백그라운드, 5초 후)
        self.after(5000, self._start_update_check)

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1200) // 2
        y = (self.winfo_screenheight() - 750) // 2
        self.geometry(f"1200x750+{x}+{y}")

    # ── 첫 실행 설정 ──────────────────────────────────────────────────────

    def _show_setup(self):
        self._clear()
        self._current_frame = _SetupPage(self, on_complete=self._on_setup_done)
        self._current_frame.pack(fill="both", expand=True)

    def _on_setup_done(self, path: str):
        from utils.local_settings import set_data_dir
        set_data_dir(path)
        self._show_login()

    # ── 로그인 / 메인 ─────────────────────────────────────────────────────

    def _show_login(self):
        self._clear()
        self._current_frame = LoginPage(self, on_login_success=self._on_login)
        self._current_frame.pack(fill="both", expand=True)

    def _on_login(self, role: str):
        self._clear()
        self._current_frame = MainApp(self, role=role, on_logout=self._show_login)
        self._current_frame.pack(fill="both", expand=True)

    def _clear(self):
        if self._current_frame:
            self._current_frame.destroy()
            self._current_frame = None

    # ── 자동 업데이트 ─────────────────────────────────────────────────────

    def _start_update_check(self):
        try:
            from utils.updater import check_and_notify
            check_and_notify(self)
        except Exception:
            pass


# ─────────────────────────────────────────────
# 첫 실행 설정 화면
# ─────────────────────────────────────────────

class _SetupPage(ctk.CTkFrame):
    def __init__(self, master, on_complete):
        super().__init__(master, fg_color="transparent")
        self._on_complete = on_complete
        self._selected_path = ctk.StringVar()
        self._build()

    def _build(self):
        from pathlib import Path

        ctk.CTkLabel(self, text="강식당 관리 시스템",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(80, 6))
        ctk.CTkLabel(self, text="처음 실행하셨습니다. 데이터(엑셀 파일)를 저장할 폴더를 선택해 주세요.",
                     font=ctk.CTkFont(size=14), text_color="gray50").pack(pady=(0, 40))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack()

        default_path = str(Path.home() / "GansikdangData")
        self._selected_path.set(default_path)

        entry = ctk.CTkEntry(row, textvariable=self._selected_path,
                             width=380, height=36, font=ctk.CTkFont(size=13))
        entry.pack(side="left", padx=(0, 8))

        ctk.CTkButton(row, text="폴더 선택", width=100, height=36,
                      command=self._pick_folder).pack(side="left")

        ctk.CTkLabel(self, text="(선택한 폴더 안에 월별 엑셀 파일이 저장됩니다)",
                     font=ctk.CTkFont(size=12), text_color="gray60").pack(pady=(10, 0))

        ctk.CTkButton(self, text="시작하기", width=160, height=44,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      command=self._confirm).pack(pady=(40, 0))

    def _pick_folder(self):
        import tkinter.filedialog as fd
        path = fd.askdirectory(title="데이터 저장 폴더 선택",
                               initialdir=self._selected_path.get())
        if path:
            self._selected_path.set(path)

    def _confirm(self):
        from pathlib import Path
        path = self._selected_path.get().strip()
        if not path:
            return
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("오류", f"폴더를 만들 수 없습니다:\n{e}")
            return
        self._on_complete(path)


if __name__ == "__main__":
    app = App()
    app.mainloop()
