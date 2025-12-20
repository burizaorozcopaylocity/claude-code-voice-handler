#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Reload voice handler to pick up code changes

.DESCRIPTION
    Stops running voice handler daemons and clears Python cache
    so that new code changes are loaded on next hook execution.

.EXAMPLE
    .\reload_voice.ps1
    Reloads the voice handler with latest code changes
#>

Write-Host "`nReloading Voice Handler..." -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# 1. Stop running daemons
Write-Host "`n[1/3] Stopping voice handler daemons..." -ForegroundColor Yellow
$processes = Get-Process python* -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like '*voice_notifications*' }

if ($processes) {
    $processes | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Stopped daemon (PID: $($_.Id))" -ForegroundColor Green
    }
} else {
    Write-Host "  ℹ No daemons running" -ForegroundColor DarkGray
}

# 2. Clear Python cache
Write-Host "`n[2/3] Clearing Python cache..." -ForegroundColor Yellow
$voiceDir = "$env:USERPROFILE\.claude\hooks\voice_notifications"
$cacheFiles = Get-ChildItem -Path $voiceDir -Recurse -Include *.pyc -File -ErrorAction SilentlyContinue
$cacheDirs = Get-ChildItem -Path $voiceDir -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue

$cacheFiles | Remove-Item -Force -ErrorAction SilentlyContinue
$cacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "  ✓ Removed $($cacheFiles.Count) .pyc files" -ForegroundColor Green
Write-Host "  ✓ Removed $($cacheDirs.Count) __pycache__ folders" -ForegroundColor Green

# 3. Clear message queue
Write-Host "`n[3/3] Clearing message queue..." -ForegroundColor Yellow
$queuePath = "$env:TEMP\claude_voice_queue.db"
if (Test-Path $queuePath) {
    Remove-Item $queuePath -Force -ErrorAction SilentlyContinue
    Write-Host "  ✓ Queue database cleared" -ForegroundColor Green
} else {
    Write-Host "  ℹ No queue database found" -ForegroundColor DarkGray
}

Write-Host "`n✓ Voice handler reloaded successfully!" -ForegroundColor Green
Write-Host "  New code will be loaded on next hook execution.`n" -ForegroundColor DarkGray
