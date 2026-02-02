# Use Case Test Scripts 수정 완료 보고서

## 문제 진단

Jenkins에서 UC-1.6 (회원 탈퇴) 테스트가 실패한 원인:

1. **Shell 호환성 문제**: 스크립트가 `#!/bin/sh`를 사용했으나 Jenkins agent에는 bash 설치
2. **Python 코드 Quote Escaping 문제**: Shell의 single quote 안에서 Python 코드의 single quote가 충돌

## 적용된 수정사항

### 1. Shebang 변경 (20개 스크립트)
- **변경 전**: `#!/bin/sh`
- **변경 후**: `#!/bin/bash`
- **대상 파일**: 모든 usecase 스크립트 (uc-*.sh, fix-*.sh, uc-all.sh)

### 2. Python 코드 블록 Heredoc 변환 (12개 스크립트)

**변경 전**:
```bash
run_simple_test "테스트 이름" "
    cd $PROJECT_ROOT && # source venv/bin/activate (using system python) && python3 -c '
import os
import sys
sys.path.append('.')
# ... Python code ...
' > /dev/null
"
```

**변경 후**:
```bash
run_simple_test "테스트 이름" "
    cd $PROJECT_ROOT && python3 << 'PYEOF'
import os
import sys
sys.path.append('.')
# ... Python code ...
    PYEOF
"
```

**수정된 스크립트**:
- uc-1.6-withdrawal.sh (22줄 변경)
- uc-2.1-file-upload.sh (10줄 변경)
- uc-2.2-file-download.sh (10줄 변경)
- uc-3.1-exam-creation.sh (38줄 변경)
- uc-3.2-exam-taking.sh (42줄 변경)
- uc-3.3-exam-results.sh (34줄 변경)
- uc-3.4-wrong-notes.sh (34줄 변경)
- uc-4.1-study-creation.sh (42줄 변경)
- uc-4.2-study-members.sh (38줄 변경)
- uc-4.3-study-tasks.sh (38줄 변경)
- uc-5.1-voice-mode.sh (34줄 변경)
- uc-5.2-ai-mock-interview.sh (42줄 변경)

## Heredoc의 장점

1. **Quote Escaping 불필요**: Single/double quote를 그대로 사용 가능
2. **가독성 향상**: Python 코드가 명확하게 분리됨
3. **안정성**: Shell 파싱 오류 방지
4. **유지보수 용이**: Python 코드 수정이 간편

## CI/CD 환경 확인

`ci/k8s.sh` (Line 721)에서 bash 자동 설치 확인:
```bash
command -v bash >/dev/null 2>&1 || MISSING_TOOLS="$MISSING_TOOLS bash"
```

Jenkins agent에서 bash가 없으면 자동으로 설치됩니다:
- Alpine Linux: `apk add --no-cache bash`
- Debian/Ubuntu: `apt-get install -y bash`
- CentOS/RHEL: `yum install -y bash`

## 통계

- **총 변경 파일**: 20개
- **총 변경 라인**: 400줄 (200줄 삭제 + 200줄 추가)
- **Heredoc 변환**: 12개 스크립트
- **Shebang 변경**: 20개 스크립트

## 테스트 방법

로컬에서 테스트:
```bash
cd /Users/dhong/workspaces/drillquiz/usecase/scripts
./uc-1.6-withdrawal.sh
```

Jenkins에서 테스트:
- Jenkins Pipeline: `tz-drillquiz-usecase`
- 자동으로 bash 설치 및 스크립트 실행
- Heredoc 형식으로 Python 코드 오류 없이 실행

## 예상 결과

이제 UC-1.6 및 모든 usecase 테스트가 Jenkins에서 정상적으로 실행될 것으로 예상됩니다.

## 작성일

2025-10-06

## 작성자

AI Assistant (Claude Sonnet 4.5)

