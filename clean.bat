
for /f "delims=" %%a in ('dir /b/ad/s "__pycache__"') do rmdir /s/q "%%~a"
for /f "delims=" %%a in ('dir /b/a ""bin\*""') do attrib +h "bin\%%~a"

attrib -h bin\7z.exe
attrib -h bin\Launcher.bat
attrib -h bin\Launcher.sh
attrib -h bin\Shortcut.exe
attrib -h bin\Shortcut.txt
attrib -h bin\Launcher.exe
attrib -h bin\Launcher.python.exe
