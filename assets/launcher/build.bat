REM @echo off
setlocal

if not defined VSCMD_VER (
	for /f "delims=" %%a in ('dir /b/a-d/s "%programfiles%\Microsoft Visual Studio\*vcvars64.bat"') do (
		set VSCMD_VER=%%~a
		break
	)
)
if not defined VSCMD_VER (
	for /f "delims=" %%a in ('dir /b/a-d/s "%programfiles% (x86)\Microsoft Visual Studio\*vcvars64.bat"') do (
		set VSCMD_VER=%%~a
		break
	)
					
)
    call "%VSCMD_VER%" || exit /b 1
set CLFLAGS=/std:c11 /O2 /W4 /nologo /D_CRT_SECURE_NO_WARNINGS
set LIBS=user32.lib shell32.lib shlwapi.lib ole32.lib psapi.lib

cl %CLFLAGS% launcher.c inih\ini.c %LIBS%

if errorlevel 1 (
    echo Build failed
    exit /b 1
)

echo Build succeeded

move /y Launcher.exe ..\..\bin\Launcher.exe
