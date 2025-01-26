#!/usr/bin/env bash


{
  echo "=== Deployment sync started ==="

  # Make sure we start in the correct directory
  cd "$(dirname "$0")/.."

  docker compose pull

  echo "=== Deployment sync finished ==="
} 2>&1 | sed "s/^/$(date '+%Y-%m-%d %H:%M:%S') /"
