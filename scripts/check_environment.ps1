# ============================================================
# ECHO-AI — Environment Validation Script (PowerShell)
# ============================================================
# Usage: .\scripts\check_environment.ps1
# ============================================================

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ECHO-AI — Environment Validation" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$script:pass = 0
$script:warn = 0
$script:fail = 0

function Check-Tool($Name, $Cmd, $Required) {
    $result = $null
    $result = & cmd /c "$Cmd 2>&1"
    if ($LASTEXITCODE -eq 0 -and $result) {
        $version = ($result | Select-Object -First 1).ToString().Trim()
        Write-Host "  [OK]   $Name - $version" -ForegroundColor Green
        $script:pass++
    }
    else {
        if ($Required) {
            Write-Host "  [FAIL] $Name - Not found (REQUIRED)" -ForegroundColor Red
            $script:fail++
        }
        else {
            Write-Host "  [WARN] $Name - Not found (optional for Phase 1)" -ForegroundColor Yellow
            $script:warn++
        }
    }
}

Write-Host "  Checking development tools..." -ForegroundColor White
Write-Host ""

Check-Tool "Git" "git --version" $true
Check-Tool "Python" "python --version" $true
Check-Tool "Node.js" "node --version" $true
Check-Tool "npm" "npm --version" $true
Check-Tool "Docker" "docker --version" $false
Check-Tool "Docker Compose" "docker compose version" $false
Check-Tool "GitHub CLI" "gh --version" $false

Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "  Checking project structure..." -ForegroundColor White
Write-Host ""

$requiredFiles = @(".gitignore", ".env.example", "AGENTS.md", "PROJECT-CONTEXT.md", "README.md", "LICENSE")
$requiredDirs = @("frontend", "backend", "ml", "rag", "safety", "database", "tests", "docs", "scripts", "infrastructure", "data", "models", "logs")

foreach ($file in $requiredFiles) {
    if (Test-Path $file -PathType Leaf) {
        Write-Host "  [OK]   $file" -ForegroundColor Green
        $script:pass++
    }
    else {
        Write-Host "  [FAIL] $file - Missing" -ForegroundColor Red
        $script:fail++
    }
}

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir -PathType Container) {
        Write-Host "  [OK]   $dir/" -ForegroundColor Green
        $script:pass++
    }
    else {
        Write-Host "  [FAIL] $dir/ - Missing" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host ""
Write-Host "  Checking security..." -ForegroundColor White
Write-Host ""

if (Test-Path ".env" -PathType Leaf) {
    $tracked = & git ls-files .env 2>&1
    if ($tracked -and $tracked.ToString().Trim() -ne "") {
        Write-Host "  [FAIL] .env is tracked by Git - REMOVE IT" -ForegroundColor Red
        $script:fail++
    }
    else {
        Write-Host "  [OK]   .env exists but is git-ignored" -ForegroundColor Green
        $script:pass++
    }
}
else {
    Write-Host "  [OK]   No .env file (use .env.example as template)" -ForegroundColor Green
    $script:pass++
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
$summary = "  Results:  " + $script:pass + " passed  /  " + $script:warn + " warnings  /  " + $script:fail + " failed"
Write-Host $summary -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($script:fail -gt 0) {
    Write-Host "  Environment validation FAILED. Fix the issues above." -ForegroundColor Red
    exit 1
}
elseif ($script:warn -gt 0) {
    Write-Host "  Environment OK with warnings. Phase 1 can proceed." -ForegroundColor Yellow
    exit 0
}
else {
    Write-Host "  Environment validation PASSED. Ready for development." -ForegroundColor Green
    exit 0
}
