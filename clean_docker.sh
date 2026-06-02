#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# Docker Cleanup Script
# Stops and removes project containers, images, and volumes, with an option
# to perform a complete system-wide Docker prune.
# ──────────────────────────────────────────────────────────────────────────────

set -e

echo "🧹 Starting Docker cleanup..."

# 1. Project-specific cleanup
if [ -f "docker-compose.yml" ]; then
    echo "Stopping and removing project containers, networks, volumes, and local images..."
    docker compose down -v --rmi local
    echo "✓ Project cleanup complete."
else
    echo "⚠ No docker-compose.yml found in the current directory."
fi

echo ""
# 2. System-wide deep clean (Optional)
read -p "Do you want to perform a system-wide wipe (removes ALL containers, images, and volumes)? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping all running containers..."
    docker stop $(docker ps -aq) 2>/dev/null || true
    
    echo "Removing all containers..."
    docker rm $(docker ps -aq) 2>/dev/null || true
    
    echo "Removing all images..."
    docker rmi $(docker images -q) -f 2>/dev/null || true
    
    echo "Removing all volumes..."
    docker volume rm $(docker volume ls -q) 2>/dev/null || true
    
    echo "Running system prune..."
    docker system prune -a --volumes -f
    
    echo "✨ System-wide Docker wipe completed successfully!"
else
    echo "Skipped system-wide wipe."
fi
