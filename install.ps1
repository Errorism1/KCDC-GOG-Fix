<#
.SYNOPSIS
    GOG workaround for KCDC (Kingdoms Connected) 1.7.1 on Kingdom Come: Deliverance II 1.5.6.0 (GOG build).

.DESCRIPTION
    Creates KCDCClient_gog.dll next to the original KCDCClient.dll and points KCDC_launcher.json at it.
    The original KCDCClient.dll is NOT modified, so the KCDC updater keeps reporting "up-to-date".

    What changes: three encrypted byte patterns (function signatures) inside the DLL are replaced so they
    match the GOG build of WHGame.dll. See docs/TECHNICAL.md.

    The script refuses to run unless KCDCClient.dll is exactly the file from KCDC 1.7.1 (SHA-256 check).

.PARAMETER ClientDir
    Folder that contains KCDCClient.dll and KCDCLauncher.exe (the "client" folder of the KCDC download).
    Defaults to the current directory.

.PARAMETER SkipConfig
    Only create KCDCClient_gog.dll, do not touch KCDC_launcher.json.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install.ps1 -ClientDir "D:\Games\KCDC-1.7.1\client"
#>
[CmdletBinding()]
param(
    [string]$ClientDir = (Get-Location).Path,
    [switch]$SkipConfig
)

$ErrorActionPreference = 'Stop'

$SrcName      = 'KCDCClient.dll'
$DstName      = 'KCDCClient_gog.dll'
$ConfigName   = 'KCDC_launcher.json'
$SrcSha256    = '28949D27AD5FC508B2FAA1FFA430E83A8401445FD3142C1469B936F7A38636FC'
$PatchedSha256 = '4CAFE06C773C893F68DEA9D5FDF0D29588CAA12A185953AAEAB3839134453BB4'

# The patterns sit XOR-encrypted in .rdata. File offset = RVA - 0x1C00 (.rdata: VA 0xD2D000, raw 0xD2B400).
# keystream = old plaintext XOR old ciphertext; new ciphertext = new plaintext XOR keystream.
$Patches = @(
    @{ Rva = 0x1577480; Length = 84
       Old = '48 89 5C 24 08 55 56 57 48 83 EC 20 48 8B F1 FF 15 ? ? ? ? 39 05 ? ? ? ? 74 0F 32 C0'
       New = '48 89 5C 24 08 55 56 57 48 83 EC 20 48 8B F1 FF 15 ? ? ? ? 39 05 ? ? ? ? 0F 85' },
    @{ Rva = 0x1583140; Length = 86
       Old = '40 55 53 56 57 41 56 48 8B EC 48 81 EC 80 00 00 00 48 8B F9 B2 0B 48 8B 89 30 03 00 00'
       New = '55 53 57 41 56 41 57 48 8B EC 48 81 EC 80 00 00 00 48 8B F9 B2 0B 48 8B 89 30 03 00 00' },
    @{ Rva = 0x1587500; Length = 142
       Old = '48 83 EC 28 48 85 C9 74 12 48 8B 05 ? ? ? ? 33 D2 FF D0 F0 01 05 ? ? ? ? 48 83 C4 28 C3 ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? CC 40 53'
       New = '48 83 EC 28 48 85 C9 74 12 48 8B 05 ? ? ? ? 33 D2 FF D0 F0 01 05 ? ? ? ? 48 83 C4 28' }
)

function Stop-Install([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

$ClientDir = (Resolve-Path -LiteralPath $ClientDir).Path
$src = Join-Path $ClientDir $SrcName
$dst = Join-Path $ClientDir $DstName
$cfg = Join-Path $ClientDir $ConfigName

if (-not (Test-Path -LiteralPath $src)) { Stop-Install "$SrcName not found in '$ClientDir'. Pass the KCDC 'client' folder with -ClientDir." }

$srcHash = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
if ($srcHash -ne $SrcSha256) {
    Stop-Install ("$SrcName does not match KCDC 1.7.1 (SHA-256 $srcHash).`n" +
        "This fix only works for that exact file. If the updater installed a newer KCDC version, first check whether it already supports GOG " +
        "(set mod_dll_name back to $SrcName, see README).")
}

[byte[]]$data = [IO.File]::ReadAllBytes($src)

foreach ($p in $Patches) {
    $off = $p.Rva - 0x1C00
    $len = $p.Length
    $old = [Text.Encoding]::ASCII.GetBytes($p.Old)
    if ($old.Length -ne $len) { Stop-Install "Internal error: old pattern length $($old.Length) != $len" }

    # New plaintext, padded with ' ?' (wildcards) to the original length.
    $txt = $p.New
    if (($len - $txt.Length) % 2 -ne 0) { $txt = ($txt.Split(' ') | Select-Object -SkipLast 1) -join ' ' }
    $txt += ' ?' * [int](($len - $txt.Length) / 2)
    if ($txt.Length -ne $len) { Stop-Install "Internal error: new pattern length $($txt.Length) != $len" }
    $new = [Text.Encoding]::ASCII.GetBytes($txt)

    for ($i = 0; $i -lt $len; $i++) {
        $ks = $old[$i] -bxor $data[$off + $i]
        $data[$off + $i] = $new[$i] -bxor $ks
    }
}

[IO.File]::WriteAllBytes($dst, $data)
$dstHash = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
if ($dstHash -ne $PatchedSha256) {
    Remove-Item -LiteralPath $dst -Force
    Stop-Install "Result hash $dstHash is not the expected $PatchedSha256. Nothing was installed."
}
Write-Host "Created $DstName (SHA-256 verified)." -ForegroundColor Green

if ($SkipConfig) {
    Write-Host "Skipped $ConfigName. Set `"mod_dll_name`":`"$DstName`" yourself."
    exit 0
}

if (-not (Test-Path -LiteralPath $cfg)) {
    Write-Host ""
    Write-Host "$ConfigName does not exist yet." -ForegroundColor Yellow
    Write-Host "Start KCDCLauncher.exe once, select your GOG KingdomCome.exe when asked (Bin\Win64MasterMasterGogPGO\KingdomCome.exe),"
    Write-Host "let it crash or close it, then run this script again."
    exit 0
}

$json = Get-Content -LiteralPath $cfg -Raw
if ($json -notmatch '"mod_dll_name"\s*:\s*"[^"]*"') { Stop-Install "$ConfigName has no mod_dll_name entry; edit it by hand (see README)." }
if (-not (Test-Path -LiteralPath "$cfg.bak")) { Copy-Item -LiteralPath $cfg -Destination "$cfg.bak" }
$json = [regex]::Replace($json, '"mod_dll_name"\s*:\s*"[^"]*"', "`"mod_dll_name`":`"$DstName`"")
[IO.File]::WriteAllText($cfg, $json, (New-Object Text.UTF8Encoding($false)))
Write-Host "Updated $ConfigName (backup: $ConfigName.bak)." -ForegroundColor Green
Write-Host ""
Write-Host "Done. Start KCDCLauncher.exe as usual."
