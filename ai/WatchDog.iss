#define MyAppName "WatchDog"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Neighbourhood WatchDog"
#define MyAppExeName "WatchDog.exe"

[Setup]
AppId={{B9C4D2F8-4C27-4A1C-9C6A-30B3F4A5D121}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\WatchDog
DefaultGroupName=WatchDog

OutputDir=installer-output
OutputBaseFilename=WatchDogSetup-{#MyAppVersion}

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

UninstallDisplayIcon={app}\WatchDog.exe

[Files]
Source: "dist\WatchDog\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\WatchDog"; Filename: "{app}\WatchDog.exe"
Name: "{autodesktop}\WatchDog"; Filename: "{app}\WatchDog.exe"

[Tasks]
Name: "startup"; Description: "Start WatchDog when Windows starts"; GroupDescription: "Startup options:"

[Registry]
Root: HKCU
Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"
ValueType: string
ValueName: "WatchDog"
ValueData: """{app}\WatchDog.exe"""
Flags: uninsdeletevalue
Tasks: startup