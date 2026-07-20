#!/bin/bash

# Clear terminal screen
clear

# Change directory to the folder containing this script
cd "$(dirname "$0")"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=================================================================================${NC}"
echo -e "${CYAN}                      AI SDR PLATFORM LAUNCHER FOR MACOS${NC}"
echo -e "${CYAN}=================================================================================${NC}"
echo ""
echo "This launcher will verify Docker Desktop, start it if needed, deploy the services,"
echo "and launch the application in your web browser."
echo ""
echo "Please wait..."
echo ""

# --- 1. Check if Docker Desktop is installed ---
echo -e "${CYAN}>>> Checking System Prerequisites...${NC}"

DOCKER_PATH="/Applications/Docker.app"
if [ -d "$DOCKER_PATH" ]; then
    export PATH="$PATH:$DOCKER_PATH/Contents/Resources/bin"
fi

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}[WARNING] Docker Desktop is not installed on this machine.${NC}"
    echo "Docker Desktop is required to run the AI SDR Platform."
    echo ""
    read -p "Would you like to download and install Docker Desktop now? (y/n): " install_choice
    
    if [[ "$install_choice" =~ ^[Yy]$ ]]; then
        ARCH=$(uname -m)
        if [ "$ARCH" = "arm64" ]; then
            echo -e "${CYAN}[INFO] Apple Silicon (M1/M2/M3) detected.${NC}"
            URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
        else
            echo -e "${CYAN}[INFO] Intel CPU detected.${NC}"
            URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
        fi
        
        echo -e "${CYAN}>>> Downloading Docker Desktop Installer...${NC}"
        echo "Downloading from $URL..."
        echo "This is a ~600MB download and may take a few minutes."
        
        curl -L -o /tmp/Docker.dmg "$URL"
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}[ERROR] Failed to download Docker Desktop.${NC}"
            exit 1
        fi
        
        echo -e "${CYAN}>>> Mounting installer image...${NC}"
        hdiutil attach /tmp/Docker.dmg
        
        echo -e "${CYAN}>>> Copying Docker to Applications directory...${NC}"
        echo "This may ask for your password or prompt for drag-and-drop..."
        sudo cp -R /Volumes/Docker/Docker.app /Applications
        
        echo -e "${CYAN}>>> Unmounting installer image...${NC}"
        hdiutil detach /Volumes/Docker
        rm /tmp/Docker.dmg
        
        echo -e "${GREEN}[SUCCESS] Docker Desktop installed successfully!${NC}"
        echo "Starting Docker Desktop..."
        open -a Docker
        
        echo -e "${YELLOW}[IMPORTANT] Please approve any system permission dialogs from Docker Desktop.${NC}"
        echo "Once Docker Desktop is fully running and active, please re-run this script."
        exit 0
    else
        echo -e "${RED}[ERROR] Docker Desktop installation declined. Cannot run the application.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}[SUCCESS] Docker is installed.${NC}"
fi

# --- 2. Check if Docker Daemon is running ---
echo -e "${CYAN}>>> Checking if Docker is running...${NC}"

docker_running=false
for i in {1..30}; do
    if docker info &> /dev/null; then
        docker_running=true
        break
    fi
    
    if [ $i -eq 1 ]; then
        echo -e "${YELLOW}[WARNING] Docker is not running. Launching Docker Desktop...${NC}"
        open -a Docker
    fi
    
    echo -e "${NC}[INFO] Waiting for Docker daemon to become responsive (attempt $i/30)...${NC}"
    sleep 3
done

if [ "$docker_running" = false ]; then
    echo -e "${RED}[ERROR] Docker daemon failed to respond. Please open Docker Desktop manually and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}[SUCCESS] Docker daemon is active and responsive.${NC}"

# --- 3. Build and Start Containers ---
echo -e "${CYAN}>>> Starting AI SDR Platform via Docker Compose...${NC}"
echo "Running: docker compose up -d --build"

docker compose up -d --build

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Docker Compose failed to start the application. See errors above.${NC}"
    exit 1
fi

echo -e "${GREEN}[SUCCESS] Containers are running in the background.${NC}"

# --- 4. Wait for Services and Open Browser ---
echo -e "${CYAN}>>> Waiting for Web Frontend to respond...${NC}"
web_ready=false
for i in {1..15}; do
    if curl -s -f -o /dev/null http://localhost:8080; then
        web_ready=true
        break
    fi
    sleep 2
done

echo -e "${GREEN}[SUCCESS] AI SDR Platform is ready!${NC}"
echo ""
echo -e "${GREEN}========================================================================${NC}"
echo -e "${GREEN}  AI SDR PLATFORM ACCESS DETAILS:${NC}"
echo -e "${GREEN}  --------------------------------------------------------------------${NC}"
echo -e "${YELLOW}  Web App (Frontend):   http://localhost:8080${NC}"
echo -e "${YELLOW}  API Docs (Backend):   http://localhost:8011/docs${NC}"
echo -e "${CYAN}  Default Login Email:  admin@sdr.local${NC}"
echo -e "${CYAN}  Default Password:     admin123${NC}"
echo -e "${GREEN}========================================================================${NC}"
echo ""

echo "Launching application in your default browser..."
open http://localhost:8080
