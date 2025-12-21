#!/bin/bash
echo "🔧 Fixing database..."
echo ""
echo "Step 1: Stopping all containers..."
docker-compose down

echo ""
echo "Step 2: Removing database volume (to reset)..."
docker volume rm tor-unveil_postgres_data 2>/dev/null || echo "Volume doesn't exist yet"

echo ""
echo "Step 3: Starting containers with fresh database..."
docker-compose up -d

echo ""
echo "✅ Done! Database recreated with fixed migration."
echo ""
echo "Check status:"
echo "  docker-compose ps"
echo ""
echo "Check logs:"
echo "  docker-compose logs postgres"
