REM @echo off
setlocal enabledelayedexpansion

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
if "%VSCMD%" NEQ "" goto VSCMD
if defined BUILD_TOOLS_ROOT (
	for /f "delims=;" %%j in ('echo "%BUILD_TOOLS_ROOT%"') do (
		for /f "delims=" %%a in ('dir /b/a-d/s "%%~j*vcvars64.bat"') do (
			set VSCMD_VER=%%~a
			break
		)
if "%VSCMD_VER%" NEQ ""	break
	)
)
:VSCMD
call "%VSCMD_VER%" || exit /b 1
set CLFLAGS=/std:c11 /O2 /W4 /nologo /D_CRT_SECURE_NO_WARNINGS
set LIBS=user32.lib shell32.lib shlwapi.lib ole32.lib psapi.lib advapi32.lib

cl %CLFLAGS% launcher.c inih\ini.c %LIBS%

if errorlevel 1 (
    echo Build failed
    exit /b 1
)

echo Build succeeded

move /y Launcher.exe ..\..\bin\Launcher.exe
