@echo off
REM nativemount.cmd.set - Native Windows Mount Template
set "DISCIMAGE=%~1"
if "%DISCIMAGE%"=="" goto :eof
if exist "drvltr" del /q "drvltr"

powershell -Command "$m = Mount-DiskImage -ImagePath '%DISCIMAGE%' -PassThru; if ($m) { ($m | Get-Volume).DriveLetter | Out-File -FilePath 'drvltr' -Encoding ASCII -NoNewline }"
