#define MyAppName "RubiMorph"
#ifndef MyAppVersion
  #error MyAppVersion must be passed by scripts\build_installer.cmd from VERSION.
#endif
#define MyAppPublisher "Tadatsune Sakamoto"
#define MyAppURL "https://github.com/TadatsuneSakamoto/RubiMorph"
#define MyAppSupportURL "https://github.com/TadatsuneSakamoto/RubiMorph/issues"
#define MyCliExeName "RubiMorph.exe"
#define MyGuiExeName "RubiMorphGUI.exe"

[Setup]
AppId={{5B6D93ED-EB9C-4F4D-A449-9B06B6C10C5A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppSupportURL}
AppUpdatesURL={#MyAppURL}
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyGuiExeName}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist\installer
OutputBaseFilename=RubiMorphSetup-{#MyAppVersion}
SetupIconFile=..\..\assets\icons\rubimorph.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Files]
Source: "..\..\dist\RubiMorph\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\assets\icons\rubimorph.ico"; DestDir: "{app}\assets\icons"; Flags: ignoreversion
Source: "..\..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\LICENSES\*"; DestDir: "{app}\LICENSES"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "デスクトップにショートカットを作成する"; GroupDescription: "追加ショートカット:"; Flags: unchecked

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyGuiExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyGuiExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyGuiExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyGuiExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyGuiExeName}"; Description: "RubiMorphを起動する"; Flags: nowait postinstall skipifsilent runasoriginaluser skipifdoesntexist
