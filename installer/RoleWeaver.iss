#ifndef AppVersion
  #error AppVersion must be supplied by build_installer.py
#endif
#ifndef PayloadDir
  #error PayloadDir must be supplied by build_installer.py
#endif
#ifndef OutputPath
  #error OutputPath must be supplied by build_installer.py
#endif

[Setup]
AppId={{C6F47CF3-CB49-4846-90F7-74FF6339D65C}
AppName=Role Weaver Module Studio
AppVersion={#AppVersion}
AppVerName=Role Weaver Module Studio {#AppVersion}
AppPublisher=RoleWeaverInfo
AppPublisherURL=https://github.com/RoleWeaverInfo/RWSoloSuite
DefaultDirName={localappdata}\Programs\Role Weaver Module Studio
DefaultGroupName=Role Weaver Module Studio
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
WizardStyle=modern
DisableProgramGroupPage=yes
AllowNoIcons=yes
OutputDir={#OutputPath}
OutputBaseFilename=Role-Weaver-Module-Studio-{#AppVersion}-Setup-x64
Compression=lzma2
SolidCompression=yes
SetupLogging=yes
AppMutex=Local\RoleWeaver.ModuleStudio.Service
CloseApplications=no
RestartApplications=no
UninstallDisplayIcon={app}\Role Weaver Module Studio.exe
LicenseFile={#PayloadDir}\ROLE-WEAVER-LICENSE.txt

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Role Weaver Module Studio"; Filename: "{app}\Role Weaver Module Studio.exe"; WorkingDir: "{app}"
Name: "{group}\AI service status"; Filename: "{app}\Role Weaver Module Studio.exe"; Parameters: "--player"; WorkingDir: "{app}"
Name: "{group}\User guide"; Filename: "{app}\README.md"
Name: "{autodesktop}\Role Weaver Module Studio"; Filename: "{app}\Role Weaver Module Studio.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\RoleWeaver\ModuleStudio"; ValueType: string; ValueName: "InstallDir"; ValueData: "{app}"; Flags: uninsdeletekey

[Run]
Filename: "{app}\Role Weaver Module Studio.exe"; Description: "Start Role Weaver Module Studio"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent

; No user-data directory is owned or removed by the installer. The application
; stores projects, builds and encrypted keys in LocalAppData\RoleWeaver\ModuleStudio.
