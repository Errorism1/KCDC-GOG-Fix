<#
.SYNOPSIS
    Reverts the GOG workaround: points KCDC_launcher.json back to the original KCDCClient.dll.

.PARAMETER ClientDir
    The "client" folder of the KCDC download. Defaults to the current directory.

.PARAMETER RemoveDll
    Also delete KCDCClient_gog.dll.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\uninstall.ps1 -ClientDir "D:\Games\KCDC-1.7.1\client" -RemoveDll
#>
[CmdletBinding()]
param(
    [string]$ClientDir = (Get-Location).Path,
    [switch]$RemoveDll
)

$ErrorActionPreference = 'Stop'
$ClientDir = (Resolve-Path -LiteralPath $ClientDir).Path
$cfg = Join-Path $ClientDir 'KCDC_launcher.json'
$dll = Join-Path $ClientDir 'KCDCClient_gog.dll'

if (Test-Path -LiteralPath $cfg) {
    $json = Get-Content -LiteralPath $cfg -Raw
    $json = [regex]::Replace($json, '"mod_dll_name"\s*:\s*"[^"]*"', '"mod_dll_name":"KCDCClient.dll"')
    [IO.File]::WriteAllText($cfg, $json, (New-Object Text.UTF8Encoding($false)))
    Write-Host "KCDC_launcher.json now uses KCDCClient.dll again." -ForegroundColor Green
} else {
    Write-Host "KCDC_launcher.json not found, nothing to revert." -ForegroundColor Yellow
}

if ($RemoveDll -and (Test-Path -LiteralPath $dll)) {
    Remove-Item -LiteralPath $dll -Force
    Write-Host "Deleted KCDCClient_gog.dll."
}
