@echo off
REM combined.cmd.set - Universal Disc Mount Orchestrator
REM Paradigm: 
REM   1. Standalone or part of larger script execution
REM   2. Clean exit with error logging to recycle log
REM   3. Multiple run modes: filename as priority app, %~2 as queue-order digits,
REM      alphabetic character for drive-letter, string for priority status
REM   4. Headless operation, independent instances, exclusive execution,
REM      run-wait status, administrator run-level support
REM
REM Usage: 
REM   combined.cmd.set [disc_image] [mode_argument]
REM   
REM Mode Arguments:
REM   (none)         - Auto-detect best mount method
REM   1-9            - Priority order for mount method queue
REM   A-Z (letter)  - Specific drive letter to use
REM   /native        - Force native Windows mount
REM   /cdemu         - Force WinCDEmu mount
REM   /imount        - Force imount mount
REM   /wait          - Wait for mount to complete (default)
REM   /nowait        - Don't wait for mount completion
REM   /admin         - Require administrator privileges
REM   /exclusive     - Exclusive mount (no other instances)
REM
REM Returns: drvltr file with drive letter on success

setlocal enabledelayedexpansion

REM Script identification
set "SCRIPT_NAME=combined"
set "SCRIPT_VERSION=2.0"

REM Error log path (recycle log)
set "ERROR_LOG=%TEMP%\%SCRIPT_NAME%_errors.log"
set "INSTANCE_LOG=%TEMP%\%SCRIPT_NAME%_instances.log"

REM ============================================
REM INSTANCE MANAGEMENT - Headless & Independent
REM ============================================
set "INSTANCE_ID=%TIME:~6,5%%RANDOM%"
set "LOCK_FILE=%TEMP%\%SCRIPT_NAME%_%INSTANCE_ID%.lock"

REM Check for exclusive mode
set "EXCLUSIVE=0"
if /i "%~2"=="/exclusive" set "EXCLUSIVE=1"

if "%EXCLUSIVE%"=="1" (
    REM Check for other instances
    for /f "tokens=1" %%a in ('dir /b "%TEMP%\%SCRIPT_NAME%_*.lock" 2^>nul') do (
        set "OTHER_INSTANCE=%%a"
        if not "!OTHER_INSTANCE!"=="%LOCK_FILE%" (
            echo [%DATE% %TIME%] ERROR: Another instance is running >> "%ERROR_LOG%"
            exit /b 1
        )
    )
    REM Create lock file
    echo %DATE% %TIME%> "%LOCK_FILE%"
)

REM ============================================
REM PRIVILEGE CHECK - Administrator Run-Level
REM ============================================
set "IS_ADMIN=0"
net session >nul 2>&1
if not errorlevel 1 set "IS_ADMIN=1"

set "REQUIRE_ADMIN=0"
if /i "%~2"=="/admin" set "REQUIRE_ADMIN=1"

if "%REQUIRE_ADMIN%"=="1" if "%IS_ADMIN%"=="0" (
    echo [%DATE% %TIME%] ERROR: Administrator privileges required >> "%ERROR_LOG%"
    if exist "%LOCK_FILE%" del /q "%LOCK_FILE%"
    exit /b 1
)

REM ============================================
REM ARGUMENT PARSING - Multiple Run Modes
REM ============================================
set "DISCIMAGE=%~1"
set "MODE_ARG=%~2"

REM Clean up previous drive letter file
if exist "drvltr" del /q "drvltr"

REM Parse mode argument
set "RUN_MODE=auto"
set "PRIORITY="
set "DRIVELETTER="
set "FORCE_METHOD="
set "WAIT_MODE=1"

if "%MODE_ARG%"=="" (
    set "RUN_MODE=auto"
) else if "%MODE_ARG:~0,1%"=="/" (
    REM Flag-based arguments
    if /i "%MODE_ARG%"=="/native" set "FORCE_METHOD=native"
    if /i "%MODE_ARG%"=="/cdemu" set "FORCE_METHOD=cdemu"
    if /i "%MODE_ARG%"=="/imount" set "FORCE_METHOD=imount"
    if /i "%MODE_ARG%"=="/wait" set "WAIT_MODE=1"
    if /i "%MODE_ARG%"=="/nowait" set "WAIT_MODE=0"
    set "RUN_MODE=flag"
) else if "%MODE_ARG%" geq 1 if "%MODE_ARG%" leq 9 (
    REM Priority digits - queue order
    set "PRIORITY=%MODE_ARG%"
    set "RUN_MODE=priority"
) else if "%MODE_ARG:~0,1%" geq a if "%MODE_ARG%" leq z (
    REM Drive letter assignment
    set "DRIVELETTER=%MODE_ARG%"
    set "RUN_MODE=letter"
) else if "%MODE_ARG:~0,1%" geq A if "%MODE_ARG%" leq Z (
    REM Drive letter assignment (uppercase)
    set "DRIVELETTER=%MODE_ARG%"
    set "RUN_MODE=letter"
) else (
    REM Priority status string
    set "PRIORITY_STATUS=%MODE_ARG%"
    set "RUN_MODE=status"
)

REM ============================================
REM EXECUTION MODE - Standalone or Subroutine
REM ============================================
set "STANDALONE=0"
if "%~3"=="-standalone" set "STANDALONE=1"
if "%~3"=="-subroutine" set "STANDALONE=0"

REM Check for valid disc image
if "%DISCIMAGE%"=="" (
    echo [%DATE% %TIME%] ERROR: No disc image specified >> "%ERROR_LOG%"
    if exist "%LOCK_FILE%" del /q "%LOCK_FILE%"
    exit /b 1
)

if not exist "%DISCIMAGE%" (
    echo [%DATE% %TIME%] ERROR: Disc image not found: %DISCIMAGE% >> "%ERROR_LOG%"
    if exist "%LOCK_FILE%" del /q "%LOCK_FILE%"
    exit /b 1
)

REM ============================================
REM MOUNT METHOD EXECUTION
REM ============================================
set "MOUNT_RESULT=1"

if "%RUN_MODE%"=="auto" (
    REM Try methods in order: native, cdemu, imount
    call :mount_native
    if errorlevel 1 call :mount_cdemu
    if errorlevel 1 call :mount_imount
) else if "%RUN_MODE%"=="priority" (
    REM Use priority to determine method
    if "%PRIORITY%"=="1" call :mount_native
    if "%PRIORITY%"=="2" call :mount_cdemu
    if "%PRIORITY%"=="3" call :mount_imount
    if errorlevel 1 (
        echo [%DATE% %TIME%] ERROR: Priority %PRIORITY% mount failed >> "%ERROR_LOG%"
    )
) else if "%RUN_MODE%"=="letter" (
    REM Use specified drive letter
    call :mount_native_letter
    if errorlevel 1 call :mount_cdemu_letter
    if errorlevel 1 call :mount_imount_letter
) else if "%RUN_MODE%"=="flag" (
    REM Force specific method
    if "%FORCE_METHOD%"=="native" call :mount_native
    if "%FORCE_METHOD%"=="cdemu" call :mount_cdemu
    if "%FORCE_METHOD%"=="imount" call :mount_imount
) else if "%RUN_MODE%"=="status" (
    REM Priority status execution
    call :mount_native
    if errorlevel 1 call :mount_cdemu
    if errorlevel 1 call :mount_imount
)

REM ============================================
REM RESULTS - Clean Exit & Logging
REM ============================================
if exist "drvltr" (
    for /f %%a in (drvltr) do (
        if "%%a" NEQ "" (
            echo [%DATE% %TIME%] SUCCESS: %DISCIMAGE% mounted to %%a (mode: %RUN_MODE%) >> "%ERROR_LOG%"
            if "%STANDALONE%"=="1" echo Mounted to drive %%a
            set "MOUNT_RESULT=0"
        )
    )
)

REM Clean up lock file
if exist "%LOCK_FILE%" del /q "%LOCK_FILE%"

if "%MOUNT_RESULT%"=="0" (
    exit /b 0
) else (
    echo [%DATE% %TIME%] ERROR: Failed to mount %DISCIMAGE% (mode: %RUN_MODE%) >> "%ERROR_LOG%"
    exit /b 1
)

REM ============================================
REM MOUNT METHODS - Standalone Subroutines
REM ============================================

:mount_native
REM Native Windows Mount (PowerShell)
set "NATIVE_EXE="
powershell -Command "$m = Mount-DiskImage -ImagePath '%DISCIMAGE%' -PassThru -ErrorAction SilentlyContinue; if ($m) { ($m | Get-Volume).DriveLetter | Out-File -FilePath 'drvltr' -Encoding ASCII -NoNewline }" 2>> "%ERROR_LOG%"
if errorlevel 0 (
    if exist "drvltr" for /f %%a in (drvltr) do (
        if "%%a" NEQ "" exit /b 0
    )
)
exit /b 1

:mount_native_letter
powershell -Command "$m = Mount-DiskImage -ImagePath '%DISCIMAGE%' -PassThru -ErrorAction SilentlyContinue; if ($m) { ($m | Get-Volume).DriveLetter | Out-File -FilePath 'drvltr' -Encoding ASCII -NoNewline }" 2>> "%ERROR_LOG%"
exit /b 0

:mount_cdemu
REM WinCDEmu Mount
set "WCDU="
if "%WCDU%"=="" set "WCDU=%~dp0WinCDEmu.exe"
if exist "%WCDU%" (
    "%WCDU%" /mount "%DISCIMAGE%" 2>> "%ERROR_LOG%"
    if errorlevel 0 (
        for /f "delims=" %%a in ('"%WCDU%" /check "%DISCIMAGE%" 2^>nul') do (
            echo 2%%a>drvltr
            exit /b 0
        )
    )
)
exit /b 1

:mount_cdemu_letter
set "WCDU="
if "%WCDU%"=="" set "WCDU=%~dp0WinCDEmu.exe"
if exist "%WCDU%" (
    "%WCDU%" /mount "%DISCIMAGE%" /letter:%DRIVELETTER% 2>> "%ERROR_LOG%"
    if errorlevel 0 (
        echo 2%DRIVELETTER%>drvltr
        exit /b 0
    )
)
exit /b 1

:mount_imount
REM imount Mount
set "IEXE="
if "%IEXE%"=="" set "IEXE=%~dp0imount.exe"
if exist "%IEXE%" (
    "%IEXE%" "%DISCIMAGE%" 2>> "%ERROR_LOG%"
    if errorlevel 0 (
        for /f %%a in (drvltr) do (
            if "%%a" NEQ "" echo 3%%a>drvltr
        )
        if not exist drvltr echo 3>drvltr
        exit /b 0
    )
)
exit /b 1

:mount_imount_letter
set "IEXE="
if "%IEXE%"=="" set "IEXE=%~dp0imount.exe"
if exist "%IEXE%" (
    "%IEXE%" "%DISCIMAGE%" "%DRIVELETTER%" 2>> "%ERROR_LOG%"
    if errorlevel 0 (
        echo 3%DRIVELETTER%>drvltr
        exit /b 0
    )
)
exit /b 1

REM ============================================
REM END OF SCRIPT
REM ============================================
:eof
endlocal
exit /b
