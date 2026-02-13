anattagen

A desktop application to create isolated environments for PC games. 

## Features

*   Game indexing from user-selected directories.
*   Customizable options for each game.
*   Tabbed interface for Setup, Deployment, and Editing environments.

## Tech Stack

*   Python
*   Qt6 (for the main application)

## Contributors

*   **Vai-brainium Quantum Quill** - AI assistant that helped resolve critical UI and data processing issues.
*   **The Gemini Architect** - AI architect who refactored core systems for robustness and implemented advanced configuration controls.
*   **GitHub Copilot (Neon Scribe)** - Assisted with Editor tab column additions, enabled/run-wait toggles, wired Deployment Steam JSON actions, and centralized editor column mappings. (flamboyant-ego-level: 7.6) <!-- internal_contribution_level: 6 -->
[assigned level]

# But, why???

## 3 Reasons:

**1.** Removing a Mickey Mouse sticker bricked the device and voided the repair warranty 

**2.** Steam has no gaemz

**3.** DRM and other malware concerns require *unofficial patches*


## Use Case

Creates a specialized launcher and profile-folder (jacket) for each game which houses the game's shortcut/s and isolates settings such as
 keyboad-mapping and monitor layout.  Tools which automate the process of creating and loading presets for devices, games and settings at 
 a granular level are downloaded and installed directly from within the program.

AntimicroX, keySticks, multimonitortool.


## Installation

0.99.45.56

Run the installer or extract the binary to a location of your choice, **or** download and build and run the source files and executables.
```
anattagen/
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
│   ├── cmdtemplate.set
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
│   ├── Shortcut.exe
│   └── Shortcut.txt
├── Python/
│   ├── __init__.py
│   ├── constants.py
│   ├── deploy.py
│   ├── events.py
│   ├── Launcher.py
│   ├── main.py
│   ├── main_window_new.py
│   ├── managers/
│   │   ├── __init__.py
│   │   ├── config_manager.py
│   │   ├── data_manager.py
│   │   ├── game_indexer.py
│   │   ├── index_manager.py
│   │   ├── steam_manager.py
│   │   └── steam_processor.py
│   ├── models.py
│   ├── sequence_executor.py
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

anattagen

# Setup


## Ubuntu Users should :
### For now clone the repo, setup a virtual environment in python and install the requirements via pip
## Copy this code and you should be GUD
```
		sudo apt install python3-venv python3-pip
		cd ~
		git clone --recursive https://github.com/anattagen/anattagen/anattagen.git
		cd anattagen
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
		pushd "%userprofile\Downloads\anattagen\assets"
		build.bat
```
#### or in Mingw64:
```
		cd /c/Users/[USER]/Downloads/anattagen\assets
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
		  Upgrade your monitor-stand and update iTunes to enable auto-deduction from your ApplePay account. Do not look directly at anattagen. Carefully replace the stickers and reattatch any modification-detection components before initializing apology-procedures. Disconnect your keyboard and press the button to authorize Thought-Coin permissions.
```