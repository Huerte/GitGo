@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "SRC_DIR=%SCRIPT_DIR%src"

echo.
echo ========================================
echo    GitGo Automated Installer v1.0
echo ========================================
echo.

net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with administrator privileges...
) else (
    echo [WARNING] Not running as administrator. PATH changes may require manual labor/restart.
)

python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found or not in PATH!
    echo Please install Python first and try utro.
    pause
    exit /b 1
)

echo [INFO] Python detected: 
python --version

if not exist "%SRC_DIR%\gitgo.py" (
    echo [ERROR] gitgo.py not found in src directory!
    echo Make sure you're running this from the GitGo root directory.
    pause
    exit /b 1
)

if not exist "%SRC_DIR%\gitgo.bat" (
    echo [ERROR] gitgo.bat not found in src directory!
    pause
    exit /b 1
)

set "INSTALL_DIR=%APPDATA%\GitGo"
echo [INFO] Installing to: %INSTALL_DIR%

if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo [INFO] Created installation directory.
)

echo [INFO] Copying files...
copy "%SRC_DIR%\gitgo.py" "%INSTALL_DIR%\" >nul
copy "%SRC_DIR%\gitgo.bat" "%INSTALL_DIR%\" >nul
copy "%SRC_DIR%\refresh-path.ps1" "%INSTALL_DIR%\" >nul
copy "%SRC_DIR%\refresh-path.bat" "%INSTALL_DIR%\" >nul

if %errorLevel% neq 0 (
    echo [ERROR] Failed to copy files!
    pause
    exit /b 1
)

echo [INFO] Files copied successfully.

echo %PATH% | findstr /i "%INSTALL_DIR%" >nul
if %errorLevel% == 0 (
    echo [INFO] GitGo is already in your PATH.
    goto :test_installation
)

echo [INFO] Adding GitGo to your PATH...

for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%B"

if "!USER_PATH!"=="" (
    set "NEW_PATH=%INSTALL_DIR%"
) else (
    echo !USER_PATH! | findstr /i "%INSTALL_DIR%" >nul
    if !errorLevel! == 0 (
        echo [INFO] GitGo is already in your user PATH.
        goto :test_installation
    )
    set "NEW_PATH=!USER_PATH!;%INSTALL_DIR%"
)

reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "!NEW_PATH!" /f >nul

if %errorLevel% == 0 (
    echo [SUCCESS] GitGo added to your PATH!
    echo [INFO] You may need to restart your terminal/IDE for changes to take effect.
) else (
    echo [ERROR] Failed to update PATH. You may need to add it manually:
    echo Add this to your PATH: %INSTALL_DIR%
)

:test_installation
echo.
echo [INFO] Testing installation...

setlocal
set "PATH=%PATH%;%INSTALL_DIR%"
gitgo -r >nul 2>&1
if %errorLevel% == 0 (
    echo [SUCCESS] GitGo is working correctly!
    echo.
    echo ========================================
    echo    Installation Complete! 🎉
    echo ========================================
    echo.
    echo You can now use 'gitgo' from anywhere:
    echo   gitgo -r                    ^(check status^)
    echo   gitgo push main "message"   ^(push to branch^)
    echo   gitgo push -n branch "msg"  ^(create new branch^)
    echo.
    
    powershell -ExecutionPolicy Bypass -Command "try { $env:PATH = [System.Environment]::GetEnvironmentVariable('PATH','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('PATH','User'); Write-Host '[SUCCESS] PATH refreshed for current session!' -ForegroundColor Green } catch { Write-Host '[INFO] Manual PATH refresh may be needed in IDE terminals.' -ForegroundColor Yellow }" 2>nul
    
) else (
    echo [WARNING] GitGo installation may not be working properly.
    echo Try restarting your terminal and running: gitgo -r
)

echo Press any key to exit...
pause >nul
