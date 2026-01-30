@echo off
setlocal

if not defined VSCMD_VER (
    call "%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" || exit /b 1
)

set CLFLAGS=/std:c11 /O2 /W4 /nologo /D_CRT_SECURE_NO_WARNINGS
set LIBS=user32.lib shell32.lib shlwapi.lib ole32.lib psapi.lib

cl %CLFLAGS% launcher.c inih\ini.c %LIBS%

if errorlevel 1 (
    echo Build failed
    exit /b 1
)

echo Build succeeded

rename ..\..\bin\Launcher.exe Launcher.old||move /y ..\..\bin\Launcher.exe ..\..\bin\Launcher.old
move Launcher.exe ..\..\bin\Launcher.exe
