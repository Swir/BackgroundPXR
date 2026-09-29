#define MyAppName "BackgroundPXR"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#ifndef MySourceDir
  #define MySourceDir "..\dist\BackgroundPXR"
#endif

[Setup]
AppId={{9A2D5C73-5A34-4C70-9FA6-DA6A80A9099A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=Swir
AppPublisherURL=https://github.com/Swir
AppSupportURL=https://github.com/Swir/BackgroundPXR/issues
AppUpdatesURL=https://github.com/Swir/BackgroundPXR/releases
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\installer-dist
OutputBaseFilename=BackgroundPXR-{#MyAppVersion}-Setup
SetupIconFile=..\build_assets\BackgroundPXR.ico
UninstallDisplayIcon={app}\BackgroundPXR.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
AllowNoIcons=yes
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany=Swir
VersionInfoDescription=BackgroundPXR AI Background Studio Installer
VersionInfoProductName=BackgroundPXR
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\BackgroundPXR"; Filename: "{app}\BackgroundPXR.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\BackgroundPXR"; Filename: "{app}\BackgroundPXR.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\BackgroundPXR.exe"; Description: "{cm:LaunchProgram,BackgroundPXR}"; Flags: nowait postinstall skipifsilent
