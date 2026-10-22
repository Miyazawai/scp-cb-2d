# Headless regression suite. One command, red or green.
#   powershell -File tools/test.ps1
$ErrorActionPreference = "Continue"
$GODOT = "D:\software\Godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe"
if (-not (Test-Path $GODOT)) { "Godot not found: $GODOT"; exit 2 }

$base = @("--path", ".", "--headless", "--quit-after", "4000", "--")

$cases = @(
    @{ n = "act1 validates clean";       a = @("--validate");                                 code = 0; has = "problems=0" },
    @{ n = "good fixture validates";     a = @("--validate=res://levels/test/good.json");      code = 0; has = "problems=0" },
    @{ n = "off-floor decal rejected";   a = @("--validate=res://levels/test/bad_decal.json"); code = 1; has = "decal" },
    @{ n = "duplicate doc id rejected";  a = @("--validate=res://levels/test/dup_doc.json");   code = 1; has = "duplicate" },
    @{ n = "scenario list";              a = @("--scenario=list");                             code = 0; has = "act1_walkthrough" },
    @{ n = "boot into --level fixture";  a = @("--level=res://levels/test/good.json", "--scenario=fixture_spawn"); code = 0; has = "PASS failures=0" },
    @{ n = "act2 scp-106 stalks";        a = @("--level=res://levels/act2.json", "--scenario=act2_106"); code = 0; has = "PASS failures=0" },
    @{ n = "act1 walkthrough";           a = @("--scenario=act1_walkthrough");                 code = 0; has = "PASS failures=0" },
    @{ n = "act1 documents";             a = @("--scenario=act1_documents");                   code = 0; has = "PASS failures=0" },
    @{ n = "act1 terminals";             a = @("--scenario=act1_terminals");                   code = 0; has = "PASS failures=0" },
    @{ n = "act1 vending machine";       a = @("--scenario=act1_vending");                     code = 0; has = "PASS failures=0" },
    @{ n = "act1 elevator";              a = @("--scenario=act1_elevator");                    code = 0; has = "PASS failures=0" },
    @{ n = "negative control goes red";  a = @("--scenario=negative_control");                 code = 1; has = "FAIL failures=1" }
)

$fail = 0
foreach ($c in $cases) {
    $a = $base + $c.a
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
