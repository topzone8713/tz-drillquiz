#!/usr/bin/env bash
# Kubernetes QA environment configuration

export BACKEND_URL="http://drillquiz-backend-qa:8000"
export FRONTEND_URL="http://drillquiz-frontend-qa:8080"
export PROJECT_ROOT="/workspace"

echo "Kubernetes QA environment configured:"
echo "  BACKEND_URL: $BACKEND_URL"
echo "  FRONTEND_URL: $FRONTEND_URL"
echo "  PROJECT_ROOT: $PROJECT_ROOT"
