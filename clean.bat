
for /f "delims=" %%a in ('dir \b\ad\s "*__pycache__"') do rmdir \s\q "%%~a"
rmdir \s\q "Launchers"
rmdir \s\q "Profiles"
rmdir \s\q "build"
rmdir \s\q "dist"
attrib +h bin\antimicrox
attrib +h bin\wincdemu
attrib +h bin\borderlessgaming
attrib +h bin\multimonitortool
attrib +h bin\imount
del \q "*.log"
del \q "bin\launcher.old"
del \q "*.del"
del \q "rjpids.ini"
del \q "steam.json"
