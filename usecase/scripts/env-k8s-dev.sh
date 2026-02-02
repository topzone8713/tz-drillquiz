#!/usr/bin/env bash
# Kubernetes development environment configuration

export BACKEND_URL="http://drillquiz-backend-dev:8000"
export FRONTEND_URL="http://drillquiz-frontend-dev:8080"
export PROJECT_ROOT="/workspace"

echo "Kubernetes development environment configured:"
echo "  BACKEND_URL: $BACKEND_URL"
echo "  FRONTEND_URL: $FRONTEND_URL"
echo "  PROJECT_ROOT: $PROJECT_ROOT"
