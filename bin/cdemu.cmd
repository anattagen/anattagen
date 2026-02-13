@echo off
setlocal enabledelayedexpansion
set "ISO=%~1"
set "SCRIPT_NAME=%~n0"
set "FLAG=%~2"

:: Check for unmount flag
if /I "%FLAG%"=="-unmount" goto :unmount
if /I "%FLAG%"=="/unmount" goto :unmount
if /I "%FLAG%"=="--unmount" goto :unmount

:: Check if script name indicates unmount
if /I "%SCRIPT_NAME%"=="_unmount" goto :unmount

:: ============================================
:: MOUNT LOGIC
:: ============================================

if /I "%SCRIPT_NAME%"=="nativemount" (
    powershell -command "Mount-DiskImage -ImagePath '%ISO%'"
    goto :eof
)

if /I "%SCRIPT_NAME%"=="cdemu" (
    "" "%ISO%"
    goto :eof
)

if /I "%SCRIPT_NAME%"=="osf" (
    "" /mount "%ISO%"
    goto :eof
)

if /I "%SCRIPT_NAME%"=="cdmage" (
    "" /mount "%ISO%"
    goto :eof
)

if /I "%SCRIPT_NAME%"=="imgdrive" (
    "" /mount "%ISO%"
    goto :eof
)

goto :eof

:: ============================================
:: UNMOUNT LOGIC
:: ============================================
:unmount

:: Try Native
powershell -command "Dismount-DiskImage -ImagePath '%ISO%'" >nul 2>&1
if %ERRORLEVEL%==0 goto :eof

:: Try WinCDEmu
if not ""=="" (
    "" /unmount "%ISO%" >nul 2>&1
    if %ERRORLEVEL%==0 goto :eof
)

:: Try OSF
if not ""=="" (
    "" -unmount "%ISO%" >nul 2>&1
    if %ERRORLEVEL%==0 goto :eof
)

:: Try CDMage
if not ""=="" (
    "" -eject >nul 2>&1
    if %ERRORLEVEL%==0 goto :eof
)

:: Try ImgDrive
if not ""=="" (
    "" -u "%ISO%" >nul 2>&1
    if %ERRORLEVEL%==0 goto :eof
)

:eof
endlocal
exit /b