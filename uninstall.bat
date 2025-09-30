@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo    GitGo Uninstaller v1.0
echo ========================================
echo.

set "INSTALL_DIR=%APPDATA%\GitGo"

if not exist "%INSTALL_DIR%" (
    echo [INFO] GitGo is not installed in the expected location.
    echo Installation directory not found: %INSTALL_DIR%
    goto :end
)

echo [INFO] Found GitGo installation at: %INSTALL_DIR%
echo.
echo This will:
echo - Remove GitGo files from %INSTALL_DIR%
echo - Remove GitGo from your PATH
echo.
set /p "CONFIRM=Are you sure you want to uninstall GitGo? (y/N): "

if /i not "%CONFIRM%"=="y" (
    echo [INFO] Uninstallation cancelled.
    goto :end
)

echo [INFO] Removing GitGo files...
if exist "%INSTALL_DIR%\gitgo.py" del "%INSTALL_DIR%\gitgo.py"
if exist "%INSTALL_DIR%\gitgo.bat" del "%INSTALL_DIR%\gitgo.bat"
if exist "%INSTALL_DIR%\refresh-path.ps1" del "%INSTALL_DIR%\refresh-path.ps1"
if exist "%INSTALL_DIR%\refresh-path.bat" del "%INSTALL_DIR%\refresh-path.bat"
if exist "%INSTALL_DIR%\fix-ide-path.bat" del "%INSTALL_DIR%\fix-ide-path.bat"
rmdir "%INSTALL_DIR%" 2>nul

if exist "%INSTALL_DIR%" (
    echo [WARNING] Could not remove installation directory completely.
    echo PS: Might need to manually remove: %INSTALL_DIR%
) else (
    echo [SUCCESS] GitGo files removed.
)

echo [INFO] Removing GitGo from PATH...

for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%B"

if "!USER_PATH!"=="" (
    echo [INFO] No user PATH found.
    goto :cleanup_complete
)

set "NEW_PATH=!USER_PATH!"
set "NEW_PATH=!NEW_PATH:%INSTALL_DIR%;=!"
set "NEW_PATH=!NEW_PATH:;%INSTALL_DIR%=!"
set "NEW_PATH=!NEW_PATH:%INSTALL_DIR%=!"

if not "!NEW_PATH!"=="!USER_PATH!" (
    reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "!NEW_PATH!" /f >nul
    if !errorLevel! == 0 (
        echo [SUCCESS] GitGo removed from PATH.
    ) else (
        echo [WARNING] Could not update PATH automatically.
        echo PS: Might need manual removal of: %INSTALL_DIR%
    )
) else (
    echo [INFO] GitGo was not found in your PATH.
)

:cleanup_complete
echo.
echo ========================================
echo    Uninstallation Complete! 👋
echo ========================================
echo.
echo GitGo has been removed from your system.
echo Restartterminal to see effect.

:end
echo.
echo Press any key to exit...
pause >nul
