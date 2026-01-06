<#
.SYNOPSIS
    Audits FairDM documentation for conformance with standards

.DESCRIPTION
    Scans documentation files and generates conformance audit report including:
    - Missing spec cross-references
    - Misplaced files in directory structure
    - Missing alt text on images
    - Heading hierarchy violations
    - Other documentation quality issues

.PARAMETER OutputFormat
    Output format: Text (default), Json, or Html

.PARAMETER OutputFile
    Path to save audit report (optional, prints to console by default)

.PARAMETER Verbose
    Show detailed audit process information

.EXAMPLE
    .\.specify\scripts\powershell\audit-docs.ps1
    Runs conformance audit with text output to console

.EXAMPLE
    .\.specify\scripts\powershell\audit-docs.ps1 -OutputFormat Json -OutputFile audit-report.json
    Generates JSON audit report

.NOTES
    Requires: PowerShell 5.1+
    Exit codes: 0 = success (may have findings), 1 = error running audit
#>

param(
    [ValidateSet("Text", "Json", "Html")]
    [string]$OutputFormat = "Text",

    [string]$OutputFile,

    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

# Change to repository root
$RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
Push-Location $RepoRoot

class AuditFinding {
    [string]$FilePath
    [string]$Category
    [string]$Issue
    [string]$Remediation
    [string]$Priority
}

class ConformanceAudit {
    [datetime]$AuditDate
    [int]$PagesScanned
    [System.Collections.ArrayList]$Findings
    [hashtable]$IssuesByCategory

    ConformanceAudit() {
        $this.AuditDate = Get-Date
        $this.PagesScanned = 0
        $this.Findings = New-Object System.Collections.ArrayList
        $this.IssuesByCategory = @{}
    }

    [void]AddFinding([string]$FilePath, [string]$Category, [string]$Issue, [string]$Remediation, [string]$Priority) {
        $finding = [AuditFinding]@{
            FilePath = $FilePath
            Category = $Category
            Issue = $Issue
            Remediation = $Remediation
            Priority = $Priority
        }
        $this.Findings.Add($finding) | Out-Null

        if (-not $this.IssuesByCategory.ContainsKey($Category)) {
            $this.IssuesByCategory[$Category] = 0
        }
        $this.IssuesByCategory[$Category]++
    }
}

function Get-MarkdownFiles {
    param([string]$Path)

    Get-ChildItem -Path $Path -Filter "*.md" -Recurse -File |
        Where-Object { $_.FullName -notmatch '\\(_build|node_modules|\.venv|venv|__pycache__|\.git)\\' }
}

function Test-SpecCrossReferences {
    param(
        [string]$FilePath,
        [ConformanceAudit]$Audit
    )

    $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return }

    # Check if file mentions features but lacks spec cross-references
    $mentionsFeature = $content -match '(feature|Feature|implementation|Implementation)'
    $hasSpecReference = $content -match '\[.*\]\(.*specs/\d+-.*\.md\)'

    # Only flag feature-related docs without spec links
    if ($mentionsFeature -and -not $hasSpecReference -and $FilePath -match 'docs\\(developer-guide|contributing)') {
        $relPath = $FilePath.Replace($RepoRoot, '').TrimStart('\')
        $Audit.AddFinding(
            $relPath,
            "Missing Spec Cross-Reference",
            "Feature-related documentation lacks link to specification",
            "Add spec cross-reference: [spec](../../specs/###-feature-name/spec.md)",
            "Medium"
        )
    }
}

function Test-FileLocation {
    param(
        [string]$FilePath,
        [ConformanceAudit]$Audit
    )

    $relPath = $FilePath.Replace($RepoRoot, '').TrimStart('\')

    # Check if file is in correct section based on content heuristics
    $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return }

    # Developer guide heuristics
    if ($content -match 'portal (developer|builder)' -and $FilePath -notmatch 'developer-guide') {
        $Audit.AddFinding(
            $relPath,
            "Misplaced File",
            "Content appears to be for portal developers but is not in developer-guide/",
            "Move to docs/developer-guide/ or update content",
            "Low"
        )
    }

    # Admin guide heuristics
    if ($content -match '(deploy|deployment|production|administrator)' -and $FilePath -notmatch 'admin-guide' -and $FilePath -notmatch 'contributing') {
        $Audit.AddFinding(
            $relPath,
            "Misplaced File",
            "Content appears to be for administrators but is not in admin-guide/",
            "Move to docs/admin-guide/ or update content",
            "Low"
        )
    }
}

function Test-ImageAltText {
    param(
        [string]$FilePath,
        [ConformanceAudit]$Audit
    )

    $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return }

    # Find Markdown images: ![alt](url) or ![](url)
    $imagePattern = '!\[(.*?)\]\((.*?)\)'
    $matches = [regex]::Matches($content, $imagePattern)

    foreach ($match in $matches) {
        $altText = $match.Groups[1].Value
        $imageUrl = $match.Groups[2].Value

        if ([string]::IsNullOrWhiteSpace($altText)) {
            $relPath = $FilePath.Replace($RepoRoot, '').TrimStart('\')
            $Audit.AddFinding(
                $relPath,
                "Missing Alt Text",
                "Image '$imageUrl' has no alt text",
                "Add descriptive alt text: ![descriptive text]($imageUrl)",
                "High"
            )
        }
    }
}

function Test-HeadingHierarchy {
    param(
        [string]$FilePath,
        [ConformanceAudit]$Audit
    )

    $lines = Get-Content $FilePath -ErrorAction SilentlyContinue
    if (-not $lines) { return }

    $previousLevel = 0
    $lineNumber = 0

    foreach ($line in $lines) {
        $lineNumber++

        if ($line -match '^(#{1,6})\s+(.+)') {
            $currentLevel = $matches[1].Length

            # Check if heading level skips (e.g., H1 → H3)
            if ($previousLevel -gt 0 -and $currentLevel -gt ($previousLevel + 1)) {
                $relPath = $FilePath.Replace($RepoRoot, '').TrimStart('\')
                $nextLevel = $previousLevel + 1
                $Audit.AddFinding(
                    $relPath,
                    "Heading Hierarchy Violation",
                    "Line ${lineNumber}: Heading level skips from H${previousLevel} to H${currentLevel}",
                    "Use H${nextLevel} instead of H${currentLevel}",
                    "Medium"
                )
            }

            $previousLevel = $currentLevel
        }
    }
}

function Format-AuditReport {
    param(
        [ConformanceAudit]$Audit,
        [string]$Format
    )

    switch ($Format) {
        "Json" {
            $Audit | ConvertTo-Json -Depth 10
        }
        "Html" {
            $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Documentation Conformance Audit</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .high { background-color: #ffcccc; }
        .medium { background-color: #fff3cd; }
        .low { background-color: #d1ecf1; }
    </style>
</head>
<body>
    <h1>Documentation Conformance Audit</h1>
    <p><strong>Audit Date:</strong> $($Audit.AuditDate.ToString('yyyy-MM-dd HH:mm:ss'))</p>
    <p><strong>Pages Scanned:</strong> $($Audit.PagesScanned)</p>
    <p><strong>Total Findings:</strong> $($Audit.Findings.Count)</p>

    <h2>Findings by Category</h2>
    <table>
        <tr><th>Category</th><th>Count</th></tr>
"@
            foreach ($category in $Audit.IssuesByCategory.Keys | Sort-Object) {
                $html += "        <tr><td>$category</td><td>$($Audit.IssuesByCategory[$category])</td></tr>`n"
            }

            $html += @"
    </table>

    <h2>All Findings</h2>
    <table>
        <tr><th>Priority</th><th>Category</th><th>File</th><th>Issue</th><th>Remediation</th></tr>
"@
            foreach ($finding in $Audit.Findings | Sort-Object Priority, Category) {
                $rowClass = $finding.Priority.ToLower()
                $html += "        <tr class='$rowClass'><td>$($finding.Priority)</td><td>$($finding.Category)</td><td>$($finding.FilePath)</td><td>$($finding.Issue)</td><td>$($finding.Remediation)</td></tr>`n"
            }

            $html += @"
    </table>
</body>
</html>
"@
            $html
        }
        default {
            # Text format
            $report = @"
═══════════════════════════════════════════════════════════════
 Documentation Conformance Audit Report
═══════════════════════════════════════════════════════════════

Audit Date: $($Audit.AuditDate.ToString('yyyy-MM-dd HH:mm:ss'))
Pages Scanned: $($Audit.PagesScanned)
Total Findings: $($Audit.Findings.Count)

Findings by Category:
"@
            foreach ($category in $Audit.IssuesByCategory.Keys | Sort-Object) {
                $report += "`n  $category : $($Audit.IssuesByCategory[$category])"
            }

            $report += "`n`n═══════════════════════════════════════════════════════════════`n"
            $report += " Findings by Priority`n"
            $report += "═══════════════════════════════════════════════════════════════`n"

            foreach ($priority in @("High", "Medium", "Low")) {
                $priorityFindings = $Audit.Findings | Where-Object { $_.Priority -eq $priority }
                if ($priorityFindings) {
                    $report += "`n## $priority Priority ($($priorityFindings.Count) findings):`n`n"
                    foreach ($finding in $priorityFindings) {
                        $report += "  X [$($finding.Category)] $($finding.FilePath)`n"
                        $report += "    Issue: $($finding.Issue)`n"
                        $report += "    Fix: $($finding.Remediation)`n`n"
                    }
                }
            }

            $report
        }
    }
}

try {
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host " FairDM Documentation Conformance Audit" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""

    $audit = [ConformanceAudit]::new()

    # Scan documentation files
    Write-Host "Scanning documentation files..." -ForegroundColor Gray
    $docsPath = Join-Path $RepoRoot "docs"
    $mdFiles = Get-MarkdownFiles -Path $docsPath

    $audit.PagesScanned = $mdFiles.Count
    Write-Host "Found $($mdFiles.Count) documentation files`n" -ForegroundColor Gray

    foreach ($file in $mdFiles) {
        if ($Verbose) {
            Write-Host "  Auditing: $($file.Name)" -ForegroundColor DarkGray
        }

        Test-SpecCrossReferences -FilePath $file.FullName -Audit $audit
        Test-FileLocation -FilePath $file.FullName -Audit $audit
        Test-ImageAltText -FilePath $file.FullName -Audit $audit
        Test-HeadingHierarchy -FilePath $file.FullName -Audit $audit
    }

    # Generate report
    $report = Format-AuditReport -Audit $audit -Format $OutputFormat

    if ($OutputFile) {
        $report | Out-File -FilePath $OutputFile -Encoding UTF8
        Write-Host "OK Audit report saved to: $OutputFile" -ForegroundColor Green
    }
    else {
        Write-Host $report
    }

    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host " Audit Complete" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Summary:" -ForegroundColor Cyan
    Write-Host "  Pages Scanned: $($audit.PagesScanned)" -ForegroundColor Gray
    Write-Host "  Total Findings: $($audit.Findings.Count)" -ForegroundColor Gray

    $highPriority = ($audit.Findings | Where-Object { $_.Priority -eq "High" }).Count
    $mediumPriority = ($audit.Findings | Where-Object { $_.Priority -eq "Medium" }).Count
    $lowPriority = ($audit.Findings | Where-Object { $_.Priority -eq "Low" }).Count

    if ($highPriority -gt 0) {
        Write-Host "  High Priority: $highPriority" -ForegroundColor Red
    }
    if ($mediumPriority -gt 0) {
        Write-Host "  Medium Priority: $mediumPriority" -ForegroundColor Yellow
    }
    if ($lowPriority -gt 0) {
        Write-Host "  Low Priority: $lowPriority" -ForegroundColor Cyan
    }

    exit 0
}
catch {
    Write-Host "X Audit failed with error: $_" -ForegroundColor Red
    exit 1
}
finally {
    Pop-Location
}
