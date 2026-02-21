[RJ_PROJ]

A desktop application to create isolated environments for PC games. 

## Features

*   Game indexing from user-selected directories.
*   Customizable options for each game.
*   Tabbed interface for Setup, Deployment, and Editing environments.
*   **Plugin-based architecture** for extensible tool integration.
*   **Cloud backup support** with Rclone and Ludusavi integration.
*   Automatic save game synchronization to cloud storage.
*   Controller mapping with AntiMicroX and KeySticks.
*   Borderless windowing and multi-monitor configuration.
*   Pre/post launch script execution.
*   Disc image mounting support.

## Tech Stack

*   Python
*   Qt6 (for the main application)

## Contributors

*   **Vai-brainium Quantum Quill** - AI assistant that helped resolve critical UI and data processing issues.
*   **The Gemini Architect** - AI architect who refactored core systems for robustness and implemented advanced configuration controls.
*   **GitHub Copilot (Neon Scribe)** - Assisted with Editor tab column additions, enabled/run-wait toggles, wired Deployment Steam JSON actions, and centralized editor column mappings.
*   **CodeForge Prime** - Crushed the PCGamingWiki API migration, merged disc mounting into native launcher code, brought the C launcher up to speed with Python, and surgically refactored combobox population logic to respect flyout menu items. No shortcuts, just solid engineering.

# But, why???

## 3 Reasons:

**1.** Removing a Mickey Mouse sticker bricked the device and voided the repair warranty 

**2.** Steam has no gaemz

**3.** DRM and other malware concerns require *unofficial patches*


## Use Case

Creates a specialized launcher and profile-folder (jacket) for each game which houses the game's shortcut/s and isolates settings such as
 keyboad-mapping and monitor layout.  Tools which automate the process of creating and loading presets for devices, games and settings at 
 a granular level are downloaded and installed directly from within the program.

AntimicroX, keySticks, multimonitortool,  borderless-gaming,  borderless ,  rclone,  ludusavi,  WinCDEmu,  OSFMount,  imgdrive


## Installation

[VERSION]

Run the installer or extract the binary to a location of your choice, **or** download and build and run the source files and executables.
```
[RJ_PROJ]/
├── assets/
│   ├── launcher/
│   │      ├── launcher.c
│   │      ├── Launcher.py.convert
│   │      ├── launcher_c_style.py
│   │      ├── compat.h
│   │      ├── inih/
│   │      │   ├── ini.c
│   │      │   └── ini.h
│   │      ├── build.sh
│   │      └── build.bat
│   ├── ax_DeskTemplate.set
│   ├── ax_GameTemplate.set
│   ├── ax_KBM_Template.set
│   ├── ax_Trigger.set
│   ├── combined.cmd.set
│   ├── combined.sh.set
│   ├── demoted.set
│   ├── exclude_exe.set
│   ├── folder_demoted.set
│   ├── folder_exclude.set
│   ├── governed_executables.set
│   ├── Joystick.ico
│   ├── killprocs.set
│   ├── ks_Blank.Template.set
│   ├── ks_Desk.Template.set
│   ├── ks_Game.Template.set
│   ├── ks_Trigger.set
│   ├── logo.PNG
│   ├── options_arguments.set
│   ├── release_groups.set
│   ├── repos.set
│   ├── splash.png
│   └── transformed_vars.set
├── bin/
│   ├── Launcher.exe
│   ├── Launcher.bat
│   ├── Launcher.sh
│   ├── Shortcut.exe
│   └── Shortcut.txt
├── Python/
│   ├── __init__.py
│   ├── constants.py
│   ├── deploy.py
│   ├── events.py
│   ├── Launcher.py
│   ├── main.py
│   ├── models.py
│   ├── main_window_new.py
│   ├── sequence_executor.py
│   ├── managers/
│   │   ├── __init__.py
│   │   ├── config_manager.py
│   │   ├── data_manager.py
│   │   ├── game_indexer.py
│   │   ├── index_manager.py
│   │   ├── steam_manager.py
│   │   └── steam_processor.py
│   └── ui/
│       ├── accordion.py
│       ├── creation/
│       │   ├── creation_controller.py
│       │   ├── file_propagator.py
│       │   └── joystick_profile_manager.py
│       ├── deployment_tab.py
│       ├── editor_tab.py
│       ├── game_indexer.py
│       ├── name_processor.py
│       ├── name_utils.py
│       ├── setup_tab.py
│       ├── steam_cache.py
│       ├── steam_utils.py
│       └── widgets.py
├── README.md
├── README.set
├── requirements.txt
├── requirements_win.txt
├── site/
│   ├── Arkhip_font.otf
│   ├── Hermit-Regular.otf
│   ├── img/
│   │   ├── Install.png
│   │   ├── key.png
│   │   ├── keymapper.png
│   │   ├── runas.png
│   │   ├── tip.png
│   │   └── Update.png
│   ├── index.html
│   ├── index.set
│   ├── key.ico
│   ├── NEW ACADEMY.woff
│   ├── TruenoLt.otf
│   └── YsabeauSC-Medium.otf
└── steam.json
```
# Documentation

## Quick Start

- **[TUTORIAL.md](TUTORIAL.md)** - Complete tutorial for creating game launchers
- **[QUICK_START_CLOUD_BACKUP.md](QUICK_START_CLOUD_BACKUP.md)** - Get cloud backup working in 5 minutes!

## Plugin System & Cloud Backup

The application now features a comprehensive plugin system with cloud backup support:

- **[PLUGIN_SYSTEM_SUMMARY.md](PLUGIN_SYSTEM_SUMMARY.md)** - Complete overview of the plugin architecture
- **[PLUGIN_QUICKSTART.md](PLUGIN_QUICKSTART.md)** - Quick reference for users and developers
- **[PLUGIN_CONFIGURATION_GUIDE.md](PLUGIN_CONFIGURATION_GUIDE.md)** - Detailed plugin configuration reference
- **[CLOUD_BACKUP_INTEGRATION.md](CLOUD_BACKUP_INTEGRATION.md)** - Cloud backup setup and configuration guide
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migrating from legacy to plugin-based system
- **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** - System architecture and data flow
- **[Game.ini.example](Game.ini.example)** - Complete configuration example

### Phase Documentation

- **[PLUGIN_SYSTEM_PHASE1.md](PLUGIN_SYSTEM_PHASE1.md)** - Foundation architecture
- **[PLUGIN_SYSTEM_PHASE2.md](PLUGIN_SYSTEM_PHASE2.md)** - Core implementation
- **[PLUGIN_SYSTEM_PHASE3.md](PLUGIN_SYSTEM_PHASE3.md)** - Integration & cloud backup
- **[PLUGIN_SYSTEM_PHASE4.md](PLUGIN_SYSTEM_PHASE4.md)** - Dependency injection, hot-reloading, marketplace
- **[PHASE3_COMPLETION_SUMMARY.md](PHASE3_COMPLETION_SUMMARY.md)** - Phase 3 completion report

[RJ_PROJ]

# Setup

## Ubuntu Users should :
### For now clone the repo, setup a virtual environment in python and install the requirements via pip
## Copy this code and you should be GUD
```
		sudo apt install python3-venv python3-pip
		cd ~
		git clone --recursive https://[GIT_SRC]/[RJ_PROJ].git
		cd [RJ_PROJ]
		python3 -m venv .venv
		source .venv/bin/activate
		python -m pip install -r requirements.txt
		python -m Python/main.py
```

win
## Windows 11 / winget users can copy/paste this to install python very quickly:
```
		winget install -e --id Python.Python.3.13 --scope machine
```
### Now you can clone or download the repo, and install the requirements via pip
```
		cd %userprofile%/Downloads
		git clone --recursive https://https://github.com/anattagen/anattagen/anattagen
		cd anattagen
		python -m pip install -r requirements_win.txt
		python -m Python\main.py
```
### To compile the launcher:
```
		cd assets
		sudo chmod +x
		build.sh --linux
```
### Windows open a dev console:
```
		pushd "%userprofile%\Downloads\[RJ_PROJ]\assets"
		build.bat
```
#### or in Mingw64:
```
		cd /c/Users/$USER/Downloads/[RJ_PROJ]/assets
		./build.sh --windows
```
### Build and Compile your own project:
#### Ubuntu/Linux:
```
	python Python/deploy.py
```
#### Windows:
```
	python Python\deploy.py
```
## Apple Mac Users
```
		  Update iTunes to enable auto-deduction from your ApplePay account. 
Upgrade your monitor-stand and do not look directly at anattagen. Carefully replace the stickers and reattatch any modification-detection components before initializing apology-procedures. Disconnect your keyboard and press the button to authorize Thought-Coin permissions.
```