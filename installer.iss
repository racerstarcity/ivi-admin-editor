; IVI Admin Editor — Inno Setup installer
; Для сборки: iscc installer.iss

[Setup]
AppName=IVI Admin Editor
AppVersion=2.0
AppPublisher=Кравченко И.В.
AppPublisherURL=https://ivi.ru
DefaultDirName={autopf}\IVI Admin Editor
DefaultGroupName=IVI Admin Editor
UninstallDisplayIcon={app}\ivi_meta.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=IVI_Admin_Editor_Setup
SetupIconFile=ivi.ico
WizardStyle=classic
WizardImageFile=dist\wizard_ivibig.bmp
WizardSmallImageFile=dist\wizard_ivismall.bmp
DisableWelcomePage=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: desktopicon; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Ярлыки:"
Name: chrome_ext; Description: "Автоматически подключить расширение к Chrome и Яндекс.Браузер (--load-extension)"; GroupDescription: "Расширение браузера:"
Name: launch_after; Description: "Запустить IVI Admin Editor после установки"; GroupDescription: "Запуск:"
Name: show_manual; Description: "Открыть инструкцию после установки"; GroupDescription: "Запуск:"

[Files]
Source: "dist\ivi_meta.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\report.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\markers.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\markers_template.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\IVI Admin Editor.pdf"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "ivi_ext\manifest.json"; DestDir: "{app}\ivi_ext"; Flags: ignoreversion
Source: "ivi_ext\content.js"; DestDir: "{app}\ivi_ext"; Flags: ignoreversion
Source: "ivi_ext\icon.png"; DestDir: "{app}\ivi_ext"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\IVI Admin Editor"; Filename: "{app}\ivi_meta.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ivi_meta.exe"
Name: "{autodesktop}\IVI Admin Editor"; Filename: "{app}\ivi_meta.exe"; WorkingDir: "{app}"; Tasks: desktopicon; IconFilename: "{app}\ivi_meta.exe"
Name: "{autoprograms}\IVI Admin Editor\Инструкция"; Filename: "{app}\IVI Admin Editor.pdf"; IconFilename: "{app}\ivi_meta.exe"

[Run]
Filename: "{app}\ivi_meta.exe"; Description: "Запустить IVI Admin Editor"; Tasks: launch_after; Flags: nowait postinstall skipifsilent
Filename: "{app}\IVI Admin Editor.pdf"; Description: "Открыть инструкцию"; Tasks: show_manual; Flags: nowait postinstall skipifsilent shellexec

[Code]
function GetChromePath(Param: string): string;
var
  Paths: array of string;
  I: Integer;
begin
  SetArrayLength(Paths, 5);
  Paths[0] := ExpandConstant('{pf64}\Google\Chrome\Application\chrome.exe');
  Paths[1] := ExpandConstant('{pf32}\Google\Chrome\Application\chrome.exe');
  Paths[2] := ExpandConstant('{localappdata}\Google\Chrome\Application\chrome.exe');
  Paths[3] := ExpandConstant('{pf64}\Yandex\YandexBrowser\Application\browser.exe');
  Paths[4] := ExpandConstant('{pf32}\Yandex\YandexBrowser\Application\browser.exe');
  Result := 'chrome.exe';
  for I := 0 to GetArrayLength(Paths)-1 do
  begin
    if FileExists(Paths[I]) then
    begin
      Result := Paths[I];
      Exit;
    end;
  end;
end;

function FindBrowserShortcut(const DesktopDir, BrowserExe: string): string;
var
  FindRec: TFindRec;
  ShortcutPath: string;
  WshShell, Shortcut: Variant;
  Target: string;
begin
  Result := '';
  if FindFirst(AddBackslash(DesktopDir) + '*.lnk', FindRec) then
  begin
    try
      repeat
        ShortcutPath := AddBackslash(DesktopDir) + FindRec.Name;
        WshShell := CreateOleObject('WScript.Shell');
        Shortcut := WshShell.CreateShortcut(ShortcutPath);
        Target := LowerCase(string(Shortcut.TargetPath));
        if Pos(LowerCase(BrowserExe), Target) > 0 then
        begin
          Result := ShortcutPath;
          Exit;
        end;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;

procedure PatchBrowserShortcut(const DesktopDir, BrowserExe, LoadExtArg: string);
var
  FoundPath, BackupPath: string;
  WshShell, Shortcut: Variant;
  OldArgs, NewArgs: string;
begin
  FoundPath := FindBrowserShortcut(DesktopDir, BrowserExe);
  if FoundPath = '' then
    Exit;

  WshShell := CreateOleObject('WScript.Shell');
  Shortcut := WshShell.CreateShortcut(FoundPath);
  OldArgs := string(Shortcut.Arguments);

  // Already patched?
  if Pos('load-extension', OldArgs) > 0 then
    Exit;

  // Create backup
  BackupPath := Copy(FoundPath, 1, Length(FoundPath) - 4) + '_original.lnk';
  if not FileExists(BackupPath) then
  begin
    WshShell := CreateOleObject('WScript.Shell');
    Shortcut := WshShell.CreateShortcut(FoundPath);
    Shortcut.Save; // flush current state
    // Copy current .lnk as backup
    CopyFile(FoundPath, BackupPath, False);
  end;

  // Modify shortcut
  NewArgs := Trim(OldArgs + ' ' + LoadExtArg);
  Shortcut.Arguments := NewArgs;
  Shortcut.Save;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  DesktopDir: string;
  AppDir: string;
  LoadExtArg: string;
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('chrome_ext') then
    begin
      DesktopDir := ExpandConstant('{autodesktop}');
      AppDir := ExpandConstant('{app}');
      LoadExtArg := '--load-extension="' + AppDir + '\ivi_ext"';
      PatchBrowserShortcut(DesktopDir, 'chrome.exe', LoadExtArg);
      PatchBrowserShortcut(DesktopDir, 'browser.exe', LoadExtArg);
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DesktopDir: string;
  FindRec: TFindRec;
  ShortcutPath, BackupPath: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DesktopDir := ExpandConstant('{autodesktop}');
    if FindFirst(AddBackslash(DesktopDir) + '*.lnk', FindRec) then
    begin
      try
        repeat
          ShortcutPath := AddBackslash(DesktopDir) + FindRec.Name;
          BackupPath := Copy(ShortcutPath, 1, Length(ShortcutPath) - 4) + '_original.lnk';
          if FileExists(BackupPath) then
          begin
            if DeleteFile(ShortcutPath) then
              RenameFile(BackupPath, ShortcutPath);
          end;
        until not FindNext(FindRec);
      finally
        FindClose(FindRec);
      end;
    end;
  end;
end;
