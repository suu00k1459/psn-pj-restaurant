import json
import os
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

from version import VERSION, GITHUB_OWNER, GITHUB_REPO


def _ver_tuple(v: str) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except Exception:
        return (0,)


def fetch_latest_release() -> dict | None:
    """GitHub API로 최신 릴리즈 확인. 현재보다 새 버전이면 info dict 반환, 아니면 None."""
    try:
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "gansikdang-updater"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read())
        tag = data.get("tag_name", "")
        if _ver_tuple(tag) > _ver_tuple(VERSION):
            assets = data.get("assets", [])
            exe_asset = next((a for a in assets if a["name"].endswith(".exe")), None)
            return {
                "version": tag,
                "download_url": exe_asset["browser_download_url"] if exe_asset else None,
                "notes": data.get("body", ""),
            }
    except Exception:
        pass
    return None


def download_and_replace(download_url: str, on_progress=None) -> bool:
    """새 exe 다운로드 후 배치 스크립트로 현재 exe 교체 예약. 성공하면 True."""
    if not getattr(sys, "frozen", False):
        return False  # 개발 환경에서는 동작 안 함

    current_exe = Path(sys.executable)
    new_exe = current_exe.parent / (current_exe.stem + "_update.exe")

    try:
        def _hook(count, block_size, total):
            if on_progress and total > 0:
                on_progress(min(100, int(count * block_size * 100 / total)))

        urllib.request.urlretrieve(download_url, str(new_exe), _hook)

        bat = Path(os.environ.get("TEMP", current_exe.parent)) / "gansikdang_update.bat"
        bat.write_text(
            f"@echo off\n"
            f"timeout /t 2 /nobreak >nul\n"
            f"copy /y \"{new_exe}\" \"{current_exe}\"\n"
            f"del \"{new_exe}\"\n"
            f"start \"\" \"{current_exe}\"\n"
            f"del \"%~f0\"\n",
            encoding="mbcs",
        )
        subprocess.Popen(
            ["cmd", "/c", str(bat)],
            creationflags=subprocess.CREATE_NO_WINDOW,
            close_fds=True,
        )
        return True
    except Exception as e:
        print(f"[updater] error: {e}")
        if new_exe.exists():
            try:
                new_exe.unlink()
            except Exception:
                pass
        return False


def check_and_notify(root, delay_ms: int = 4000):
    """백그라운드에서 업데이트 확인 후 새 버전이 있으면 다이얼로그 표시."""
    from utils.local_settings import get_last_seen_version, set_last_seen_version

    def _bg():
        info = fetch_latest_release()
        if not info:
            return
        # 이미 이 버전 알림을 본 경우 다시 묻지 않음
        if info["version"] == get_last_seen_version():
            return
        set_last_seen_version(info["version"])
        root.after(delay_ms, lambda: _show_dialog(root, info))

    threading.Thread(target=_bg, daemon=True).start()


def _show_dialog(root, info: dict):
    import customtkinter as ctk

    dlg = ctk.CTkToplevel(root)
    dlg.title("업데이트 알림")
    dlg.geometry("420x240")
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.lift()

    ctk.CTkLabel(dlg, text=f"새 버전 {info['version']} 이 출시되었습니다",
                 font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(28, 6))

    notes_raw = (info.get("notes") or "").split("\n")
    notes = " · ".join(
        line.lstrip("#- ").strip() for line in notes_raw if line.strip() and not line.startswith("#")
    )[:120]
    if notes:
        ctk.CTkLabel(dlg, text=notes, font=ctk.CTkFont(size=12),
                     wraplength=360, text_color="gray50").pack(padx=24)

    ctk.CTkLabel(dlg, text="지금 업데이트할까요?",
                 font=ctk.CTkFont(size=13)).pack(pady=(14, 4))

    status_var = ctk.StringVar()
    ctk.CTkLabel(dlg, textvariable=status_var,
                 font=ctk.CTkFont(size=12), text_color="gray50").pack()

    def _do_update():
        if not info.get("download_url"):
            import webbrowser
            webbrowser.open(
                f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
            )
            dlg.destroy()
            return

        btn_yes.configure(state="disabled")
        btn_no.configure(state="disabled")
        status_var.set("다운로드 중...")

        def _on_progress(pct):
            root.after(0, lambda: status_var.set(f"다운로드 중... {pct}%"))

        def _run():
            ok = download_and_replace(info["download_url"], _on_progress)
            if ok:
                root.after(0, _on_done)
            else:
                root.after(0, lambda: status_var.set("실패. 수동으로 다운로드해 주세요."))

        def _on_done():
            status_var.set("완료! 잠시 후 재시작합니다.")
            dlg.after(1500, lambda: (dlg.destroy(), root.destroy()))

        threading.Thread(target=_run, daemon=True).start()

    bf = ctk.CTkFrame(dlg, fg_color="transparent")
    bf.pack(pady=(14, 0))
    btn_yes = ctk.CTkButton(bf, text="업데이트", width=120, command=_do_update)
    btn_yes.pack(side="left", padx=8)
    btn_no = ctk.CTkButton(bf, text="나중에", width=100,
                            fg_color="gray60", command=dlg.destroy)
    btn_no.pack(side="left", padx=8)
