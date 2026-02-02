-- Study 권한 문제 진단 SQL
-- study-detail/24에서 doohee323@gmail.com 사용자의 권한을 확인

\set email 'doohee323@gmail.com'
\set study_id 24

\echo '============================================================'
\echo 'Study 권한 진단: Study ID ' :study_id
\echo '사용자 이메일: ' :email
\echo '============================================================'

-- 1. 사용자 정보
\echo ''
\echo '[1] 사용자 정보:'
SELECT 
    id, 
    username, 
    email, 
    is_superuser, 
    is_staff
FROM quiz_user
WHERE email = :'email';

-- 2. UserProfile 정보
\echo ''
\echo '[2] UserProfile 정보:'
SELECT 
    up.user_id,
    up.role,
    u.username,
    u.email
FROM quiz_userprofile up
JOIN quiz_user u ON up.user_id = u.id
WHERE u.email = :'email';

-- 3. Study 정보
\echo ''
\echo '[3] Study 정보:'
SELECT 
    s.id,
    s.title_ko,
    s.title_en,
    s.is_public,
    s.created_by_id,
    creator.username as creator_username,
    creator.email as creator_email
FROM quiz_study s
LEFT JOIN quiz_user creator ON s.created_by_id = creator.id
WHERE s.id = :study_id;

-- 4. 현재 사용자가 Study 생성자인지 확인
\echo ''
\echo '[4] Study 생성자 확인:'
SELECT 
    s.id as study_id,
    s.created_by_id,
    u.id as user_id,
    u.email,
    CASE 
        WHEN s.created_by_id = u.id THEN 'YES'
        ELSE 'NO'
    END as is_creator
FROM quiz_study s
CROSS JOIN quiz_user u
WHERE s.id = :study_id 
  AND u.email = :'email';

-- 5. Member 관계 확인
\echo ''
\echo '[5] Member 관계 확인:'
SELECT 
    m.id as member_id,
    m.user_id,
    m.study_id,
    m.role,
    m.is_active,
    m.joined_at,
    u.username,
    u.email,
    CASE 
        WHEN m.is_active = true AND m.role IN ('study_admin', 'study_leader') THEN 'YES'
        ELSE 'NO'
    END as has_admin_permission
FROM quiz_member m
JOIN quiz_user u ON m.user_id = u.id
WHERE m.study_id = :study_id 
  AND u.email = :'email';

-- 6. 전체 멤버 목록 (참고용)
\echo ''
\echo '[6] 전체 멤버 목록 (Study ID ' :study_id '):'
SELECT 
    m.id as member_id,
    m.user_id,
    u.username,
    u.email,
    m.role,
    m.is_active,
    m.joined_at
FROM quiz_member m
JOIN quiz_user u ON m.user_id = u.id
WHERE m.study_id = :study_id
ORDER BY m.joined_at
LIMIT 10;

-- 7. 권한 요약
\echo ''
\echo '============================================================'
\echo '[권한 요약]'
\echo '============================================================'

WITH user_info AS (
    SELECT 
        u.id as user_id,
        u.is_superuser,
        COALESCE(up.role, 'N/A') as profile_role
    FROM quiz_user u
    LEFT JOIN quiz_userprofile up ON u.id = up.user_id
    WHERE u.email = :'email'
),
study_info AS (
    SELECT 
        id as study_id,
        created_by_id
    FROM quiz_study
    WHERE id = :study_id
),
member_info AS (
    SELECT 
        m.user_id,
        m.role,
        m.is_active,
        CASE 
            WHEN m.is_active = true AND m.role IN ('study_admin', 'study_leader') THEN true
            ELSE false
        END as is_study_admin
    FROM quiz_member m
    JOIN quiz_user u ON m.user_id = u.id
    WHERE m.study_id = :study_id 
      AND u.email = :'email'
)
SELECT 
    ui.user_id,
    ui.is_superuser as is_global_admin,
    CASE 
        WHEN ui.is_superuser = true OR ui.profile_role = 'admin_role' THEN 'YES'
        ELSE 'NO'
    END as has_global_admin,
    si.created_by_id,
    CASE 
        WHEN si.created_by_id = ui.user_id THEN 'YES'
        ELSE 'NO'
    END as is_creator,
    COALESCE(mi.role, 'N/A') as member_role,
    COALESCE(mi.is_active::text, 'N/A') as is_member_active,
    CASE 
        WHEN COALESCE(mi.is_study_admin, false) = true THEN 'YES'
        ELSE 'NO'
    END as is_study_admin,
    CASE 
        WHEN ui.is_superuser = true 
             OR ui.profile_role = 'admin_role'
             OR si.created_by_id = ui.user_id
             OR COALESCE(mi.is_study_admin, false) = true 
        THEN 'YES'
        ELSE 'NO'
    END as can_edit
FROM user_info ui
CROSS JOIN study_info si
LEFT JOIN member_info mi ON ui.user_id = mi.user_id;

-- 8. 해결 방안 SQL (실행하지 않음, 참고용)
\echo ''
\echo '============================================================'
\echo '[해결 방안 SQL]'
\echo '============================================================'
\echo ''
\echo '-- 1. Study 생성자로 변경:'
\echo '-- UPDATE quiz_study SET created_by_id = (SELECT id FROM quiz_user WHERE email = ''' :email ''') WHERE id = ' :study_id ';'
\echo ''
\echo '-- 2. Study 관리자로 추가 (멤버가 없는 경우):'
\echo '-- INSERT INTO quiz_member (study_id, user_id, role, is_active, joined_at)'
\echo '-- SELECT ' :study_id ', id, ''study_admin'', true, NOW()'
\echo '-- FROM quiz_user WHERE email = ''' :email ''';'
\echo ''
\echo '-- 3. Study 관리자 역할 변경 (멤버가 있는 경우):'
\echo '-- UPDATE quiz_member SET role = ''study_admin'', is_active = true'
\echo '-- WHERE study_id = ' :study_id ' AND user_id = (SELECT id FROM quiz_user WHERE email = ''' :email ''');'
\echo ''
\echo '-- 4. 전역 관리자로 변경:'
\echo '-- UPDATE quiz_user SET is_superuser = true WHERE email = ''' :email ''';'
\echo ''
\echo '-- 또는 UserProfile에 admin_role 부여:'
\echo '-- INSERT INTO quiz_userprofile (user_id, role)'
\echo '-- SELECT id, ''admin_role'' FROM quiz_user WHERE email = ''' :email ''''
\echo '-- ON CONFLICT (user_id) DO UPDATE SET role = ''admin_role'';'


