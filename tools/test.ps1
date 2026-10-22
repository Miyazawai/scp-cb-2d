# Headless regression suite. One command, red or green.
#   pwsh tools/test.ps1
$ErrorActionPreference = "Continue"
$GODOT = "D:\software\Godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe"
if (-not (Test-Path $GODOT)) { "Godot not found: $GODOT"; exit 2 }

$cases = @(
    @{ n = "act1 validates clean";        a = @("--path", ".", "--headless", "--quit-after", "240", "--", "--validate");                                  code = 0; has = "problems=0" },
    @{ n = "good fixture validates";      a = @("--path", ".", "--headless", "--quit-after", "240", "--", "--validate=res://levels/test/good.json");      code = 0; has = "problems=0" },
    @{ n = "off-floor decal rejected";    a = @("--path", ".", "--headless", "--quit-after", "240", "--", "--validate=res://levels/test/bad_decal.json");  code = 1; has = "decal" },
    @{ n = "duplicate doc id rejected";   a = @("--path", ".", "--headless", "--quit-after", "240", "--", "--validate=res://levels/test/dup_doc.json");    code = 1; has = "duplicate" }
)

$fail = 0
foreach ($c in $cases) {
    $a = $c.a
    $out = (& $GODOT @a 2>&1 | Out-String)
    $code = $LASTEXITCODE
    $hit = $out -match [regex]::Escape($c.has)
    if (($code -eq $c.code) -and $hit) {
        "PASS  {0}" -f $c.n
    }
    else {
        "FAIL  {0}  (exit={1} want={2} match='{3}')" -f $c.n, $code, $c.code, $c.has
        $fail++
    }
}
if ($fail -gt 0) { "FAILURES: $fail"; exit 1 }
"ALL PASS"
exit 0

