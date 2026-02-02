#!/usr/bin/env bash
# Kubernetes production environment configuration

export BACKEND_URL="http://drillquiz-backend:8000"
export FRONTEND_URL="http://drillquiz-frontend:8080"
export PROJECT_ROOT="/workspace"

echo "Kubernetes production environment configured:"
echo "  BACKEND_URL: $BACKEND_URL"
echo "  FRONTEND_URL: $FRONTEND_URL"
echo "  PROJECT_ROOT: $PROJECT_ROOT"
