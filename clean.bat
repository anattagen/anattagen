for /f "delims=" %%a in ('dir /b/ad/s "*__pycache__"') do rmdir /s/q "%%~a"
rmdir /s/q "Launchers"
rmdir /s/q "Profiles"

