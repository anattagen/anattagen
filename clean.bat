for /f "delims=" %%a in ('dir /b/ad "*\__pycache"') do rmdir /s/q "%%~a"
rmdir /s/q "Launchers"
rmdir /s/q "Profiles"

