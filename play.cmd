@echo off
setlocal
set "PROJECT=%~dp0"
set "GODOT=D:\software\Godot\4.7.2\Godot_v4.7.2-stable_win64.exe"

if exist "%GODOT%" goto run
where godot >nul 2>nul
if %errorlevel%==0 (
  set "GODOT=godot"
  goto run
)
echo Godot not found. Install Godot 4.7 and set GODOT in play.cmd.
pause
exit /b 1

:run
start "" "%GODOT%" --path "%PROJECT%"
exit /b 0
