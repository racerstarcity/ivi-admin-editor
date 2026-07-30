@echo off
chcp 65001 >nul
title Установка IVI Tools

set DEST=%ProgramFiles%\IVI Tools
set SRC=%~dp0

echo.
echo  Установка IVI Tools v1.3
echo =============================
echo.
echo Будет установлено в: %DEST%
echo.

:confirm
set /p CONFIRM=Продолжить? (Enter - да, N - нет): 
if /i "%CONFIRM%"=="N" exit /b

:: Создание папки
if not exist "%DEST%" mkdir "%DEST%"

:: Копирование файлов
echo.
echo Копирование файлов...
copy /Y "%SRC%dist\ivi_meta.exe" "%DEST%\" >nul
copy /Y "%SRC%dist\ivi.xlsx" "%DEST%\" >nul
copy /Y "%SRC%dist\report.txt" "%DEST%\" >nul
copy /Y "%SRC%dist\ivi_meta_manual.pdf" "%DEST%\" >nul

if exist "%SRC%ivi_ext" (
    if not exist "%DEST%\ivi_ext" mkdir "%DEST%\ivi_ext"
    copy /Y "%SRC%ivi_ext\manifest.json" "%DEST%\ivi_ext\" >nul
    copy /Y "%SRC%ivi_ext\content.js" "%DEST%\ivi_ext\" >nul
    copy /Y "%SRC%ivi_ext\icon.png" "%DEST%\ivi_ext\" >nul
)

:: Создаём ярлык на рабочем столе через VBS
set VBS=%TEMP%\mklnk.vbs
set SHORTCUT=%USERPROFILE%\Desktop\IVI Tools.lnk
echo Set sh = CreateObject("WScript.Shell") > "%VBS%"
echo Set lnk = sh.CreateShortcut("%SHORTCUT%") >> "%VBS%"
echo lnk.TargetPath = "%DEST%\ivi_meta.exe" >> "%VBS%"
echo lnk.WorkingDirectory = "%DEST%" >> "%VBS%"
echo lnk.Description = "IVI Tools - утилита тестировщика" >> "%VBS%"
echo lnk.Save >> "%VBS%"
cscript //nologo "%VBS%"
del "%VBS%"

echo.
echo =============================
echo Установка завершена!
echo.
echo Ярлык: на рабочем столе
echo Расширение Chrome: %DEST%\ivi_ext
echo   chrome://extensions/ → Загрузить распакованное
echo.
pause
