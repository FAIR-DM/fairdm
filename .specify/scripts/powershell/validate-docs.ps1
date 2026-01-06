<#
.SYNOPSIS
    Validates FairDM documentation for errors, warnings, and link failures

.DESCRIPTION
    Runs comprehensive documentation validation including:
    - Sphinx build check with -W flag (warnings treated as errors)
    - Internal link validation (hard errors)
    - External link validation (warnings only)
    - Feature documentation checklist validation

.PARAMETER SkipBuild
    Skip Sphinx build check

.PARAMETER SkipLinkCheck
    Skip link validation

.PARAMETER SkipChecklist
    Skip checklist validation

.PARAMETER ExitOnError
    Exit immediately on first error (default: false, collect all errors)

.EXAMPLE
    .\.specify\scripts\powershell\validate-docs.ps1
    Runs full validation suite

.EXAMPLE
    .\.specify\scripts\powershell\validate-docs.ps1 -SkipLinkCheck
    Runs validation without link checking

.NOTES
    Requires: poetry, python, sphinx
    Exit codes: 0 = success, 1 = validation failed
#>

param(
    [switch]$SkipBuild,
    [switch]$SkipLinkCheck,
    [switch]$SkipChecklist,
    [switch]$ExitOnError
)

$ErrorActionPreference = "Continue"
$script:ValidationFailed = $false
$script:WarningCount = 0
$script:ErrorCount = 0

function Write-ValidationHeader {
    param([string]$Title)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

function Write-ValidationSuccess {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-ValidationWarning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
    $script:WarningCount++
}

function Write-ValidationError {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
    $script:ErrorCount++
    $script:ValidationFailed = $true

    if ($ExitOnError) {
        Write-Host ""
        Write-Host "Validation failed. Exiting due to -ExitOnError flag." -ForegroundColor Red
        exit 1
    }
}

# Change to repository root
$RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
Push-Location $RepoRoot

try {
    Write-ValidationHeader "FairDM Documentation Validation"
    Write-Host "Repository: $RepoRoot"
    Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

    # Validate Sphinx build
    if (-not $SkipBuild) {
        Write-ValidationHeader "Sphinx Build Check (Warnings as Errors)"

        Write-Host "Running: poetry run sphinx-build -W -b html docs docs/_build" -ForegroundColor Gray

        $buildOutput = & poetry run sphinx-build -W -b html docs docs/_build 2>&1
        $buildExitCode = $LASTEXITCODE

        if ($buildExitCode -eq 0) {
            Write-ValidationSuccess "Documentation builds without errors or warnings"
        }
        else {
            Write-ValidationError "Documentation build failed with errors or warnings"
            Write-Host ""
            Write-Host "Build output:" -ForegroundColor Yellow
            $buildOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        }
    }

    # Validate links
    if (-not $SkipLinkCheck) {
        Write-ValidationHeader "Link Validation (Internal: Hard Errors, External: Warnings)"

        Write-Host "Running: poetry run sphinx-build -b linkcheck docs docs/_build" -ForegroundColor Gray

        $linkcheckOutput = & poetry run sphinx-build -b linkcheck docs docs/_build 2>&1
        $linkcheckExitCode = $LASTEXITCODE

        # Parse linkcheck output
        $outputFile = Join-Path $RepoRoot "docs\_build\output.txt"

        if (Test-Path $outputFile) {
            $linkcheckResults = Get-Content $outputFile

            $brokenInternal = $linkcheckResults | Where-Object { $_ -match "broken" -and $_ -notmatch "http" }
            $brokenExternal = $linkcheckResults | Where-Object { $_ -match "broken" -and $_ -match "http" }

            if ($brokenInternal) {
                Write-ValidationError "Found $($brokenInternal.Count) broken internal links:"
                $brokenInternal | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
            }
            else {
                Write-ValidationSuccess "All internal links are valid"
            }

            if ($brokenExternal) {
                Write-ValidationWarning "Found $($brokenExternal.Count) broken external links (manual review required):"
                $brokenExternal | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
            }
            else {
                Write-ValidationSuccess "All external links are valid"
            }
        }
        else {
            Write-ValidationWarning "Link check output file not found at $outputFile"
        }
    }

    # Validate checklists
    if (-not $SkipChecklist) {
        Write-ValidationHeader "Feature Documentation Checklist Validation"

        $validatorScript = Join-Path $RepoRoot ".specify\scripts\powershell\validate-checklists.py"

        if (Test-Path $validatorScript) {
            Write-Host "Running: poetry run python $validatorScript" -ForegroundColor Gray

            $checklistOutput = & poetry run python $validatorScript 2>&1
            $checklistExitCode = $LASTEXITCODE

            if ($checklistExitCode -eq 0) {
                Write-ValidationSuccess "All feature documentation checklists are complete"
            }
            else {
                Write-ValidationError "Feature documentation checklist validation failed"
                Write-Host ""
                Write-Host "Checklist validation output:" -ForegroundColor Yellow
                $checklistOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            }
        }
        else {
            Write-ValidationWarning "Checklist validator not found at $validatorScript (skipping)"
        }
    }

    # Summary
    Write-ValidationHeader "Validation Summary"

    Write-Host "Errors:   $script:ErrorCount" -ForegroundColor $(if ($script:ErrorCount -gt 0) { "Red" } else { "Green" })
    Write-Host "Warnings: $script:WarningCount" -ForegroundColor $(if ($script:WarningCount -gt 0) { "Yellow" } else { "Green" })

    if ($script:ValidationFailed) {
        Write-Host ""
        Write-Host "✗ Validation FAILED - fix errors above before merging" -ForegroundColor Red
        exit 1
    }
    else {
        Write-Host ""
        Write-Host "✓ Validation PASSED" -ForegroundColor Green

        if ($script:WarningCount -gt 0) {
            Write-Host "  ($script:WarningCount warnings require manual review)" -ForegroundColor Yellow
        }

        exit 0
    }
}
finally {
    Pop-Location
}
