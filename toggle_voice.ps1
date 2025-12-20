#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Toggle voice notifications on/off

.DESCRIPTION
    Simple script to enable or disable voice notifications by modifying
    the VOICE_ENABLED flag in .env file and clearing the message queue.

.PARAMETER Enable
    Enable voice notifications

.PARAMETER Disable
    Disable voice notifications (and clear message queue)

.PARAMETER Status
    Show current voice status

.EXAMPLE
    .\toggle_voice.ps1 -Disable
    Disables voice and clears pending messages

.EXAMPLE
    .\toggle_voice.ps1 -Enable
    Enables voice notifications

.EXAMPLE
    .\toggle_voice.ps1 -Status
    Shows current voice status
#>

param(
    [switch]$Enable,
    [switch]$Disable,
    [switch]$Status
)

$envPath = "$PSScriptRoot\.env"

if (-not (Test-Path $envPath)) {
    Write-Error ".env file not found at: $envPath"
    exit 1
}

# Read current .env content
$content = Get-Content $envPath -Raw

# Get current status
$currentStatus = if ($content -match 'VOICE_ENABLED=(\w+)') {
    $matches[1]
} else {
    "unknown"
}

# Show status if requested or no action specified
if ($Status -or (-not $Enable -and -not $Disable)) {
    Write-Host "`nVoice Notifications Status" -ForegroundColor Cyan
    Write-Host "===========================" -ForegroundColor Cyan

    if ($currentStatus -eq "true") {
        Write-Host "Status: " -NoNewline
        Write-Host "ENABLED" -ForegroundColor Green
        Write-Host "`nVoice notifications are currently ACTIVE."
        Write-Host "Run with -Disable to silence notifications.`n"
    } elseif ($currentStatus -eq "false") {
        Write-Host "Status: " -NoNewline
        Write-Host "DISABLED" -ForegroundColor Red
        Write-Host "`nVoice notifications are currently SILENT."
        Write-Host "Run with -Enable to activate notifications.`n"
    } else {
        Write-Host "Status: " -NoNewline
        Write-Host "UNKNOWN" -ForegroundColor Yellow
        Write-Host "`nCould not determine voice status.`n"
    }

    exit 0
}

# Enable voice
if ($Enable) {
    $content = $content -replace 'VOICE_ENABLED=false', 'VOICE_ENABLED=true'
    Set-Content -Path $envPath -Value $content -Force

    Write-Host "`n✓ Voice notifications " -NoNewline -ForegroundColor Green
    Write-Host "ENABLED" -ForegroundColor Green -NoNewline
    Write-Host " - Tech Advisor is now active.`n" -ForegroundColor Green
}

# Disable voice
if ($Disable) {
    $content = $content -replace 'VOICE_ENABLED=true', 'VOICE_ENABLED=false'
    Set-Content -Path $envPath -Value $content -Force

    Write-Host "`n✓ Voice notifications " -NoNewline -ForegroundColor Yellow
    Write-Host "DISABLED" -ForegroundColor Yellow -NoNewline
    Write-Host " - Silence mode activated." -ForegroundColor Yellow
    Write-Host "  Message queue will be cleared on next hook call.`n" -ForegroundColor DarkGray
}
