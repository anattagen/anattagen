@echo off
setlocal enabledelayedexpansion
REM _unmount.cmd.set - Unmount Template
if not exist "drvltr" goto :eof
set /p VAL=<drvltr
if "%VAL%"=="" goto :eof

set "PREFIX=%VAL:~0,1%"
set "LETTER=%VAL:~1%"

if "%PREFIX%"=="2" (
    REM Prefix 2 detected: Try WinCDEmu first
    if exist "%~dp0WinCDEmu.exe" (
        "%~dp0WinCDEmu.exe" /unmount "%LETTER%:"
    )
    REM Fallback to Native if drive still exists
    if exist "%LETTER%:\nul" (
        powershell -Command "Get-DiskImage -DevicePath (Get-Volume -DriveLetter '%LETTER%').Path | Dismount-DiskImage"
    )
) else (
    REM No prefix: Try Native first (VAL is the letter)
    set "LETTER=%VAL%"
    mountvol %LETTER% /p
    vol %LETTER%: | find "Volume"
    if not errorlevel 1 ( 
    powershell -Command "Get-DiskImage -DevicePath (Get-Volume -DriveLetter '!LETTER!').Path | Dismount-DiskImage"
    )
    REM Fallback to WinCDEmu if drive still exists
    if exist "!LETTER!:\nul" (
        if exist("[WINCDEMUPATH]" && "[WINCDEMUPATH]" neq "") set "WCDU=[WINCDEMUPATH]" && "!WCDU!" /unmount "!LETTER!:"
            )
        else if (exist("%~dp0WinCDEmu.exe") set "WCDU=%~dp0WinCDEmu.exe" && "!WCDU!" /unmount "!LETTER!:")
    )
)n
del "drvltr"
