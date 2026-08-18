@echo off
echo ========================================
echo  강식당 관리 시스템 빌드
echo ========================================

pip install pyinstaller --quiet

pyinstaller gansikdang.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [오류] 빌드 실패
    pause
    exit /b 1
)

echo.
echo [완료] dist\gansikdang.exe 생성됨
echo.
echo 깃헙 릴리즈에 dist\gansikdang.exe 를 업로드하세요.
pause
