#!/usr/bin/env python3
"""
포트포워딩된 k8s dev DB를 대상으로 다국어 마이그레이션 적용 여부와
`quiz_study`의 `title_ko`/`title_en` 상태를 읽기 전용으로 점검합니다.

기본 접속 정보 (포트포워딩 필요):
  - host: localhost (변경 가능: --host)
  - port: 57786 (변경 가능: --port)
  - db:   drillquiz (변경 가능: --db)
  - user: admin (변경 가능: --user)
  - pass: DevOps!323 (변경 가능: --password)

데이터 변경은 수행하지 않습니다.
"""

import sys
import os
import argparse
from typing import Iterable, Set

import psycopg2
from psycopg2.extras import RealDictCursor

def parse_args():
    parser = argparse.ArgumentParser(description="k8s dev DB 읽기 전용 점검")
    parser.add_argument("--host", default=os.environ.get("DB_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("DB_PORT", 57786)))
    parser.add_argument("--db", default=os.environ.get("DB_NAME", "drillquiz"))
    parser.add_argument("--user", default=os.environ.get("DB_USER", "admin"))
    parser.add_argument("--password", default=os.environ.get("DB_PASSWORD", "DevOps!323"))
    return parser.parse_args()


def fetch_all(cursor, query: str, params: Iterable = None):
    cursor.execute(query, params or [])
    return cursor.fetchall()


def check_migrations(cursor) -> None:
    print("=== 1) 마이그레이션 적용 여부 (quiz 앱) ===")
    expected = (
        "0049_comprehensive_multilingual_migration",
        "0050_safe_multilingual_migration",
        "0051_merge_20250818_1547",
    )
    rows = fetch_all(
        cursor,
        """
        SELECT name
        FROM django_migrations
        WHERE app = 'quiz' AND name = ANY(%s)
        ORDER BY name
        """,
        (list(expected),),
    )
    applied: Set[str] = {r[0] for r in rows}
    for name in expected:
        print(f"- {name}: {'APPLIED' if name in applied else 'PENDING'}")
    print()


def check_schema(cursor) -> None:
    print("=== 2) 스키마 확인: quiz_study 다국어 컬럼 존재 여부 ===")
    rows = fetch_all(
        cursor,
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'quiz_study'
        """,
    )
    existing = {r[0] for r in rows}
    required = [
        "title_ko",
        "title_en",
        "goal_ko",
        "goal_en",
        "created_language",
        "is_ko_complete",
        "is_en_complete",
    ]
    missing = [c for c in required if c not in existing]
    if missing:
        print(f"- 누락 컬럼: {missing}")
    else:
        print("- OK (필요 컬럼 전부 존재)")
    print()


def check_data(cursor) -> None:
    print("=== 3) 데이터 상태 (읽기 전용) ===")
    # 집계
    cursor.execute(
        """
        SELECT
          COUNT(*) AS total,
          SUM(CASE WHEN NULLIF(BTRIM(title_ko), '') IS NOT NULL THEN 1 ELSE 0 END) AS ko_non_empty,
          SUM(CASE WHEN NULLIF(BTRIM(title_en), '') IS NOT NULL THEN 1 ELSE 0 END) AS en_non_empty
        FROM quiz_study
        """
    )
    total, ko_non_empty, en_non_empty = cursor.fetchone()
    print(f"- total={total}, title_ko 채워짐={ko_non_empty}, title_en 채워짐={en_non_empty}")

    # 샘플 출력
    print("\n샘플 10건 (id, title_ko, title_en):")
    rows = fetch_all(
        cursor,
        """
        SELECT id, title_ko, title_en
        FROM quiz_study
        ORDER BY id
        LIMIT 10
        """,
    )
    for r in rows:
        print(r)
    print()


def main() -> int:
    args = parse_args()
    print("🚀 k8s dev DB 읽기 전용 점검 시작 (포트포워딩 필요)")
    try:
        conn = psycopg2.connect(
            host=args.host,
            port=args.port,
            dbname=args.db,
            user=args.user,
            password=args.password,
        )
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        print(f"ℹ️ 확인: {args.host}:{args.port}, db={args.db}, user={args.user}")
        return 1

    try:
        with conn:
            with conn.cursor() as cursor:
                check_migrations(cursor)
                check_schema(cursor)
                check_data(cursor)
    finally:
        conn.close()

    print("✅ 점검 완료 (데이터 변경 없음)")
    return 0


if __name__ == "__main__":
    sys.exit(main())


