# Pre-push hook for Windows (PowerShell)
# Runs the same checks as CI to prevent failures

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Running pre-push validation (same as CI)..." -ForegroundColor Cyan
Write-Host ""

# Run pre-commit on all files (same as CI lint job)
Write-Host "Running pre-commit checks..." -ForegroundColor Yellow
& poetry run pre-commit run --all-files --show-diff-on-failure

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Pre-commit checks failed!" -ForegroundColor Red
    Write-Host "Fix the issues above and try again." -ForegroundColor Red
    Write-Host ""
    Write-Host "Tip: Run 'poetry run invoke format' to auto-fix formatting issues" -ForegroundColor Yellow
    Write-Host "Or run 'poetry run invoke pre-push' to see all issues" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "SUCCESS: All pre-push checks passed!" -ForegroundColor Green
Write-Host "Safe to push to remote." -ForegroundColor Green
Write-Host ""

exit 0
