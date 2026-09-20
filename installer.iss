[Setup]
AppId={{087413E6-F1C7-459E-AF10-942001CD9B52}
AppName=Siemens IC35 Sync Alpha
AppVersion=3.3.0a8
AppPublisher=Christian Thomas
AppPublisherURL=https://ic35.thundersoos.cc/
DefaultDirName={localappdata}\Programs\IC35SyncAlpha
DefaultGroupName=Siemens IC35 Sync Alpha
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=dist
OutputBaseFilename=IC35-Sync-3.3.0a8-Alpha-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=LICENSE
UninstallDisplayIcon={app}\IC35Sync.exe

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; Flags: unchecked

[Files]
Source: "dist\IC35Sync.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "build-licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Siemens IC35 Sync Alpha"; Filename: "{app}\IC35Sync.exe"
Name: "{autodesktop}\Siemens IC35 Sync Alpha"; Filename: "{app}\IC35Sync.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\IC35Sync.exe"; Description: "Siemens IC35 Sync Alpha starten"; Flags: nowait postinstall skipifsilent
