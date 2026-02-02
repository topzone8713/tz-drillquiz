# 사용자 나이, 사용자 Rating, 시험 난이도, 문제 난이도의 관계

## 개요

이 문서는 사용자의 나이, 사용자 rating, 시험의 난이도, 문제의 난이도 간의 관계를 정리합니다.

## 1. 사용자 나이 → 사용자 Rating

### 계산 방식
- **함수**: `calculate_age_rating(date_of_birth)` (`quiz/utils/user_utils.py`)
- **입력**: 사용자의 생년월일 (`date_of_birth`)
- **출력**: 사용자의 연령 등급 (`age_rating`)

### 등급 기준
| 나이 | Rating | 설명 |
|------|--------|------|
| 4세 미만 | `4+` | 누구나 사용 가능, 폭력·성적·도박·웹 접근·UGC가 거의 없어야 허용됨 |
| 4세 이상 9세 미만 | `9+` | 경미한 만화적/가벼운 요소 허용, 위험 기능은 여전히 제한적 |
| 9세 이상 12세 미만 | `12+` | UGC 가능, 소셜 기능 가능, 제한된 웹 접근 가능, 약간의 현실적 폭력·공포·경쟁적 요소 허용 |
| 12세 이상 | `17+` | 성인 콘텐츠, 강한 폭력, 완전한 웹 브라우징, 무제한 UGC, 메시징/DM, 도박, 뉴스/웹 전체 접근 등 |
| 생년월일 없음 | `17+` | 기본값 (기존 사용자 호환성) |

### 예시
```python
# 2012년생 (12세) → '12+'
# 2015년생 (9세) → '9+'
# 2020년생 (4세) → '4+'
# 생년월일 없음 → '17+'
```

---

## 2. 사용자 Rating → 시험 기본 난이도

### 계산 방식
- **함수**: `get_default_difficulty_by_age_rating(age_rating)` (`quiz/utils/exam_utils.py`)
- **입력**: 사용자의 연령 등급 (`age_rating`)
- **출력**: 시험의 기본 난이도 (`exam_difficulty`, 1~10)

### 기본 난이도 매핑
| 사용자 Rating | 기본 시험 난이도 | 설명 |
|---------------|------------------|------|
| `4+` | **3** | 낮은 난이도 (어린 사용자를 위한 쉬운 문제) |
| `9+` | **4** | 낮은 난이도 |
| `12+` | **5** | 중간 난이도 |
| `17+` | **7** | 높은 난이도 (성인 사용자를 위한 도전적인 문제) |
| 없음 | **5** | 기본값 |

### 사용 위치
- **프론트엔드**: `TextToQuestions.vue` - 시험 생성 시 기본 난이도 설정
- **백엔드**: `text_to_questions` API - 사용자가 난이도를 지정하지 않은 경우

---

## 3. 시험 내용 → 시험 Age Rating

### 계산 방식
- **함수**: 
  - `estimate_exam_age_rating(exam, questions=None)` - 시험 생성 후 최종 평가
  - `estimate_age_rating_from_text(text_content, title=None, description=None)` - 텍스트 분석 시 초기 평가
- **입력**: 시험의 제목, 설명, 문제 내용 (텍스트)
- **출력**: 시험의 연령 등급 (`age_rating`)

### 평가 기준
시험 내용을 키워드 분석하여 연령 등급을 추정합니다:

1. **성인 콘텐츠 키워드** 발견 → `17+` (즉시 반환)
   - 폭력, 성적, 도박, 마약, 알코올 관련 키워드

2. **공포/경쟁적 콘텐츠** 많음 → `12+`
   - 공포 키워드 > 2개 또는 경쟁적 키워드 > 3개

3. **공포/경쟁적 콘텐츠** 조금 → `9+`
   - 공포 키워드 > 0개 또는 경쟁적 키워드 > 0개

4. **교육적 콘텐츠** 많음 → `4+`
   - 교육적 키워드 > 5개

5. **기본값** → `9+`

### 텍스트 길이/복잡도 조정
- 매우 짧고 단순한 텍스트 (길이 < 100자, 단어 < 20개) → 등급 낮춤
- 매우 긴 텍스트 (길이 > 5000자 또는 단어 > 500개) → 등급 높임

---

## 4. 시험 Age Rating → 시험 난이도 조정

### 계산 방식
- **함수**: `adjust_exam_difficulty_by_age_rating(exam_difficulty, age_rating)` (`quiz/utils/exam_utils.py`)
- **입력**: 
  - 현재 시험 난이도 (`exam_difficulty`, 1~10)
  - 시험의 연령 등급 (`age_rating`)
- **출력**: 조정된 시험 난이도 (1~10 범위 내)

### 조정 규칙
| 시험 Age Rating | 조정 방식 | 예시 |
|-----------------|-----------|------|
| `4+` | **유지** | 5 → 5, 10 → 10 |
| `9+` | **-3** (최소 1) | 10 → 7, 8 → 5, 5 → 2, 3 → 1 |
| `12+` | **-1** (최소 1) | 10 → 9, 8 → 7, 5 → 4, 2 → 1 |
| `17+` | **+2** (최대 10) | 2 → 4, 3 → 5, 5 → 7, 8 → 10, 10 → 10 |

### 사용 위치
- **백엔드**: `text_to_questions` API - 문제 생성 **전**에 시험 난이도 조정
  - 텍스트 분석으로 초기 `age_rating` 추정
  - 추정된 `age_rating`에 따라 `exam_difficulty` 조정
  - 조정된 `exam_difficulty`로 문제 생성 (easy/medium/hard 분배)

---

## 5. 시험 난이도 → 문제 난이도 분배

### 계산 방식
- **함수**: `calculate_difficulty_distribution(exam_difficulty, question_count)` (`quiz/views/exam_views.py`)
- **입력**: 
  - 시험 난이도 (`exam_difficulty`, 1~10)
  - 생성할 문제 수 (`question_count`)
- **출력**: `{'easy': count, 'medium': count, 'hard': count}`

### 분배 규칙

#### 극단값
- **난이도 1**: 100% easy (쉬운 문제만)
- **난이도 10**: 100% hard (어려운 문제만)

#### 중간값 (난이도 2~9)
- **Medium**: 항상 40% 고정
- **Easy/Hard**: 나머지 60%를 난이도에 따라 분배
  - 난이도가 낮을수록 (1에 가까울수록) easy 비율 증가
  - 난이도가 높을수록 (10에 가까울수록) hard 비율 증가

### 분배 예시

| 시험 난이도 | Easy | Medium | Hard | 설명 |
|-------------|------|--------|------|------|
| 1 | 100% | 0% | 0% | 쉬운 문제만 |
| 2 | 45% | 40% | 15% | 쉬운 문제 중심 |
| 5 | 30% | 40% | 30% | 균형잡힌 분배 |
| 8 | 15% | 40% | 45% | 어려운 문제 중심 |
| 10 | 0% | 0% | 100% | 어려운 문제만 |

### 계산 공식
```python
# Medium은 항상 40% 고정
medium_ratio = 0.4
remaining_ratio = 0.6  # Easy + Hard

# Easy 비율: (10 - exam_difficulty) / 9 * 0.6
easy_ratio = (10 - exam_difficulty) / 9 * remaining_ratio

# Hard 비율: (exam_difficulty - 1) / 9 * 0.6
hard_ratio = (exam_difficulty - 1) / 9 * remaining_ratio
```

### 문제 난이도 필드
- **Question 모델**: `difficulty` 필드 (CharField, 'Easy', 'Medium', 'Hard' 등)
- **ExamResult 모델**: `question_difficulty` 필드 (문제 풀이 시 저장)

---

## 전체 흐름도

```
1. 사용자 가입/로그인
   └─> 생년월일 (date_of_birth)
       └─> calculate_age_rating()
           └─> 사용자 age_rating ('4+', '9+', '12+', '17+')

2. 시험 생성 화면 (TextToQuestions)
   └─> 사용자 age_rating
       └─> get_default_difficulty_by_age_rating()
           └─> 기본 exam_difficulty 설정 (4+: 3, 9+: 4, 12+: 5, 17+: 7)

3. 시험 생성 API (text_to_questions)
   ├─> 텍스트 내용 입력
   │   └─> estimate_age_rating_from_text()
   │       └─> 초기 시험 age_rating 추정
   │
   ├─> 사용자가 exam_difficulty 지정 안 함
   │   └─> get_default_difficulty_by_age_rating(사용자 age_rating)
   │       └─> 기본 exam_difficulty 설정
   │
   ├─> adjust_exam_difficulty_by_age_rating(exam_difficulty, 시험 age_rating)
   │   └─> 시험 age_rating에 따라 exam_difficulty 조정
   │       └─> 4+: 유지, 9+: -3, 12+: -1, 17+: +2
   │
   ├─> generate_questions_from_text(exam_difficulty)
   │   └─> 조정된 exam_difficulty로 문제 생성
   │       └─> easy/medium/hard 분배 결정
   │
   └─> estimate_exam_age_rating(exam, questions)
       └─> 최종 시험 age_rating 설정 (DB 저장)
```

---

## 주요 함수 요약

| 함수 | 위치 | 입력 | 출력 | 용도 |
|------|------|------|------|------|
| `calculate_age_rating` | `quiz/utils/user_utils.py` | `date_of_birth` | `age_rating` | 사용자 나이 → 사용자 rating |
| `get_default_difficulty_by_age_rating` | `quiz/utils/exam_utils.py` | `age_rating` | `exam_difficulty` (1~10) | 사용자 rating → 기본 시험 난이도 |
| `estimate_age_rating_from_text` | `quiz/utils/exam_utils.py` | `text_content` | `age_rating` | 텍스트 → 시험 age_rating 추정 |
| `estimate_exam_age_rating` | `quiz/utils/exam_utils.py` | `exam, questions` | `age_rating` | 시험 → 최종 age_rating 평가 |
| `adjust_exam_difficulty_by_age_rating` | `quiz/utils/exam_utils.py` | `exam_difficulty, age_rating` | `exam_difficulty` (조정) | 시험 age_rating → 시험 난이도 조정 |

---

## 주의사항

1. **사용자 rating**과 **시험 age_rating**은 서로 다른 개념입니다:
   - **사용자 rating**: 사용자의 나이에 따라 결정되는 등급 (접근 권한 제어)
   - **시험 age_rating**: 시험 내용을 분석하여 추정되는 등급 (콘텐츠 적합성)

2. **시험 난이도 조정**은 문제 생성 **전**에 수행됩니다:
   - 텍스트 분석으로 시험 `age_rating` 추정
   - 추정된 `age_rating`에 따라 `exam_difficulty` 조정
   - 조정된 `exam_difficulty`로 문제 생성 (easy/medium/hard 분배)

3. **기본 난이도 설정**은 사용자가 난이도를 지정하지 않은 경우에만 적용됩니다:
   - 사용자가 명시적으로 난이도를 지정하면 그 값을 사용
   - 지정하지 않은 경우 사용자의 `age_rating`에 따라 기본값 설정

