#define AppVersion "3.4.0a11"
#ifndef BuildTest
  #define BuildTest 0
#endif
[Setup]
#if BuildTest
AppId={{A576BB3A-D586-4EB7-B7D7-679D9CEB99AF}
#else
AppId={{D4AFB827-62E8-4C72-9856-F7FB10ED5DB5}
#endif
AppName=IC35 Sync Beta
AppVersion={#AppVersion}
AppPublisher=Christian Thomas
DefaultDirName={localappdata}\Programs\IC35ThunderbirdAlpha
DefaultGroupName=IC35 Sync Beta
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
#if BuildTest
OutputDir=.installer-test
OutputBaseFilename=Isolated-Test-Setup
#else
OutputDir=release
OutputBaseFilename=IC35-Sync-Beta-{#AppVersion}-Setup
#endif
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=LICENSE
UninstallDisplayIcon={app}\IC35Thunderbird.exe
SetupLogging=yes
[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: desktopicon; Description: "Desktop-Verknüpfung / Desktop shortcut"; Flags: unchecked
[Files]
Source: "dist\IC35Thunderbird.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "release\IC35-Thunderbird-Bridge-3.4.0a9.xpi"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.en.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "PRIVACY.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "TWITCH_EINRICHTEN.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "build-requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "build-licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\IC35 Sync Beta"; Filename: "{app}\IC35Thunderbird.exe"
Name: "{autodesktop}\IC35 Sync Beta"; Filename: "{app}\IC35Thunderbird.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\IC35Thunderbird.exe"; Description: "IC35 Sync Beta starten / Launch"; Flags: nowait postinstall skipifsilent
