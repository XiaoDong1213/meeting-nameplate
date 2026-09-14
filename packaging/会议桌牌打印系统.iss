; 会议桌牌打印系统 Inno Setup 7 installer
; Copyright © 2026 XiaoDong and JiangRTTTR

#define MyAppName "会议桌牌打印系统"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "XiaoDong & JiangRTTTR"
#define MyAppExeName "会议桌牌打印系统.exe"
; Paths are relative to this .iss file in packaging/.
#define MyAppSourceDir AddBackslash(SourcePath) + "..\dist\会议桌牌打印系统"
#define MyAppIcon AddBackslash(SourcePath) + "..\resources\icon.ico"
#define MyAppUserModelId "XiaoDong.MeetingNameplate"

[Setup]
AppId={{A7E3C291-4F8B-4D2A-9C61-8E2F5B7A1D03}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
OutputDir=..\dist_installer
OutputBaseFilename=会议桌牌打印系统_Setup
SetupIconFile={#MyAppIcon}
SolidCompression=yes
WizardStyle=modern dynamic

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:\Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Personal configuration files are never included in the installer.
; Existing user configuration is preserved during overwrite/upgrade installation.
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "config.ini,config.json,settings.ini,settings.json,history.ini,history.json,crash.log"

[Icons]
; Read the icon directly from the installed EXE instead of referencing icon.ico.
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; IconIndex: 0; WorkingDir: "{app}"; AppUserModelID: "{#MyAppUserModelId}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; IconIndex: 0; WorkingDir: "{app}"; AppUserModelID: "{#MyAppUserModelId}"; Tasks: desktopicon

[Code]
procedure DeleteUserData;
var
  UserDataDir: string;
begin
  { Installed-version configuration is stored in %APPDATA%\meeting_nameplate. }
  UserDataDir := ExpandConstant('{userappdata}\meeting_nameplate');
  if DirExists(UserDataDir) then
    DelTree(UserDataDir, True, True, True);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  { Only a real uninstall removes user data. Overwrite/upgrade installation does not call this. }
  if CurUninstallStep = usUninstall then
  begin
    MsgBox('会议桌牌打印系统将删除程序文件以及当前用户保存的配置等数据。', mbInformation, MB_OK);
    DeleteUserData;
  end;
end;

[Run]
; Refresh the Windows shell icon cache after an overwrite installation.
Filename: "{sys}\ie4uinit.exe"; Parameters: "-show"; Flags: runhidden waituntilterminated skipifsilent
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
