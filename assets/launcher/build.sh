#!/bin/sh
set -eu

MODE="auto"

if [ "${1:-}" = "--linux" ]; then
    MODE="linux"
elif [ "${1:-}" = "--windows" ]; then
    MODE="windows"
fi

# ---------- toolchain selection ----------

if [ "$MODE" = "windows" ]; then
    CC=${CC:-x86_64-w64-mingw32-gcc}
    OUT=launcher.exe
    LDFLAGS="-luser32 -lshlwapi -lole32 -lpsapi"
elif [ "$MODE" = "linux" ]; then
    CC=${CC:-gcc}
    OUT=launcher
    LDFLAGS=""
else
    # auto
    CC=${CC:-gcc}
    OUT=launcher
    LDFLAGS=""
fi

# ---------- flags (locked, reproducible) ----------

CFLAGS="
-std=c11
-O2
-Wall
-Wextra
-Wpedantic
-fno-omit-frame-pointer
-fno-ident
-ffile-prefix-map=$(pwd)=.
"

# ---------- build ----------

echo "Compiler : $CC"
echo "Output   : $OUT"

$CC $CFLAGS \
    launcher.c \
    inih/ini.c \
    -o $OUT \
    $LDFLAGS

echo "Built $OUT"
if [ "$MODE" = "windows" ]; then
    rm -rf ../../bin/launcher.old
    mv ../../bin/launcher.exe ../../bin/launcher.old
    mv launcher.exe ../../bin/launcher.exe
elif [ "$MODE" = "linux" ]; then
    rm -rf ../../bin/launcher.old
    mv ../../bin/launcher ../../bin/launcher.old
    mv launcher ../../bin/launcher
else
    # auto
    echo "Move the launcher into the /../bin directory"
fi