; Inno Setup Script for downloadcc CLI Downloader
; See https://www.jrsoftware.org/ishelp/ for details on creating Inno Setup scripts.

#define MyAppName "downloadcc"
#define MyAppVersion "2.2"
#define MyAppPublisher "Oumar Ibrahim"
#define MyAppExeName "downloadcc.exe"

[Setup]
; NOTE: The AppId uniquely identifies this application. Keep the same to allow clean upgrades.
AppId={{2A9F4442-5C29-11F1-B19C-D843AE4E8AE7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={userappdata}\downloadcc
DefaultGroupName={#MyAppName}
OutputDir=.
OutputBaseFilename=MoviesAndShowsInstaller
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\downloadcc.exe"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Flags: preservestringtype; Check: NeedsAddPath

[Code]
function NeedsAddPath(): Boolean;
var
  CurrentPath: String;
begin
  if RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', CurrentPath) then
  begin
    Result := Pos(ExpandConstant('{app}'), CurrentPath) = 0;
  end
  else
  begin
    Result := True;
  end;
end;
