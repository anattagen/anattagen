/**
 * launcher.c - Game Launcher
 *
 * A C port of the Python game launcher script. This scaffold provides the
 * basic structure and function stubs needed for the port.
 *
 * Compilation (using MinGW-w64):
 * gcc -o launcher.exe launcher.c inih/ini.c -luser32 -lshlwapi -lole32 -Wall
 *
 * Dependencies:
 * - inih library (https://github.com/benhoyt/inih) for INI parsing.
 *   Place ini.h and ini.c in an 'inih' subdirectory.
 */

#define _WIN32_WINNT 0x0600 // Required for some modern Windows API functions
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <tlhelp32.h> // For process snapshots
#include <shlwapi.h>   // For PathRemoveFileSpecA

// Include the inih library header
#include "inih/ini.h"

#pragma comment(lib, "user32.lib")
#pragma comment(lib, "shlwapi.lib")
#pragma comment(lib, "ole32.lib")

// --- Global Configuration Struct ---
typedef struct {
    // [Game]
    char executable[MAX_PATH];
    char directory[MAX_PATH];
    char name[256];

    // [Paths]
    char controller_mapper_app[MAX_PATH];
    char borderless_windowing_app[MAX_PATH];
    char multimonitor_tool[MAX_PATH];
    char player1_profile[MAX_PATH];
    char player2_profile[MAX_PATH];
    char mm_game_config[MAX_PATH];
    char mm_desktop_config[MAX_PATH];

    // [Options]
    int run_as_admin;
    int hide_taskbar;
    char borderless[4];
    int use_kill_list;
    int terminate_borderless_on_exit;

    // [PreLaunch]
    char pre_launch_app_1[MAX_PATH];
    int pre_launch_app_1_wait;
    // ... add other pre/post apps

    // [Sequences]
    char launch_sequence[512];
    char exit_sequence[512];

} GameConfiguration;

// --- Global State Variables ---
GameConfiguration G_CONFIG;
PROCESS_INFORMATION G_GAME_PROCESS_INFO;
// ... Add other handles for tracked processes


// --- Function Prototypes ---
void show_message(const char* message);
static int config_handler(void* user, const char* section, const char* name, const char* value);
int load_configuration(const char* ini_path);
void execute_sequence(const char* sequence_str, int is_exit_sequence);
void execute_action(const char* action, int is_exit_sequence);
void run_game_process();
BOOL run_process(const char* command, const char* working_dir, BOOL wait, PROCESS_INFORMATION* pi);
void terminate_process_tree(DWORD pid);
void set_taskbar_visibility(BOOL show);

// Action function prototypes
void action_run_controller_mapper();
void action_kill_controller_mapper();
void action_hide_taskbar();
void action_show_taskbar();
// ... other action prototypes


// --- Main Entry Point ---
int main(int argc, char* argv[]) {
    if (argc < 2) {
        show_message("Usage: launcher.exe <path_to_shortcut>");
        Sleep(2000);
        return 1;
    }

    const char* shortcut_path = argv[1];
    char ini_path[MAX_PATH];
    
    // Determine the path to Game.ini based on the shortcut path
    strncpy(ini_path, shortcut_path, MAX_PATH - 1);
    PathRemoveFileSpecA(ini_path); // from shlwapi.h
    PathAppendA(ini_path, "Game.ini");

    show_message("Launcher starting...");

    // Initialize the configuration struct with zeros
    memset(&G_CONFIG, 0, sizeof(GameConfiguration));
    memset(&G_GAME_PROCESS_INFO, 0, sizeof(PROCESS_INFORMATION));

    // Load configuration
    if (load_configuration(ini_path) != 0) {
        show_message("Failed to load configuration.");
        Sleep(2000);
        return 1;
    }

    // Execute launch sequence
    execute_sequence(G_CONFIG.launch_sequence, 0);

    // Run the game
    run_game_process();

    // Wait for the game process to exit
    if (G_GAME_PROCESS_INFO.hProcess != NULL) {
        WaitForSingleObject(G_GAME_PROCESS_INFO.hProcess, INFINITE);
        CloseHandle(G_GAME_PROCESS_INFO.hProcess);
        CloseHandle(G_GAME_PROCESS_INFO.hThread);
    }

    // Execute exit sequence
    execute_sequence(G_CONFIG.exit_sequence, 1);

    // Final cleanup
    // ... (e.g., ensure taskbar is visible, kill any remaining tracked processes)
    show_message("Launcher finished.");
    return 0;
}

// --- Function Implementations (Stubs) ---

void show_message(const char* message) {
    // For now, just print to console.
    // Could be replaced with a simple GUI tooltip window using CreateWindowEx.
    printf("[Launcher] %s\n", message);
}

// INI parsing handler for the inih library
static int config_handler(void* user, const char* section, const char* name, const char* value) {
    GameConfiguration* pConfig = (GameConfiguration*)user;
    
    // Macro to simplify string comparisons
    #define MATCH(s, n) strcmp(section, s) == 0 && strcmp(name, n) == 0

    if (MATCH("Game", "executable")) {
        strncpy(pConfig->executable, value, sizeof(pConfig->executable) - 1);
    } else if (MATCH("Game", "directory")) {
        strncpy(pConfig->directory, value, sizeof(pConfig->directory) - 1);
    } else if (MATCH("Options", "hidetaskbar")) {
        pConfig->hide_taskbar = (strcmp(value, "true") == 0);
    } else if (MATCH("Sequences", "launchsequence")) {
        strncpy(pConfig->launch_sequence, value, sizeof(pConfig->launch_sequence) - 1);
    } else if (MATCH("Sequences", "exitsequence")) {
        strncpy(pConfig->exit_sequence, value, sizeof(pConfig->exit_sequence) - 1);
    }
    // ... Add all other configuration options here using else if ...
    
    else {
        return 0; // unknown section/name, error
    }
    return 1;
}

int load_configuration(const char* ini_path) {
    // This uses the inih library.
    // Download from https://github.com/benhoyt/inih
    // Add ini.h and ini.c to your project in an 'inih' subfolder.
    if (ini_parse(ini_path, config_handler, &G_CONFIG) < 0) {
        show_message("Can't load 'Game.ini'");
        return 1;
    }
    show_message("Configuration loaded successfully.");
    return 0;
}

void execute_sequence(const char* sequence_str, int is_exit_sequence) {
    // Create a mutable copy of the sequence string for strtok
    char* sequence_copy = _strdup(sequence_str);
    if (sequence_copy == NULL) return;

    char* context = NULL;
    char* token = strtok_s(sequence_copy, ",", &context);

    while (token != NULL) {
        // Trim whitespace (if any)
        while (*token == ' ') token++;
        // Execute the action
        execute_action(token, is_exit_sequence);
        token = strtok_s(NULL, ",", &context);
    }

    free(sequence_copy);
}

void execute_action(const char* action, int is_exit_sequence) {
    // This will be a large if-else-if block to map action strings to function calls.
    show_message(action);
    if (strcmp(action, "No-TB") == 0) {
        if (!is_exit_sequence) set_taskbar_visibility(FALSE);
    } else if (strcmp(action, "Taskbar") == 0) {
        if (is_exit_sequence) set_taskbar_visibility(TRUE);
    }
    // ... Add other actions here ...
}

void run_game_process() {
    show_message("Running game...");
    run_process(G_CONFIG.executable, G_CONFIG.directory, FALSE, &G_GAME_PROCESS_INFO);
}

BOOL run_process(const char* command, const char* working_dir, BOOL wait, PROCESS_INFORMATION* pi) {
    STARTUPINFOA si;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(pi, sizeof(*pi));

    // CreateProcess needs a mutable command line string
    char* cmd_mutable = _strdup(command);
    if (cmd_mutable == NULL) return FALSE;

    BOOL success = CreateProcessA(NULL, cmd_mutable, NULL, NULL, FALSE, 0, NULL, working_dir, &si, pi);
    free(cmd_mutable);

    if (success && wait) {
        WaitForSingleObject(pi->hProcess, INFINITE);
    }
    // Note: The caller is responsible for calling CloseHandle on pi->hProcess and pi->hThread
    return success;
}

void terminate_process_tree(DWORD pid) {
    // Implementation would use CreateToolhelp32Snapshot, Process32First,
    // Process32Next to find child processes recursively and terminate them.
    // Then terminate the parent process with OpenProcess and TerminateProcess.
}

void set_taskbar_visibility(BOOL show) {
    HWND taskbar = FindWindowA("Shell_TrayWnd", NULL);
    if (taskbar) {
        ShowWindow(taskbar, show ? SW_SHOW : SW_HIDE);
    }
}