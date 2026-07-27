"""AI SDR Platform - packaging script.

Produces a double-click installable package for Windows and macOS:

    python package_project.py

Output: ai_sdr_platform_package.zip

The recipient unzips it and double-clicks start_windows.bat (Windows) or
start_mac.command (macOS). Docker Desktop is the only prerequisite - they do
NOT need Python, Node, or any of the services installed.

Design notes
------------
* Python source is compiled to .pyc and the .py files are deleted, so the
  shipped package contains no readable source.
* IMPORTANT: .pyc bytecode is Python-version specific. This script must run on
  the SAME minor version as the Docker base image (3.11). It refuses to run
  otherwise, because mismatched bytecode fails at import time inside the image.
* The React frontend is pre-built here (needs npm locally) and shipped as
  static files, so the recipient never needs Node.
* Discovery runs in `public` mode - no Apollo API key is embedded in the
  package. Nothing secret ships.
* The full local stack is packaged: OpenSearch, SearXNG, MetaRank, Temporal and
  Ollama, plus the API, follow-up worker and web UI. OpenSearch and SearXNG are
  included for parity with the local development environment and are pre-wired
  through environment variables, so enrichment starts working as soon as a
  search provider implementation is added to the codebase.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "package_temp"
INTERNAL = BUILD / ".internal"
ZIP_PATH = ROOT / "ai_sdr_platform_package.zip"

# Must match the Docker base image tag below.
REQUIRED_PY = (3, 11)
PY_IMAGE = "python:3.11-slim"

LLM_MODEL = "llama3.2:3b"

IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", ".venv", "venv", ".git",
    "*.db", "*.log", "tests", "evals", "node_modules", ".pytest_cache",
)


def log(msg: str) -> None:
    print(f"  {msg}")


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------
def check_python() -> None:
    actual = sys.version_info[:2]
    if actual != REQUIRED_PY:
        print(
            f"ERROR: this script must run on Python {REQUIRED_PY[0]}.{REQUIRED_PY[1]} "
            f"(found {actual[0]}.{actual[1]}).\n"
            f"       Compiled .pyc files only load on the matching interpreter,\n"
            f"       and the Docker image uses {PY_IMAGE}.\n"
            f"       Run with your 3.11 interpreter, e.g.:\n"
            f"           py -3.11 package_project.py"
        )
        raise SystemExit(1)
    log(f"Python {actual[0]}.{actual[1]} OK (matches {PY_IMAGE})")


def clean() -> None:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    INTERNAL.mkdir(parents=True)
    log(f"clean build dir: {BUILD}")


def copy_backend() -> None:
    shutil.copytree(ROOT / "ai_sdr_platform", INTERNAL / "ai_sdr_platform", ignore=IGNORE)
    # data/ holds local SQLite DBs; ship an empty dir so the app creates fresh ones.
    data_dir = INTERNAL / "ai_sdr_platform" / "data"
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True)
    (data_dir / ".gitkeep").write_text("")
    shutil.copy2(
        ROOT / "ai_sdr_platform" / "requirements.txt",
        INTERNAL / "requirements.txt",
    )
    log("copied backend source")


def compile_backend() -> None:
    subprocess.run(
        [sys.executable, "-m", "compileall", "-b", "-q", str(INTERNAL / "ai_sdr_platform")],
        check=True,
    )
    removed = 0
    for path in (INTERNAL / "ai_sdr_platform").rglob("*.py"):
        path.unlink()
        removed += 1
    for cache in (INTERNAL / "ai_sdr_platform").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    log(f"compiled to .pyc and removed {removed} .py source files")


def build_frontend() -> None:
    frontend = ROOT / "ai-sdr-frontend"
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if npm is None:
        print("ERROR: npm not found on PATH - needed to pre-build the React app.")
        raise SystemExit(1)

    if not (frontend / "node_modules").exists():
        log("installing frontend dependencies (first run, may take a few minutes)...")
        subprocess.run([npm, "install"], cwd=frontend, check=True, shell=False)

    log("building React frontend...")
    subprocess.run([npm, "run", "build"], cwd=frontend, check=True, shell=False)

    dist = frontend / "dist"
    if not dist.exists():
        print("ERROR: frontend build produced no dist/ folder.")
        raise SystemExit(1)
    shutil.copytree(dist, INTERNAL / "web")
    shutil.copy2(frontend / "nginx.conf", INTERNAL / "nginx.conf")
    log("frontend built and copied")


def copy_searxng() -> None:
    """Ship the SearXNG config that enables the JSON API and disables the limiter.

    Without this the container serves 403 to programmatic queries, which is the
    behaviour you hit when setting this up locally.
    """
    src = ROOT / "searxng" / "settings.yml"
    dest = INTERNAL / "searxng"
    dest.mkdir(parents=True, exist_ok=True)
    if src.exists():
        shutil.copy2(src, dest / "settings.yml")
        log("copied SearXNG settings.yml")
    else:
        (dest / "settings.yml").write_text(
            "use_default_settings: true\n"
            "server:\n"
            '  secret_key: "ai-sdr-packaged-searxng-secret"\n'
            "  limiter: false\n"
            "  image_proxy: false\n"
            "search:\n"
            "  formats:\n"
            "    - html\n"
            "    - json\n",
            encoding="utf-8",
        )
        log("generated default SearXNG settings.yml")


def copy_metarank() -> None:
    src = ROOT / "metarank" / "sdr"
    dest = INTERNAL / "metarank"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("config.yml", "seed-events.jsonl"):
        if (src / name).exists():
            shutil.copy2(src / name, dest / name)
    # MetaRank needs an events file to start; seed it if we have one.
    seed = dest / "seed-events.jsonl"
    events = dest / "events.jsonl"
    events.write_text(seed.read_text(encoding="utf-8") if seed.exists() else "", encoding="utf-8")
    log("copied MetaRank config + seed events")


# --------------------------------------------------------------------------
# Generated files
# --------------------------------------------------------------------------
def write_dockerfiles() -> None:
    (INTERNAL / "Dockerfile.api").write_text(
        f"""FROM {PY_IMAGE}

WORKDIR /app

COPY requirements.txt /app/requirements.txt

# requirements.txt is incomplete for a clean environment: several packages are
# imported at module level on the startup chain but are absent from it (they
# happen to be present in dev virtualenvs as transitive dependencies). Without
# these the API crashes on import with ModuleNotFoundError, and because the
# crash happens before ensure_default_admin() runs, no admin account is ever
# created and every login fails. Verified by static analysis of the import
# chain from ai_sdr_platform.src.api.app.
RUN pip install --no-cache-dir -r requirements.txt \
        requests \
        jinja2 \
        numpy \
        scikit-learn \
        joblib \
        lightgbm \
        temporalio

# Compiled bytecode only - no .py source is shipped.
COPY ai_sdr_platform /app/ai_sdr_platform

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8011

CMD ["uvicorn", "ai_sdr_platform.src.api.app:app", "--host", "0.0.0.0", "--port", "8011"]
""",
        encoding="utf-8",
    )

    (INTERNAL / "Dockerfile.web").write_text(
        """FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY web /usr/share/nginx/html

EXPOSE 80
""",
        encoding="utf-8",
    )
    log("wrote Dockerfiles")


def write_compose() -> None:
    (INTERNAL / "docker-compose.yml").write_text(
        f"""# AI SDR Platform - packaged stack.
# Discovery runs in public/mock mode; no API keys required.

# Without this, Compose names the project after its folder (".internal"), so
# every container appears as "internal-*" in Docker Desktop.
name: ai-sdr

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ai-sdr-ollama
    volumes:
      - ollama-data:/root/.ollama
    restart: unless-stopped

  # One-shot: pulls the local LLM the first time the stack starts.
  ollama-init:
    image: ollama/ollama:latest
    container_name: ai-sdr-ollama-init
    depends_on:
      - ollama
    environment:
      OLLAMA_HOST: http://ollama:11434
    entrypoint: ["/bin/sh", "-c", "sleep 8; ollama pull {LLM_MODEL}"]
    restart: "no"

  # Runs with an in-memory database. Writing to a mounted volume fails because
  # the image runs as a non-root user that cannot write to it, which sends the
  # container into a restart loop. Workflow history resets if the container is
  # recreated; the follow-up plans themselves live in the API's own database.
  temporal:
    image: temporalio/temporal:latest
    container_name: ai-sdr-temporal
    command: ["server", "start-dev", "--ip", "0.0.0.0"]
    ports:
      - "8233:8233"
    restart: unless-stopped

  # Evidence store for enrichment. Security plugin disabled for local use.
  opensearch:
    image: opensearchproject/opensearch:2
    container_name: ai-sdr-opensearch
    environment:
      discovery.type: single-node
      DISABLE_SECURITY_PLUGIN: "true"
      OPENSEARCH_JAVA_OPTS: -Xms512m -Xmx512m
      bootstrap.memory_lock: "false"
    ports:
      - "9200:9200"
    volumes:
      - opensearch-data:/usr/share/opensearch/data
    restart: unless-stopped

  # Public web search for enrichment. The mounted settings.yml enables the JSON
  # API and turns off the bot limiter, both of which are required for
  # programmatic queries (the default config returns 403).
  searxng:
    image: searxng/searxng:latest
    container_name: ai-sdr-searxng
    environment:
      BASE_URL: http://localhost:8088/
    ports:
      - "8088:8080"
    volumes:
      - ./searxng:/etc/searxng
    restart: unless-stopped

  metarank:
    image: metarank/metarank:latest
    container_name: ai-sdr-metarank
    volumes:
      - ./metarank:/opt/metarank
    command:
      - standalone
      - --config
      - /opt/metarank/config.yml
      - --data
      - /opt/metarank/events.jsonl
    restart: unless-stopped

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: ai-sdr-api
    ports:
      - "8011:8011"
    environment:
      SDR_AUTH_ENABLED: "true"
      SDR_JWT_SECRET: packaged-demo-secret-change-me-32chars
      SDR_CORS_ORIGINS: http://localhost:8080
      # Pinned explicitly so the packaged login is never ambiguous.
      SDR_DEFAULT_ADMIN_EMAIL: admin@sdr.local
      SDR_DEFAULT_ADMIN_PASSWORD: admin123
      SDR_DISCOVERY_PROVIDER: public
      SDR_DISCOVERY_SYNTHETIC_CONTACTS: "true"
      SDR_OUTREACH_PROVIDER: dry_run
      SDR_MEETING_PROVIDER: dry_run
      SDR_CRM_PROVIDER: dry_run
      SDR_CONVERSATION_LLM_BASE_URL: http://ollama:11434
      SDR_CONVERSATION_LLM_MODEL: {LLM_MODEL}
      SDR_ENRICHMENT_LLM_MODEL: {LLM_MODEL}
      SDR_INTELLIGENCE_METARANK_URL: http://metarank:8081
      SDR_OUTREACH_TEMPORAL_HOST: temporal:7233
      # Search wiring. These point at the bundled services using Docker's
      # internal DNS, so enrichment is fully configured the moment a search
      # provider implementation is added to the codebase.
      WEB_SEARCH_PROVIDER: searxng
      SEARXNG_BASE_URL: http://searxng:8080
      SDR_ENRICHMENT_SEARCH_PROVIDER: searxng
      SDR_ENRICHMENT_SEARXNG_URL: http://searxng:8080
      SDR_OPENSEARCH_URL: http://opensearch:9200
      OPENSEARCH_URL: http://opensearch:9200
      SDR_ENRICHMENT_COLLECTION: sdr_enrichment
      SDR_ENRICHMENT_TOP_K: "8"
    volumes:
      - sdr-data:/app/ai_sdr_platform/data
    depends_on:
      - ollama
      - temporal
      - metarank
      - opensearch
      - searxng
    restart: unless-stopped

  # Executes durable follow-up sequences against the API.
  worker:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: ai-sdr-worker
    command: ["python", "-m", "ai_sdr_platform.src.agents.follow_up.temporal_worker"]
    environment:
      SDR_API_BASE_URL: http://api:8011
      SDR_OUTREACH_TEMPORAL_HOST: temporal:7233
    depends_on:
      - api
      - temporal
    restart: unless-stopped

  web:
    build:
      context: .
      dockerfile: Dockerfile.web
    container_name: ai-sdr-web
    ports:
      - "8080:80"
    depends_on:
      - api
    restart: unless-stopped

volumes:
  ollama-data:
  opensearch-data:
  sdr-data:
""",
        encoding="utf-8",
    )
    log("wrote docker-compose.yml")


WIN_PS1 = r"""
# Native commands (docker) write progress to stderr. With ErrorActionPreference
# set to Stop, PowerShell turns that into a terminating NativeCommandError and
# kills the script before the retry loop can run - so keep it Continue here and
# check exit codes explicitly instead.
$ErrorActionPreference = "Continue"
$core = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-DockerEngine {
    try {
        $null = & docker info 2>&1
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Ok($m)   { Write-Host $m -ForegroundColor Green }
function Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Fail($m) { Write-Host $m -ForegroundColor Red }

Info ">>> Checking Docker Desktop..."
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    Fail "[ERROR] Docker Desktop is not installed."
    Write-Host "Install it from https://www.docker.com/products/docker-desktop/ then re-run this launcher."
    Start-Process "https://www.docker.com/products/docker-desktop/"
    exit 1
}
Ok "[OK] Docker is installed."

Info ">>> Checking the Docker engine is running..."
$running = $false
for ($i = 1; $i -le 60; $i++) {
    if (Test-DockerEngine) { $running = $true; break }
    if ($i -eq 1) {
        Warn "[..] Docker engine is not responding. Starting Docker Desktop..."
        $candidates = @(
            "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
            "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
            "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
        )
        $exe = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
        if ($exe) {
            Start-Process $exe
            Write-Host "     Docker Desktop is starting - this usually takes 30-60 seconds."
        } else {
            Warn "     Could not locate Docker Desktop. Please start it manually."
        }
    }
    Write-Host "     waiting for Docker engine ($i/60)..."
    Start-Sleep -Seconds 3
}
if (-not $running) {
    Fail "[ERROR] The Docker engine never became available."
    Write-Host "        Open Docker Desktop, wait until it reports 'Running', then run this launcher again."
    exit 1
}
Ok "[OK] Docker engine is responsive."

Info ">>> Building and starting the AI SDR Platform..."
Write-Host "     First run downloads images and the local LLM (~2GB) - this can take 5-15 minutes."
Write-Host "     Later runs start in seconds."
Push-Location $core
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { Pop-Location; Fail "[ERROR] docker compose failed. See the output above."; exit 1 }
Pop-Location
Ok "[OK] Containers are up."

Info ">>> Waiting for the web app..."
$ready = $false
for ($i = 1; $i -le 60; $i++) {
    try {
        if ((Invoke-WebRequest -Uri "http://localhost:8080" -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200) {
            $ready = $true; break
        }
    } catch { }
    Start-Sleep -Seconds 2
}
if ($ready) { Ok "[OK] Web app is responding." } else { Warn "[..] Still starting - the browser may need a refresh." }

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "  AI SDR PLATFORM IS RUNNING" -ForegroundColor Green
Write-Host "  ----------------------------------------------------------------------"
Write-Host "  Web App        : http://localhost:8080" -ForegroundColor Yellow
Write-Host "  API Docs       : http://localhost:8011/docs" -ForegroundColor Yellow
Write-Host "  Temporal UI    : http://localhost:8233" -ForegroundColor Yellow
Write-Host "  Login email    : admin@sdr.local" -ForegroundColor Cyan
Write-Host "  Login password : admin123" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Green
Write-Host ""

Start-Process "http://localhost:8080"

Write-Host "  Leave this window open while you use the app."
Write-Host ""
Write-Host "  Press any key to STOP the platform and shut everything down..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Info ">>> Stopping services..."
Push-Location $core
docker compose down
Pop-Location
Ok "[OK] All services stopped. Your data is saved for next time."
Start-Sleep -Seconds 2
""".lstrip()


WIN_BAT = """@echo off
title AI SDR Platform Launcher
mode con: cols=95 lines=32

echo =================================================================================
echo                       AI SDR PLATFORM LAUNCHER FOR WINDOWS
echo =================================================================================
echo.
echo  This will verify Docker Desktop, start the services, and open the app
echo  in your browser. The first run downloads images and may take 5-15 minutes.
echo.

attrib +h "%~dp0.internal" >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0.internal\\launch_windows.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Launcher failed. Please check the messages above.
    echo.
    pause
    exit /b %ERRORLEVEL%
)
"""


MAC_SH = r"""#!/bin/bash
clear
cd "$(dirname "$0")/.internal" || exit 1

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}=================================================================================${NC}"
echo -e "${CYAN}                        AI SDR PLATFORM LAUNCHER FOR MACOS${NC}"
echo -e "${CYAN}=================================================================================${NC}"
echo ""
echo "This will verify Docker Desktop, start the services, and open the app in your browser."
echo "The first run downloads images and a local LLM (~2GB) - allow 5-15 minutes."
echo ""

# --- 1. Docker installed? ---
echo -e "${CYAN}>>> Checking Docker Desktop...${NC}"
DOCKER_PATH="/Applications/Docker.app"
if [ -d "$DOCKER_PATH" ]; then
    export PATH="$PATH:$DOCKER_PATH/Contents/Resources/bin"
fi

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}[WARNING] Docker Desktop is not installed.${NC}"
    read -p "Download and install it now? (y/n): " choice
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        ARCH=$(uname -m)
        if [ "$ARCH" = "arm64" ]; then
            URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
            echo -e "${CYAN}[INFO] Apple Silicon detected.${NC}"
        else
            URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
            echo -e "${CYAN}[INFO] Intel CPU detected.${NC}"
        fi
        curl -L -o /tmp/Docker.dmg "$URL" || { echo -e "${RED}[ERROR] Download failed.${NC}"; exit 1; }
        hdiutil attach /tmp/Docker.dmg
        sudo cp -R /Volumes/Docker/Docker.app /Applications
        hdiutil detach /Volumes/Docker
        rm /tmp/Docker.dmg
        open -a Docker
        echo -e "${YELLOW}[IMPORTANT] Approve Docker's permission dialogs, wait until it says Running, then re-run this launcher.${NC}"
        exit 0
    else
        echo -e "${RED}[ERROR] Docker Desktop is required.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}[OK] Docker is installed.${NC}"

# --- 2. Docker engine running? ---
echo -e "${CYAN}>>> Checking the Docker engine...${NC}"
docker_running=false
for i in {1..40}; do
    if docker info &> /dev/null; then docker_running=true; break; fi
    if [ $i -eq 1 ]; then
        echo -e "${YELLOW}[..] Docker is not running. Launching Docker Desktop...${NC}"
        open -a Docker
    fi
    echo "     waiting for Docker engine ($i/40)..."
    sleep 3
done
if [ "$docker_running" = false ]; then
    echo -e "${RED}[ERROR] Docker engine did not start. Open Docker Desktop manually and retry.${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Docker engine is responsive.${NC}"

# --- 3. Start the stack ---
echo -e "${CYAN}>>> Building and starting the AI SDR Platform...${NC}"
docker compose up -d --build || { echo -e "${RED}[ERROR] docker compose failed.${NC}"; exit 1; }
echo -e "${GREEN}[OK] Containers are up.${NC}"

# --- 4. Wait for the web app ---
echo -e "${CYAN}>>> Waiting for the web app...${NC}"
for i in {1..60}; do
    if curl -s -f -o /dev/null http://localhost:8080; then break; fi
    sleep 2
done

echo ""
echo -e "${GREEN}========================================================================${NC}"
echo -e "${GREEN}  AI SDR PLATFORM IS RUNNING${NC}"
echo -e "${GREEN}  ----------------------------------------------------------------------${NC}"
echo -e "${YELLOW}  Web App        : http://localhost:8080${NC}"
echo -e "${YELLOW}  API Docs       : http://localhost:8011/docs${NC}"
echo -e "${YELLOW}  Temporal UI    : http://localhost:8233${NC}"
echo -e "${CYAN}  Login email    : admin@sdr.local${NC}"
echo -e "${CYAN}  Login password : admin123${NC}"
echo -e "${GREEN}========================================================================${NC}"
echo ""

open http://localhost:8080

echo "  Leave this window open while you use the app."
echo ""
read -n 1 -s -r -p "  Press any key to STOP the platform and shut everything down..."
echo ""
echo -e "${CYAN}>>> Stopping services...${NC}"
docker compose down
echo -e "${GREEN}[OK] All services stopped. Your data is saved for next time.${NC}"
sleep 2
"""


README = """# AI SDR Platform

## Requirements

**Docker Desktop** is the only thing you need installed.
Download: https://www.docker.com/products/docker-desktop/

You do NOT need Python, Node.js, or any database installed.

## Running it

- **Windows:** double-click `start_windows.bat`
- **macOS:**  double-click `start_mac.command`

The first launch downloads the container images and a local AI model
(about 2GB) - allow 5 to 15 minutes depending on your connection.
Later launches take only a few seconds.

Your browser opens automatically at http://localhost:8080

| Setting | Value |
|---|---|
| Web app | http://localhost:8080 |
| API docs | http://localhost:8011/docs |
| Temporal UI | http://localhost:8233 |
| Login email | admin@sdr.local |
| Login password | admin123 |

## Stopping it

Press any key in the launcher window. It shuts all the services down
cleanly. Your data is preserved between runs.

## Notes

Prospect discovery runs in **public/demo mode** - it uses the built-in
provider rather than a live Apollo account, so no API key is required.

Outreach, meetings, and CRM sync all run in **dry-run** mode: messages are
generated and approved through the UI but never actually sent.

## Troubleshooting

**"Docker engine did not start"** - open Docker Desktop manually, wait until
it reports *Running*, then launch again.

**Blank page or login fails** - the API may still be warming up. Wait a
minute and refresh.

**macOS "unidentified developer"** - right-click `start_mac.command`, choose
Open, then confirm.
"""


def write_launchers() -> None:
    (INTERNAL / "launch_windows.ps1").write_text(WIN_PS1, encoding="utf-8")
    (BUILD / "start_windows.bat").write_text(WIN_BAT, encoding="utf-8", newline="\r\n")

    mac = BUILD / "start_mac.command"
    mac.write_text(MAC_SH, encoding="utf-8", newline="\n")
    os.chmod(mac, 0o755)

    (BUILD / "README.txt").write_text(README, encoding="utf-8")
    log("wrote launchers + README")


def make_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for path in BUILD.rglob("*"):
            if path.is_file():
                z.write(path, path.relative_to(BUILD))
    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    log(f"created {ZIP_PATH.name} ({size_mb:.1f} MB)")


def main() -> int:
    print("=" * 70)
    print("AI SDR PLATFORM - PACKAGING")
    print("=" * 70)

    check_python()
    clean()
    copy_backend()
    compile_backend()
    build_frontend()
    copy_searxng()
    copy_metarank()
    write_dockerfiles()
    write_compose()
    write_launchers()
    make_zip()

    shutil.rmtree(BUILD, ignore_errors=True)

    print("=" * 70)
    print(f"DONE -> {ZIP_PATH}")
    print("=" * 70)
    print()
    print("Send that zip to anyone. They need only Docker Desktop, then:")
    print("  Windows : double-click start_windows.bat")
    print("  macOS   : double-click start_mac.command")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
