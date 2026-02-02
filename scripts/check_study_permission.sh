#!/bin/bash
# Study 권한 문제 진단 스크립트
# DB 연결: localhost:54486

PGPASSWORD='DevOps!323' psql -h localhost -p 54486 -U postgres -d drillquiz -f check_study_permission.sql
