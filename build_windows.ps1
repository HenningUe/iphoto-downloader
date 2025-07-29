#!/usr/bin/env powershell
# Windows build script for iPhoto Downloader Tool
# Builds a Windows executable using PyInstaller

param(
    [switch]$Clean,
    [switch]$Test,
    [switch]$CredentialsOnly,
    [switch]$MainOnly,
    [string]$OutputDir = "dist"
)

$ErrorActionPreference = "Stop"

Write-Host "Building iPhoto Downloader Tool for Windows" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Check if running in correct directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Error "Must run from repository root directory"
    exit 1
}

# Check if uv is available, install if not
$uvCommand = Get-Command "uv" -ErrorAction SilentlyContinue

# If not found globally, check in local virtual environment
if (-not $uvCommand -and (Test-Path ".venv\Scripts\uv.exe")) {
    $uvCommand = Get-Command ".venv\Scripts\uv.exe" -ErrorAction SilentlyContinue
    Write-Host "Found uv in virtual environment: $($uvCommand.Source)" -ForegroundColor Green
}

if (-not $uvCommand) {
    Write-Host "uv not found. Attempting to install..." -ForegroundColor Yellow
    
    # Check if pip is available
    $pipCommand = Get-Command "pip" -ErrorAction SilentlyContinue
    if (-not $pipCommand) {
        Write-Error "Neither uv nor pip is installed. Please install Python with pip first."
        exit 1
    }
    
    # Try to install uv using pip
    try {
        Write-Host "Installing uv using pip..." -ForegroundColor Yellow
        & $pipCommand install uv
        Write-Host "uv installed successfully" -ForegroundColor Green
        
        # Refresh PATH for current session
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
        
        # Check again
        $uvCommand = Get-Command "uv" -ErrorAction SilentlyContinue
        if (-not $uvCommand) {
            Write-Warning "uv was installed but not found in PATH. Trying to locate it..."
            
            # Try common installation paths
            $possiblePaths = @(
                "$env:USERPROFILE\AppData\Roaming\Python\Python*\Scripts\uv.exe",
                "$env:LOCALAPPDATA\Programs\Python\Python*\Scripts\uv.exe",
                "C:\Program Files\Python*\Scripts\uv.exe",
                "$env:USERPROFILE\.local\bin\uv.exe",
                ".venv\Scripts\uv.exe"
            )
            
            foreach ($path in $possiblePaths) {
                $foundUv = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($foundUv) {
                    $uvCommand = $foundUv
                    Write-Host "Found uv at: $($uvCommand.FullName)" -ForegroundColor Green
                    break
                }
            }
            
            if (-not $uvCommand) {
                Write-Error "uv installation failed or not found in PATH. Please install manually: pip install uv"
                exit 1
            }
        }
    }
    catch {
        Write-Error "Failed to install uv automatically. Please install manually: pip install uv. Error: $_"
        exit 1
    }
}

Write-Host "Using uv: $($uvCommand.Source)" -ForegroundColor Blue

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path $OutputDir) { Remove-Item -Recurse -Force $OutputDir }
    if (Test-Path "__pycache__") { Remove-Item -Recurse -Force "__pycache__" }
    Write-Host "Cleaned build directories" -ForegroundColor Green
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
try {
    if ($uvCommand.Source) {
        & $uvCommand sync --dev
    }
    else {
        uv sync --dev
    }
    Write-Host "Dependencies installed" -ForegroundColor Green
}
catch {
    Write-Error "Failed to install dependencies: $_"
    exit 1
}

# Verify required files exist
Write-Host "Verifying required files..." -ForegroundColor Yellow
$RequiredFiles = @("README.md", ".env.example", "iphoto_downloader.spec")
foreach ($file in $RequiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Error "Required file missing: $file"
        exit 1
    }
}
Write-Host "All required files present" -ForegroundColor Green

# Build executable with PyInstaller
Write-Host "Building Windows executable(s)..." -ForegroundColor Yellow

# Build main executable (unless CredentialsOnly is specified)
if (-not $CredentialsOnly) {
    Write-Host "Building main iPhoto Downloader executable..." -ForegroundColor Cyan
    try {
        if ($uvCommand.Source) {
            & $uvCommand run pyinstaller iphoto_downloader.spec --distpath $OutputDir --workpath build
        }
        else {
            uv run pyinstaller iphoto_downloader.spec --distpath $OutputDir --workpath build
        }
        Write-Host "Main executable build completed successfully" -ForegroundColor Green
    }
    catch {
        Write-Error "Main executable build failed: $_"
        exit 1
    }
}

# Build credentials manager executable (unless MainOnly is specified)
if (-not $MainOnly) {
    Write-Host "Building credentials manager executable..." -ForegroundColor Cyan
    try {
        if ($uvCommand.Source) {
            & $uvCommand run pyinstaller manage_credentials.spec --distpath $OutputDir --workpath build
        }
        else {
            uv run pyinstaller manage_credentials.spec --distpath $OutputDir --workpath build
        }
        Write-Host "Credentials manager build completed successfully" -ForegroundColor Green
    }
    catch {
        Write-Error "Credentials manager build failed: $_"
        exit 1
    }
}

# Verify build output
$MainExePath = Join-Path $OutputDir "iphoto_downloader.exe"
$CredExePath = Join-Path $OutputDir "manage_credentials.exe"

Write-Host "Build Information:" -ForegroundColor Cyan

# Check main executable
if (-not $CredentialsOnly -and (Test-Path $MainExePath)) {
    $MainExeSize = (Get-Item $MainExePath).Length / 1MB
    Write-Host "   Main Executable: $MainExePath" -ForegroundColor White
    Write-Host "   Main Size: $([math]::Round($MainExeSize, 2)) MB" -ForegroundColor White
}
elseif (-not $CredentialsOnly) {
    Write-Error "Main executable not found at expected location: $MainExePath"
    exit 1
}

# Check credentials manager executable
if (-not $MainOnly -and (Test-Path $CredExePath)) {
    $CredExeSize = (Get-Item $CredExePath).Length / 1MB
    Write-Host "   Credentials Manager: $CredExePath" -ForegroundColor White
    Write-Host "   Credentials Size: $([math]::Round($CredExeSize, 2)) MB" -ForegroundColor White
}
elseif (-not $MainOnly) {
    Write-Error "Credentials manager executable not found at expected location: $CredExePath"
    exit 1
}

# Test executable if requested
if ($Test) {
    Write-Host "Testing executable..." -ForegroundColor Yellow
    
    # Test basic startup (should exit quickly in Delivered mode without settings)
    try {
        $TestOutput = & $ExePath --help 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Executable starts successfully" -ForegroundColor Green
        }
        else {
            Write-Warning "Executable exit code: $LASTEXITCODE"
        }
    }
    catch {
        Write-Warning "Could not test executable: $_"
    }
    
    # Check embedded resources
    Write-Host "Checking embedded resources..." -ForegroundColor Yellow
    $TempSettingsDir = Join-Path $env:TEMP "icloud_test_settings"
    if (Test-Path $TempSettingsDir) {
        Remove-Item -Recurse -Force $TempSettingsDir
    }
    
    # Note: This would require modifying the app to accept a test settings dir
    Write-Host "Resource testing requires manual verification" -ForegroundColor Blue
}

Write-Host ""
Write-Host "Windows build completed successfully!" -ForegroundColor Green
Write-Host "Output location: $OutputDir" -ForegroundColor White
Write-Host "Ready for distribution" -ForegroundColor Green

# Display next steps
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Test the executable on a clean Windows system" -ForegroundColor White
Write-Host "2. Verify delivery artifacts creation in Delivered mode" -ForegroundColor White
Write-Host "3. Test 2FA functionality and Pushover notifications" -ForegroundColor White
Write-Host "4. Package for distribution (installer, zip, etc.)" -ForegroundColor White
