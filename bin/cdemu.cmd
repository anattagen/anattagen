@echo off
set "ISO=%~1"
set "SCRIPT_NAME=%~n0"

:: Unmount Logic
if /I "%SCRIPT_NAME%"=="_unmount" (
    :: Try Native
    powershell -command "Dismount-DiskImage -ImagePath '%ISO%'" >nul 2>&1
    
    :: Try WinCDEmu
    if not ""=="" (
        "" /unmount "%ISO%" >nul 2>&1
    )
    
    :: Try iMount
    if not ""=="" (
        "" -unmount "%ISO%" >nul 2>&1
    )
    
    :: Try OSF
    if not ""=="" (
        "" -unmount "%ISO%" >nul 2>&1
    )
    
    goto :eof
)

:: Mount Logic
if /I "%SCRIPT_NAME%"=="nativemount" (
    powershell -command "Mount-DiskImage -ImagePath '%ISO%'"
    goto :eof
)

if /I "%SCRIPT_NAME%"=="cdemu" (
    "" /mount "%ISO%"
    goto :eof
)

if /I "%SCRIPT_NAME%"=="imount" (
    "" -mount "%ISO%"
    goto :eof
)

if /I "%SCRIPT_NAME%"=="osf" (
    "" -mount "%ISO%"
    goto :eof
)

if /I "%SCRIPT_NAME%"=="cdmage" (
    "" /mount "%ISO%"
    goto :eof
)