@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo    GitGo Uninstaller v1.1
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
echo - Remove all GitGo files from %INSTALL_DIR%
echo - Remove GitGo from your PATH
echo.
set /p "CONFIRM=Are you sure you want to uninstall GitGo? (y/N): "

if /i not "%CONFIRM%"=="y" (
    echo [INFO] Uninstallation cancelled.
    goto :end
)

echo [INFO] Removing GitGo files...
rmdir /S /Q "%INSTALL_DIR%" 2>nul

if exist "%INSTALL_DIR%" (
    echo [WARNING] Could not remove installation directory completely.
    echo PS: You may need to manually delete: %INSTALL_DIR%
) else (
    echo [SUCCESS] GitGo files removed successfully.
)

echo [INFO] Removing GitGo from PATH...

for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%B"

if not defined USER_PATH (
    echo [INFO] No user PATH found.
    goto :refresh_path
)

set "NEW_PATH=!USER_PATH:%INSTALL_DIR%;=!"
set "NEW_PATH=!NEW_PATH:;%INSTALL_DIR%=!"
set "NEW_PATH=!NEW_PATH:%INSTALL_DIR%=!"

if not "!NEW_PATH!"=="!USER_PATH!" (
    reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "!NEW_PATH!" /f >nul
    if !errorLevel! == 0 (
        echo [SUCCESS] GitGo removed from PATH.
    ) else (
        echo [WARNING] Could not update PATH automatically.
        echo PS: You may need to manually remove "%INSTALL_DIR%" from your PATH.
    )
) else (
    echo [INFO] GitGo not found in PATH.
)

:refresh_path
echo [INFO] Refreshing PATH for current session...
powershell -ExecutionPolicy Bypass -Command ^
"try {
    $env:PATH = [System.Environment]::GetEnvironmentVariable('PATH','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('PATH','User');
    Write-Host '[SUCCESS] PATH refreshed for current session!' -ForegroundColor Green
} catch {
    Write-Host '[INFO] Manual PATH refresh may be needed in IDE terminals.' -ForegroundColor Yellow
}" 2>nul

echo.
echo ========================================
echo    Uninstallation Complete! 
echo ========================================
echo.
echo GitGo has been removed from your system.
echo Restart your terminal to see the effect.

:end
echo.
echo Press any key to exit...
pause >nul
