# Recreate the launcher shortcuts (desktop + project folder).
#   powershell -File tools/make_shortcut.ps1
$proj = Split-Path -Parent $PSScriptRoot
$godot = "D:\software\Godot\4.7.2\Godot_v4.7.2-stable_win64.exe"
$icon = Join-Path $proj "assets\icon.ico"

if (-not (Test-Path $godot)) { "Godot not found: $godot"; exit 1 }
if (-not (Test-Path $icon)) { "Icon not found: $icon"; exit 1 }

$ws = New-Object -ComObject WScript.Shell
$targets = @(
    (Join-Path ([Environment]::GetFolderPath('Desktop')) "SCP-CB 2D.lnk"),
    (Join-Path $proj "启动 SCP-CB 2D.lnk")
)
foreach ($path in $targets) {
    $sc = $ws.CreateShortcut($path)
    $sc.TargetPath = $godot
    $sc.Arguments = ('--path "{0}"' -f $proj)
    $sc.WorkingDirectory = $proj
    $sc.IconLocation = $icon
    $sc.Description = "SCP:CB 2D — pixel top-down fan game (vertical slice)"
    $sc.Save()
    if (Test-Path $path) { "OK  $path" } else { "FAILED  $path" }
}
