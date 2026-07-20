# launch_windows.ps1 - PowerShell script to check Docker and launch the application

$ErrorActionPreference = "Stop"

function Write-Header ($text) {
    Write-Host ""
    Write-Host ">>> $text" -ForegroundColor Cyan
}

function Write-Success ($text) {
    Write-Host "[SUCCESS] $text" -ForegroundColor Green
}

function Write-Info ($text) {
    Write-Host "[INFO] $text" -ForegroundColor Gray
}

function Write-WarningLocal ($text) {
    Write-Host "[WARNING] $text" -ForegroundColor Yellow
}

function Write-ErrorLocal ($text) {
    Write-Host "[ERROR] $text" -ForegroundColor Red
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# --- 1. Check if Docker Desktop is installed ---
Write-Header "Checking System Prerequisites..."

$dockerInstalled = $false
try {
    $null = Get-Command docker -ErrorAction SilentlyContinue
    $dockerInstalled = $true
} catch {}

if (-not $dockerInstalled -and (Test-Path "C:\Program Files\Docker\Docker\resources\bin\docker.exe")) {
    # Sometimes docker is not in PATH yet, but is installed in default location
    $env:Path += ";C:\Program Files\Docker\Docker\resources\bin"
    $dockerInstalled = $true
}

if (-not $dockerInstalled) {
    Write-WarningLocal "Docker Desktop is not installed on this machine."
    Write-Info "Docker Desktop is required to run the AI SDR Platform."
    
    $choice = Read-Host "Would you like to download and install Docker Desktop now? (Y/N)"
    if ($choice -imatch "^y") {
        Write-Header "Downloading Docker Desktop Installer..."
        $url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
        $installerPath = "$env:TEMP\DockerDesktopInstaller.exe"
        
        Write-Info "Downloading from $url..."
        Write-Info "This is a ~500MB download and may take a few minutes."
        
        try {
            Import-Module BitsTransfer
            Start-BitsTransfer -Source $url -Destination $installerPath -DisplayName "Docker Desktop Installer"
        } catch {
            Write-WarningLocal "BITS transfer failed. Falling back to Net.WebClient..."
            $webClient = New-Object System.Net.WebClient
            $webClient.DownloadFile($url, $installerPath)
        }
        
        Write-Header "Launching Docker Desktop Installer..."
        Write-Info "Please complete the installer wizard. Ensure WSL 2 component is checked if prompted."
        
        $process = Start-Process -FilePath $installerPath -ArgumentList "install" -Wait -PassThru
        
        Write-Success "Installer has completed."
        Write-WarningLocal "You may need to restart your computer to enable WSL 2 and virtualization."
        Write-Info "After restarting (if needed), please run 'start_windows.bat' again."
        Exit 0
    } else {
        Write-ErrorLocal "Docker Desktop installation was declined. Cannot run the platform."
        Exit 1
    }
} else {
    Write-Success "Docker Desktop is installed."
}

# --- 2. Check if Docker Daemon is running ---
Write-Header "Checking if Docker is running..."

function Test-DockerDaemon {
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $null = & docker info 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $oldPreference
    }
}

$dockerRunning = Test-DockerDaemon

if (-not $dockerRunning) {
    Write-WarningLocal "Docker Daemon is not running. Attempting to start Docker Desktop..."
    $paths = @(
        "C:\Program Files\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    )
    $started = $false
    foreach ($p in $paths) {
        if (Test-Path $p) {
            Write-Info "Starting: $p"
            Start-Process -FilePath $p
            $started = $true
            break
        }
    }
    if (-not $started) {
        Write-ErrorLocal "Could not locate 'Docker Desktop.exe' in default installation paths."
        Write-Info "Please start Docker Desktop manually, then run this script again."
        Exit 1
    }

    # Loop waiting for Docker to start up
    Write-Info "Waiting for Docker daemon to become responsive. This can take up to a minute..."
    for ($i = 1; $i -le 30; $i++) {
        Write-Info "Checking Docker status (attempt $i/30)..."
        if (Test-DockerDaemon) {
            $dockerRunning = $true
            break
        }
        Start-Sleep -Seconds 3
    }
}

if (-not $dockerRunning) {
    Write-ErrorLocal "Docker daemon failed to respond. Please make sure Docker Desktop is running and fully initialized."
    Exit 1
}

Write-Success "Docker daemon is active and responsive."

# --- 3. Build and Start Containers ---
Write-Header "Starting AI SDR Platform via Docker Compose..."
Write-Info "Running: docker compose up -d --build"

& docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-ErrorLocal "Docker Compose failed to start the application. See errors above."
    Exit 1
}

Write-Success "Containers are running in the background."

# --- 4. Wait for Services and Open Browser ---
Write-Header "Waiting for Web Frontend to respond..."
$portOpen = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $portOpen = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 2
}

Write-Success "AI SDR Platform is ready!"
Write-Host ""
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "  AI SDR PLATFORM ACCESS DETAILS:" -ForegroundColor Green
Write-Host "  --------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "  Web App (Frontend):   http://localhost:8080" -ForegroundColor Yellow
Write-Host "  API Docs (Backend):   http://localhost:8011/docs" -ForegroundColor Yellow
Write-Host "  Default Login Email:  admin@sdr.local" -ForegroundColor Cyan
Write-Host "  Default Password:     admin123" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Green
Write-Host ""

# Launch Browser
Write-Info "Launching application in your default browser..."
Start-Process "http://localhost:8080"
