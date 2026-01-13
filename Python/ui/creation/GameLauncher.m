/*
 * GameLauncher.m
 *
 * A lightweight Objective-C port of the Python Game Launcher.
 * Features:
 * - INI Configuration Parsing
 * - Pre/Post Launch Sequence Execution
 * - Global Hotkey (Cmd+Opt+Esc) for Menu
 * - Game Controller Navigation support
 * - Failure suppression and file logging
 *
 * Compile with:
 * macOS: clang -fobjc-arc -framework Cocoa -framework GameController -o GameLauncher GameLauncher.m
 * Windows (GNUStep): clang `gnustep-config --objc-flags` `gnustep-config --base-libs --gui-libs` -lxinput -o GameLauncher.exe GameLauncher.m
 */

#ifdef GNUSTEP
#import <Foundation/Foundation.h>
#import <AppKit/AppKit.h>
#import <windows.h>
#import <xinput.h>
// Link with -lgnustep-base -lgnustep-gui -lxinput
#else
#import <Cocoa/Cocoa.h>
#import <GameController/GameController.h>
#endif

// --- Logging Subsystem ---

@interface Logger : NSObject
@property (strong) NSString *logPath;
@property (strong) NSFileHandle *fileHandle;
+ (instancetype)shared;
- (void)setup;
- (void)log:(NSString *)format, ...;
- (void)openLogViewer;
@end

@implementation Logger
+ (instancetype)shared {
    static Logger *shared = nil;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{ shared = [[Logger alloc] init]; });
    return shared;
}

- (void)setup {
    NSString *docDir = [NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES) firstObject];
    self.logPath = [docDir stringByAppendingPathComponent:@"GameLauncher.log"];
    
    // Create file if not exists
    if (![[NSFileManager defaultManager] fileExistsAtPath:self.logPath]) {
        [@"" writeToFile:self.logPath atomically:YES encoding:NSUTF8StringEncoding error:nil];
    }
    
    self.fileHandle = [NSFileHandle fileHandleForWritingAtPath:self.logPath];
    [self.fileHandle seekToEndOfFile];
    
    // Redirect stderr to this file
    freopen([self.logPath fileSystemRepresentation], "a+", stderr);
}

- (void)log:(NSString *)format, ... {
    va_list args;
    va_start(args, format);
    NSString *msg = [[NSString alloc] initWithFormat:format arguments:args];
    va_end(args);
    
    NSString *timestamped = [NSString stringWithFormat:@"[%@] %@\n", [NSDate date], msg];
    NSData *data = [timestamped dataUsingEncoding:NSUTF8StringEncoding];
    
    @try {
        [self.fileHandle writeData:data];
    } @catch (NSException *e) {
        // Suppress logging failure
    }
    
    // Also print to stdout for debug
    printf("%s", [timestamped UTF8String]);
}

- (void)openLogViewer {
    [[NSWorkspace sharedWorkspace] openFile:self.logPath];
}
@end

// --- Configuration Parser ---

@interface ConfigParser : NSObject
+ (NSDictionary *)parseINI:(NSString *)path;
@end

@implementation ConfigParser
+ (NSDictionary *)parseINI:(NSString *)path {
    NSMutableDictionary *config = [NSMutableDictionary dictionary];
    NSString *content = [NSString stringWithContentsOfFile:path encoding:NSUTF8StringEncoding error:nil];
    if (!content) return config;
    
    NSArray *lines = [content componentsSeparatedByString:@"\n"];
    NSString *currentSection = @"Global";
    
    for (NSString *line in lines) {
        NSString *trimmed = [line stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
        if ([trimmed length] == 0 || [trimmed hasPrefix:@";"] || [trimmed hasPrefix:@"#"]) continue;
        
        if ([trimmed hasPrefix:@"["] && [trimmed hasSuffix:@"]"]) {
            currentSection = [trimmed substringWithRange:NSMakeRange(1, [trimmed length] - 2)];
            if (!config[currentSection]) config[currentSection] = [NSMutableDictionary dictionary];
            continue;
        }
        
        NSArray *parts = [trimmed componentsSeparatedByString:@"="];
        if ([parts count] >= 2) {
            NSString *key = [parts[0] stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceCharacterSet]];
            NSString *val = [[parts subarrayWithRange:NSMakeRange(1, parts.count-1)] componentsJoinedByString:@"="];
            val = [val stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceCharacterSet]];
            
            if (!config[currentSection]) config[currentSection] = [NSMutableDictionary dictionary];
            config[currentSection][key] = val;
        }
    }
    return config;
}
@end

// --- Modal Dialog Window ---

@interface ModalOverlay : NSWindow
@end

@implementation ModalOverlay
- (BOOL)canBecomeKeyWindow { return YES; }
- (BOOL)canBecomeMainWindow { return YES; }
@end

// --- Main Application Controller ---

@interface AppDelegate : NSObject <NSApplicationDelegate>
@property (strong) NSDictionary *config;
@property (strong) NSTask *gameTask;
@property (strong) ModalOverlay *overlayWindow;
@property (strong) NSTextField *statusLabel;
@property (assign) BOOL isMenuVisible;
@property (strong) NSStatusItem *statusItem;
#ifdef GNUSTEP
@property (strong) NSTimer *inputTimer;
@property (assign) WORD lastButtonState;
#endif
@end

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)aNotification {
    [[Logger shared] setup];
    [[Logger shared] log:@"Launcher started."];
    
    // Load Config
    NSString *iniPath = @"Game.ini"; // Assumes Game.ini is in CWD
    if (![[NSFileManager defaultManager] fileExistsAtPath:iniPath]) {
        // Fallback to bundle resource or home dir for testing
        iniPath = [@"~/Documents/Game.ini" stringByExpandingTildeInPath];
    }
    
    self.config = [ConfigParser parseINI:iniPath];
    [[Logger shared] log:@"Config loaded from %@", iniPath];
    
    // Setup System Tray
    [self setupSystemTray];
    
    // Setup Controller Monitoring
    [self setupControllerSupport];
    
#ifndef GNUSTEP
    // Setup Global Hotkey (Cmd+Opt+Esc for demo purposes)
    [NSEvent addGlobalMonitorForEventsMatchingMask:NSEventMaskKeyDown handler:^(NSEvent *event) {
        if (([event modifierFlags] & NSEventModifierFlagCommand) &&
            ([event modifierFlags] & NSEventModifierFlagOption) &&
            [event keyCode] == 53) { // Esc
            [self toggleMenu];
        }
    }];
#endif
    
    // Start Sequence
    [self executeLaunchSequence];
}

- (void)setupSystemTray {
    self.statusItem = [[NSStatusBar systemStatusBar] statusItemWithLength:NSVariableStatusItemLength];
    
#ifdef GNUSTEP
    [self.statusItem setTitle:@"GL"];
    [self.statusItem setHighlightMode:YES];
#else
    self.statusItem.button.title = @"GL";
#endif

    NSMenu *menu = [[NSMenu alloc] initWithTitle:@"GameLauncher"];
    [menu addItemWithTitle:@"Show Menu" action:@selector(toggleMenu) keyEquivalent:@"m"];
    [menu addItem:[NSMenuItem separatorItem]];
    [menu addItemWithTitle:@"Quit" action:@selector(quitFromMenu:) keyEquivalent:@"q"];
    self.statusItem.menu = menu;
}

- (void)executeLaunchSequence {
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        // 1. Pre-Launch
        [self runSequence:@"PreLaunch"];
        
        // 2. Launch Game
        dispatch_async(dispatch_get_main_queue(), ^{
            [self launchGame];
        });
    });
}

- (void)runSequence:(NSString *)sectionName {
    NSDictionary *section = self.config[sectionName];
    if (!section) return;
    
    // Simple implementation: iterates App1, App2, App3 keys
    for (int i = 1; i <= 3; i++) {
        NSString *appKey = [NSString stringWithFormat:@"App%d", i];
        NSString *waitKey = [NSString stringWithFormat:@"App%dWait", i];
        
        NSString *appPath = section[appKey];
        BOOL wait = [section[waitKey] boolValue];
        
        if (appPath && [appPath length] > 0) {
            [self runProcess:appPath arguments:@[] wait:wait];
        }
    }
}

- (void)launchGame {
    NSString *gameExe = self.config[@"Game"][@"Executable"];
    NSString *gameDir = self.config[@"Game"][@"Directory"];
    
    if (!gameExe) {
        [[Logger shared] log:@"Error: No Game Executable defined."];
        [self terminateApp];
        return;
    }
    
    [[Logger shared] log:@"Launching Game: %@", gameExe];
    
    self.gameTask = [[NSTask alloc] init];
    self.gameTask.launchPath = gameExe;
    if (gameDir) self.gameTask.currentDirectoryPath = gameDir;
    
    self.gameTask.terminationHandler = ^(NSTask *task) {
        [[Logger shared] log:@"Game terminated. Running PostLaunch..."];
        [self runSequence:@"PostLaunch"];
        dispatch_async(dispatch_get_main_queue(), ^{
            [self terminateApp];
        });
    };
    
    @try {
        [self.gameTask launch];
    } @catch (NSException *exception) {
        [[Logger shared] log:@"Failed to launch game: %@", exception.reason];
        [self terminateApp];
    }
}

- (void)runProcess:(NSString *)path arguments:(NSArray *)args wait:(BOOL)wait {
    [[Logger shared] log:@"Running process: %@ (Wait: %@)", path, wait ? @"YES" : @"NO"];
    
    NSTask *task = [[NSTask alloc] init];
    task.launchPath = path;
    task.arguments = args;
    
    @try {
        [task launch];
        if (wait) {
            [task waitUntilExit];
        }
    } @catch (NSException *exception) {
        [[Logger shared] log:@"Failed to run process %@: %@", path, exception.reason];
    }
}

- (void)terminateApp {
    [[Logger shared] log:@"Launcher exiting."];
    [[Logger shared] openLogViewer];
    [NSApp terminate:nil];
}

- (void)quitFromMenu:(id)sender {
    [self terminateApp];
}

// --- Menu / Overlay Logic ---

- (void)toggleMenu {
    if (self.isMenuVisible) {
        [self.overlayWindow close];
        self.overlayWindow = nil;
        self.isMenuVisible = NO;
    } else {
        [self showOverlay];
    }
}

- (void)showOverlay {
    NSRect screenRect = [[NSScreen mainScreen] frame];
    NSRect windowRect = NSMakeRect((screenRect.size.width - 400)/2, (screenRect.size.height - 200)/2, 400, 200);
    
    self.overlayWindow = [[ModalOverlay alloc] initWithContentRect:windowRect
                                                       styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskFullSizeContentView
                                                         backing:NSBackingStoreBuffered
                                                           defer:NO];
    [self.overlayWindow setTitle:@"Game Launcher Menu"];
    [self.overlayWindow setLevel:NSFloatingWindowLevel];
    [self.overlayWindow setBackgroundColor:[NSColor colorWithCalibratedWhite:0.1 alpha:0.9]];
    
    NSTextField *label = [NSTextField labelWithString:@"Paused / Menu"];
    [label setFont:[NSFont systemFontOfSize:24 weight:NSFontWeightBold]];
    [label setTextColor:[NSColor whiteColor]];
    [label setFrame:NSMakeRect(0, 140, 400, 40)];
    [label setAlignment:NSTextAlignmentCenter];
    [[self.overlayWindow contentView] addSubview:label];
    
    NSTextField *instr = [NSTextField labelWithString:@"Press (A) to Resume\nPress (B) to Kill Game"];
    [instr setTextColor:[NSColor lightGrayColor]];
    [instr setFrame:NSMakeRect(0, 60, 400, 60)];
    [instr setAlignment:NSTextAlignmentCenter];
    [[self.overlayWindow contentView] addSubview:instr];
    
    [self.overlayWindow makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];
    self.isMenuVisible = YES;
}

// --- Controller Support ---

- (void)setupControllerSupport {
#ifdef GNUSTEP
    [[Logger shared] log:@"Starting Windows Input Polling (XInput + Hotkeys)..."];
    // Poll every 100ms for Controller and Hotkeys
    self.inputTimer = [NSTimer scheduledTimerWithTimeInterval:0.1 target:self selector:@selector(pollWindowsInput) userInfo:nil repeats:YES];
#else
    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(controllerDidConnect:)
                                                 name:GCControllerDidConnectNotification
                                               object:nil];
    
    [GCController startWirelessControllerDiscoveryWithCompletionHandler:^{
        [[Logger shared] log:@"Controller discovery complete."];
    }];
#endif
}

#ifdef GNUSTEP
- (void)pollWindowsInput {
    // 1. Global Hotkey Check (Ctrl + Alt + Esc)
    // Note: GetAsyncKeyState returns a SHORT where the MSB indicates pressed state.
    BOOL ctrl = (GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0;
    BOOL alt = (GetAsyncKeyState(VK_MENU) & 0x8000) != 0;
    BOOL esc = (GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0;
    
    static BOOL hotkeyWasPressed = NO;
    if (ctrl && alt && esc) {
        if (!hotkeyWasPressed) {
            hotkeyWasPressed = YES;
            [self toggleMenu];
        }
    } else {
        hotkeyWasPressed = NO;
    }

    // 2. XInput Controller Check
    XINPUT_STATE state;
    ZeroMemory(&state, sizeof(XINPUT_STATE));
    
    // Check Controller 0
    if (XInputGetState(0, &state) == ERROR_SUCCESS) {
        WORD buttons = state.Gamepad.wButtons;
        WORD changed = buttons ^ self.lastButtonState;
        
        // Button A (Resume)
        if ((changed & XINPUT_GAMEPAD_A) && (buttons & XINPUT_GAMEPAD_A)) {
            if (self.isMenuVisible) [self toggleMenu];
        }
        
        // Button B (Kill)
        if ((changed & XINPUT_GAMEPAD_B) && (buttons & XINPUT_GAMEPAD_B)) {
            if (self.isMenuVisible) {
                [[Logger shared] log:@"User requested game termination via controller."];
                if (self.gameTask && [self.gameTask isRunning]) {
                    [self.gameTask terminate];
                }
                [self toggleMenu];
            }
        }
        
        // Start/Menu Button (Toggle)
        if ((changed & XINPUT_GAMEPAD_START) && (buttons & XINPUT_GAMEPAD_START)) {
            [self toggleMenu];
        }
        
        self.lastButtonState = buttons;
    }
}
#else
- (void)controllerDidConnect:(NSNotification *)note {
    GCController *controller = note.object;
    [[Logger shared] log:@"Controller connected: %@", controller.vendorName];
    
    // Bind buttons
    if (controller.extendedGamepad) {
        controller.extendedGamepad.buttonA.valueChangedHandler = ^(GCControllerButtonInput *button, float value, BOOL pressed) {
            if (pressed && self.isMenuVisible) {
                dispatch_async(dispatch_get_main_queue(), ^{
                    [self toggleMenu]; // Resume
                });
            }
        };
        
        controller.extendedGamepad.buttonB.valueChangedHandler = ^(GCControllerButtonInput *button, float value, BOOL pressed) {
            if (pressed && self.isMenuVisible) {
                dispatch_async(dispatch_get_main_queue(), ^{
                    [[Logger shared] log:@"User requested game termination via controller."];
                    if (self.gameTask && [self.gameTask isRunning]) {
                        [self.gameTask terminate];
                    }
                    [self toggleMenu];
                });
            }
        };
        
        controller.extendedGamepad.buttonMenu.valueChangedHandler = ^(GCControllerButtonInput *button, float value, BOOL pressed) {
            if (pressed) {
                dispatch_async(dispatch_get_main_queue(), ^{
                    [self toggleMenu];
                });
            }
        };
    }
}
#endif

@end

// --- Main Entry Point ---

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        NSApplication *app = [NSApplication sharedApplication];
        AppDelegate *delegate = [[AppDelegate alloc] init];
        [app setDelegate:delegate];
        [app setActivationPolicy:NSApplicationActivationPolicyRegular];
        [app run];
    }
    return 0;
}