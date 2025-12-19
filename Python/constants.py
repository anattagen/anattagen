import os
from enum import IntEnum

# --- Core Paths ---

# The absolute path to the 'Python' directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# The absolute path to the project's root directory (one level above 'Python')
APP_ROOT_DIR = os.path.dirname(SCRIPT_DIR)

# --- Binaries ---
SHORTCUT_EXE_PATH = os.path.join(APP_ROOT_DIR, "bin", "Shortcut.exe")

# --- Template Files ---
LAUNCHER_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "cmdtemplate.set")

# AntimicroX templates
AX_GAME_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "ax_GameTemplate.set")
AX_DESK_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "ax_DeskTemplate.set")
AX_TRIGGER_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "ax_Trigger.set")
AX_KBM_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "ax_KBM_Template.set")

# Keysticks templates
KS_GAME_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "ks_Game.Template")
KS_DESK_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "ks_Desk.Template")
KS_BLANK_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "ks_Blank.Template")
KS_TRIGGER_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "ks_Trigger.set")

# Legacy aliases
JOYSTICK_TEMPLATE_PATH = AX_GAME_TEMPLATE_PATH
DESKTOP_TEMPLATE_PATH = AX_DESK_TEMPLATE_PATH
TRIGGERS_TEMPLATE_PATH = AX_TRIGGER_TEMPLATE_PATH
KBM_TEMPLATE_PATH = AX_KBM_TEMPLATE_PATH

JOYSTICK_ICON_PATH = os.path.join(SCRIPT_DIR, "Joystick.ico")

# --- Configuration Files (.set) ---
RELEASE_GROUPS_SET = os.path.join(SCRIPT_DIR, "release_groups.set")
FOLDER_EXCLUDE_SET = os.path.join(SCRIPT_DIR, "folder_exclude.set")
EXCLUDE_EXE_SET = os.path.join(SCRIPT_DIR, "exclude_exe.set")
DEMOTED_SET = os.path.join(SCRIPT_DIR, "demoted.set")
FOLDER_DEMOTED_SET = os.path.join(SCRIPT_DIR, "folder_demoted.set")
REPOS_SET = os.path.join(SCRIPT_DIR, "repos.set")

# --- Cache & Index Files ---
APP_LOG_FILE = os.path.join(SCRIPT_DIR, 'app.log')
STEAM_JSON_FILE = os.path.join(APP_ROOT_DIR, "steam.json")
CURRENT_INDEX_FILE = os.path.join(APP_ROOT_DIR, "current.index")

# --- Editor Table Column Mapping ---

class EditorColumn(IntEnum):
    """Maps editor table column names to their integer indices."""
    INCLUDE = 0
    EXECUTABLE = 1
    DIRECTORY = 2
    STEAM_TITLE = 3
    NAME_OVERRIDE = 4
    OPTIONS = 5
    ARGUMENTS = 6
    STEAM_ID = 7
    P1_PROFILE = 8
    P2_PROFILE = 9
    DESKTOP_CTRL = 10
    GAME_MONITOR_CFG = 11
    DESKTOP_MONITOR_CFG = 12
    POST1 = 13
    POST2 = 14
    POST3 = 15
    PRE1 = 16
    PRE2 = 17
    PRE3 = 18
    JUST_AFTER = 19
    JUST_BEFORE = 20
    BORDERLESS = 21
    AS_ADMIN = 22
    NO_TB = 23