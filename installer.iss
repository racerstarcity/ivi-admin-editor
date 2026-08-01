; IVI Admin Editor — Inno Setup installer
; Для сборки: iscc installer.iss

[Setup]
AppName=IVI Admin Editor
AppVersion=2.2
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
Name: chrome_ext; Description: "Подключить расширение IVI Admin Fill: ярлык «IVI Admin Editor (Браузер)» для запуска браузера с расширением"; GroupDescription: "Расширение браузера:"
Name: launch_after; Description: "Запустить IVI Admin Editor после установки"; GroupDescription: "Запуск:"
Name: show_manual; Description: "Открыть инструкцию после установки"; GroupDescription: "Запуск:"

[Files]
Source: "dist\ivi_meta.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\report.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\markers.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\markers_template.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\IVI Admin Editor.pdf"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\ivi_ext_loader.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "ivi_ext\manifest.json"; DestDir: "{app}\ivi_ext"; Flags: ignoreversion
Source: "ivi_ext\content.js"; DestDir: "{app}\ivi_ext"; Flags: ignoreversion
Source: "ivi_ext\icon.png"; DestDir: "{app}\ivi_ext"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\IVI Admin Editor"; Filename: "{app}\ivi_meta.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ivi_meta.exe"
Name: "{autodesktop}\IVI Admin Editor"; Filename: "{app}\ivi_meta.exe"; WorkingDir: "{app}"; Tasks: desktopicon; IconFilename: "{app}\ivi_meta.exe"
Name: "{autoprograms}\IVI Admin Editor\Инструкция"; Filename: "{app}\IVI Admin Editor.pdf"; IconFilename: "{app}\ivi_meta.exe"
Name: "{autoprograms}\IVI Admin Editor\Chrome (с расширением)"; Filename: "{app}\ivi_ext_loader.exe"; Parameters: "--browser=chrome https://b2b.ivi.ru"; WorkingDir: "{app}"; Tasks: chrome_ext; IconFilename: "{app}\ivi_meta.exe"
Name: "{autodesktop}\IVI Admin Editor (Chrome)"; Filename: "{app}\ivi_ext_loader.exe"; Parameters: "--browser=chrome https://b2b.ivi.ru"; WorkingDir: "{app}"; Tasks: chrome_ext; IconFilename: "{app}\ivi_meta.exe"
Name: "{autoprograms}\IVI Admin Editor\Яндекс (с расширением)"; Filename: "{app}\ivi_ext_loader.exe"; Parameters: "--browser=yandex https://b2b.ivi.ru"; WorkingDir: "{app}"; Tasks: chrome_ext; IconFilename: "{app}\ivi_meta.exe"
Name: "{autodesktop}\IVI Admin Editor (Яндекс)"; Filename: "{app}\ivi_ext_loader.exe"; Parameters: "--browser=yandex https://b2b.ivi.ru"; WorkingDir: "{app}"; Tasks: chrome_ext; IconFilename: "{app}\ivi_meta.exe"

[Run]
Filename: "{app}\ivi_meta.exe"; Description: "Запустить IVI Admin Editor"; Tasks: launch_after; Flags: nowait postinstall skipifsilent
Filename: "{app}\ivi_ext_loader.exe"; Parameters: "--browser=yandex https://b2b.ivi.ru"; Description: "Запустить браузер с расширением"; Tasks: chrome_ext; Flags: nowait postinstall skipifsilent
Filename: "{app}\IVI Admin Editor.pdf"; Description: "Открыть инструкцию"; Tasks: show_manual; Flags: nowait postinstall skipifsilent shellexec
