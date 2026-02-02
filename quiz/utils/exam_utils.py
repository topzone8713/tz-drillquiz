"""
시험 관련 유틸리티 함수
"""
import re
import logging

logger = logging.getLogger(__name__)


def estimate_exam_age_rating(exam, questions=None):
    """
    시험의 제목, 설명, 문제 내용을 분석하여 연령 등급을 추정합니다.
    
    등급 기준:
    - 4+: 4세 미만 (누구나 사용 가능, 폭력·성적·도박·웹 접근·UGC가 거의 없어야 허용됨)
    - 9+: 4세 이상 9세 미만 (경미한 만화적/가벼운 요소 허용, 위험 기능은 여전히 제한적)
    - 12+: 9세 이상 12세 미만 (UGC 가능, 소셜 기능 가능, 제한된 웹 접근 가능, 약간의 현실적 폭력·공포·경쟁적 요소 허용)
    - 17+: 12세 이상 (성인 콘텐츠, 강한 폭력, 완전한 웹 브라우징, 무제한 UGC, 메시징/DM, 도박, 뉴스/웹 전체 접근 등)
    
    Args:
        exam: Exam 모델 인스턴스
        questions: 시험에 포함된 Question 객체 리스트 (선택적)
        
    Returns:
        str: '4+', '9+', '12+', '17+' 중 하나
    """
    # 기본 등급은 17+ (가장 제한이 적음)
    rating_score = 0  # 점수가 높을수록 더 높은 등급 필요
    
    # 모든 언어의 제목과 설명을 수집
    all_texts = []
    
    # 제목 수집
    from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
    for lang in SUPPORTED_LANGUAGES:
        title = getattr(exam, f'title_{lang}', '')
        description = getattr(exam, f'description_{lang}', '')
        if title:
            all_texts.append(title.lower())
        if description:
            all_texts.append(description.lower())
    
    # 문제 내용 수집 (제공된 경우)
    if questions:
        for question in questions:
            for lang in SUPPORTED_LANGUAGES:
                content = getattr(question, f'content_{lang}', '')
                answer = getattr(question, f'answer_{lang}', '')
                if content:
                    all_texts.append(content.lower())
                if answer:
                    all_texts.append(answer.lower())
    
    # 모든 텍스트를 하나로 합침
    combined_text = ' '.join(all_texts)
    
    if not combined_text.strip():
        # 텍스트가 없으면 기본값 17+ 반환
        return '17+'
    
    # 성인 콘텐츠 키워드 검사 (17+ 필요)
    adult_keywords = [
        # 영어
        'violence', 'violent', 'blood', 'gore', 'death', 'kill', 'murder', 'weapon', 'gun', 'knife',
        'sexual', 'sex', 'nude', 'nudity', 'porn', 'adult', 'mature', 'explicit',
        'gambling', 'casino', 'poker', 'bet', 'betting', 'lottery',
        'drug', 'alcohol', 'beer', 'wine', 'cigarette', 'smoking',
        # 한국어
        '폭력', '살인', '범죄', '무기', '총', '칼', '피', '죽음',
        '성적', '성인', '음란', '야한', '노출',
        '도박', '카지노', '베팅', '복권',
        '마약', '알코올', '술', '담배', '흡연',
        # 스페인어
        'violencia', 'violento', 'sangre', 'muerte', 'matar', 'arma', 'pistola', 'cuchillo',
        'sexual', 'sexo', 'desnudo', 'pornografía', 'adulto', 'maduro', 'explícito',
        'juego', 'casino', 'póker', 'apuesta', 'lotería',
        'droga', 'alcohol', 'cerveza', 'vino', 'cigarrillo', 'fumar',
        # 중국어
        '暴力', '血腥', '死亡', '杀人', '武器', '枪', '刀',
        '性', '色情', '成人', '裸露',
        '赌博', '赌场', '扑克', '投注', '彩票',
        '毒品', '酒精', '酒', '香烟', '吸烟',
        # 일본어
        '暴力', '血', '死', '殺', '武器', '銃', '刀',
        '性的', 'ポルノ', '成人', '露出',
        'ギャンブル', 'カジノ', 'ポーカー', '賭け', '宝くじ',
        '薬物', 'アルコール', '酒', 'タバコ', '喫煙',
    ]
    
    # 공포/무서운 콘텐츠 키워드 (12+ 필요)
    horror_keywords = [
        # 영어
        'horror', 'scary', 'frightening', 'terror', 'ghost', 'zombie', 'monster', 'demon',
        # 한국어
        '공포', '무서운', '귀신', '좀비', '괴물', '악마',
        # 스페인어
        'horror', 'aterrador', 'terror', 'fantasma', 'zombi', 'monstruo', 'demonio',
        # 중국어
        '恐怖', '可怕', '鬼', '僵尸', '怪物', '恶魔',
        # 일본어
        'ホラー', '怖い', '幽霊', 'ゾンビ', 'モンスター', '悪魔',
    ]
    
    # 경쟁적/전략적 콘텐츠 키워드 (12+ 필요)
    competitive_keywords = [
        # 영어
        'war', 'battle', 'fight', 'combat', 'strategy', 'tactics', 'military',
        # 한국어
        '전쟁', '전투', '싸움', '전략', '전술', '군사',
        # 스페인어
        'guerra', 'batalla', 'lucha', 'combate', 'estrategia', 'táctica', 'militar',
        # 중국어
        '战争', '战斗', '打架', '战略', '战术', '军事',
        # 일본어
        '戦争', '戦闘', '戦い', '戦略', '戦術', '軍事',
    ]
    
    # 교육적/기본 콘텐츠 키워드 (4+ 또는 9+ 가능)
    educational_keywords = [
        # 영어
        'learn', 'study', 'education', 'school', 'student', 'teacher', 'lesson', 'quiz', 'test',
        'math', 'science', 'language', 'reading', 'writing', 'alphabet', 'number', 'color',
        # 한국어
        '학습', '공부', '교육', '학교', '학생', '선생님', '수업', '퀴즈', '시험',
        '수학', '과학', '언어', '읽기', '쓰기', '알파벳', '숫자', '색깔',
        # 스페인어
        'aprender', 'estudiar', 'educación', 'escuela', 'estudiante', 'maestro', 'lección', 'prueba',
        'matemáticas', 'ciencia', 'idioma', 'lectura', 'escritura', 'alfabeto', 'número', 'color',
        # 중국어
        '学习', '教育', '学校', '学生', '老师', '课程', '测验',
        '数学', '科学', '语言', '阅读', '写作', '字母', '数字', '颜色',
        # 일본어
        '学習', '勉強', '教育', '学校', '学生', '先生', '授業', 'テスト',
        '数学', '科学', '言語', '読書', '書き', 'アルファベット', '数字', '色',
    ]
    
    # 키워드 검사
    adult_matches = [keyword for keyword in adult_keywords if keyword in combined_text]
    horror_matches = [keyword for keyword in horror_keywords if keyword in combined_text]
    competitive_matches = [keyword for keyword in competitive_keywords if keyword in combined_text]
    educational_matches = [keyword for keyword in educational_keywords if keyword in combined_text]
    
    adult_count = len(adult_matches)
    horror_count = len(horror_matches)
    competitive_count = len(competitive_matches)
    educational_count = len(educational_matches)
    
    # 텍스트 길이와 복잡도 계산
    text_length = len(combined_text)
    word_count = len(combined_text.split())
    
    # 디버깅 로그
    from quiz.utils.multilingual_utils import get_localized_field, BASE_LANGUAGE
    exam_lang = exam.created_language if hasattr(exam, 'created_language') else BASE_LANGUAGE
    exam_title = get_localized_field(exam, 'title', exam_lang, '') if exam else ''
    logger.info(f"[ESTIMATE_AGE_RATING] 시험 ID: {exam.id if exam else 'N/A'}, 제목: {exam_title}")
    logger.info(f"[ESTIMATE_AGE_RATING] 텍스트 길이: {text_length}자, 단어 수: {word_count}개")
    logger.info(f"[ESTIMATE_AGE_RATING] 키워드 검사 결과 - 성인: {adult_count}, 공포: {horror_count}, 경쟁적: {competitive_count}, 교육적: {educational_count}")
    
    # 점수 계산
    if adult_count > 0:
        # 성인 콘텐츠가 있으면 무조건 17+
        logger.info(f"[ESTIMATE_AGE_RATING] 성인 콘텐츠 키워드 발견 ({adult_count}개) → 17+")
        logger.info(f"[ESTIMATE_AGE_RATING] 매칭된 성인 키워드: {adult_matches[:10]}")  # 최대 10개만 표시
        return '17+'
    
    if horror_count > 2 or competitive_count > 3:
        # 공포/무서운 콘텐츠가 많거나 경쟁적 콘텐츠가 많으면 12+
        rating_score = 12
        logger.info(f"[ESTIMATE_AGE_RATING] 공포/경쟁적 콘텐츠 많음 (공포: {horror_count}, 경쟁적: {competitive_count}) → 초기 점수: 12")
    elif horror_count > 0 or competitive_count > 0:
        # 공포/무서운 콘텐츠가 조금 있거나 경쟁적 콘텐츠가 조금 있으면 9+
        rating_score = 9
        logger.info(f"[ESTIMATE_AGE_RATING] 공포/경쟁적 콘텐츠 조금 (공포: {horror_count}, 경쟁적: {competitive_count}) → 초기 점수: 9")
    elif educational_count > 5:
        # 교육적 콘텐츠가 많으면 4+ 가능
        rating_score = 4
        logger.info(f"[ESTIMATE_AGE_RATING] 교육적 콘텐츠 많음 ({educational_count}개) → 초기 점수: 4")
    else:
        # 기본값은 9+ (안전한 기본값)
        rating_score = 9
        logger.info(f"[ESTIMATE_AGE_RATING] 키워드 매칭 없음 → 초기 점수: 9 (기본값)")
    
    # 텍스트 길이와 복잡도 고려
    # 매우 짧고 단순한 텍스트는 4+ 가능
    if text_length < 100 and word_count < 20 and educational_count > 0:
        rating_score = min(rating_score, 4)
        logger.info(f"[ESTIMATE_AGE_RATING] 짧고 단순한 텍스트 → 점수 조정: {rating_score}")
    # 매우 긴 텍스트는 더 높은 등급 필요 가능성
    elif text_length > 5000 or word_count > 500:
        old_score = rating_score
        rating_score = max(rating_score, 12)
        logger.info(f"[ESTIMATE_AGE_RATING] 긴 텍스트 ({text_length}자, {word_count}단어) → 점수 조정: {old_score} → {rating_score}")
    
    # 등급 결정
    if rating_score <= 4:
        final_rating = '4+'
    elif rating_score <= 9:
        final_rating = '9+'
    elif rating_score <= 12:
        final_rating = '12+'
    else:
        final_rating = '17+'
    
    logger.info(f"[ESTIMATE_AGE_RATING] 최종 결정 - 점수: {rating_score}, 등급: {final_rating}")
    return final_rating


def estimate_age_rating_from_text(text_content, title=None, description=None):
    """
    텍스트 내용만으로 연령 등급을 추정합니다.
    문제 생성 전에 사용하여 초기 age_rating을 추정합니다.
    
    Args:
        text_content: 분석할 텍스트 내용
        title: 시험 제목 (선택적)
        description: 시험 설명 (선택적)
        
    Returns:
        str: '4+', '9+', '12+', '17+' 중 하나
    """
    if not text_content or not text_content.strip():
        return '17+'
    
    # 텍스트를 소문자로 변환
    combined_text = text_content.lower()
    if title:
        combined_text = f"{title.lower()} {combined_text}"
    if description:
        combined_text = f"{description.lower()} {combined_text}"
    
    # 키워드 정의 (estimate_exam_age_rating과 동일)
    adult_keywords = [
        'violence', 'violent', 'blood', 'gore', 'death', 'kill', 'murder', 'weapon', 'gun', 'knife',
        'sexual', 'sex', 'nude', 'nudity', 'porn', 'adult', 'mature', 'explicit',
        'gambling', 'casino', 'poker', 'bet', 'betting', 'lottery',
        'drug', 'alcohol', 'beer', 'wine', 'cigarette', 'smoking',
        '폭력', '살인', '범죄', '무기', '총', '칼', '피', '죽음',
        '성적', '성인', '음란', '야한', '노출',
        '도박', '카지노', '베팅', '복권',
        '마약', '알코올', '술', '담배', '흡연',
    ]
    
    horror_keywords = [
        'horror', 'scary', 'frightening', 'terror', 'ghost', 'zombie', 'monster', 'demon',
        '공포', '무서운', '귀신', '좀비', '괴물', '악마',
    ]
    
    competitive_keywords = [
        'war', 'battle', 'fight', 'combat', 'strategy', 'tactics', 'military',
        '전쟁', '전투', '싸움', '전략', '전술', '군사',
    ]
    
    educational_keywords = [
        'learn', 'study', 'education', 'school', 'student', 'teacher', 'lesson', 'quiz', 'test',
        'math', 'science', 'language', 'reading', 'writing', 'alphabet', 'number', 'color',
        '학습', '공부', '교육', '학교', '학생', '선생님', '수업', '퀴즈', '시험',
        '수학', '과학', '언어', '읽기', '쓰기', '알파벳', '숫자', '색깔',
    ]
    
    # 키워드 검사
    adult_count = sum(1 for keyword in adult_keywords if keyword in combined_text)
    horror_count = sum(1 for keyword in horror_keywords if keyword in combined_text)
    competitive_count = sum(1 for keyword in competitive_keywords if keyword in combined_text)
    educational_count = sum(1 for keyword in educational_keywords if keyword in combined_text)
    
    text_length = len(combined_text)
    word_count = len(combined_text.split())
    
    logger.info(f"[ESTIMATE_AGE_RATING_FROM_TEXT] 텍스트 길이: {text_length}자, 단어 수: {word_count}개")
    logger.info(f"[ESTIMATE_AGE_RATING_FROM_TEXT] 키워드 검사 결과 - 성인: {adult_count}, 공포: {horror_count}, 경쟁적: {competitive_count}, 교육적: {educational_count}")
    
    # 점수 계산
    if adult_count > 0:
        logger.info(f"[ESTIMATE_AGE_RATING_FROM_TEXT] 성인 콘텐츠 키워드 발견 ({adult_count}개) → 17+")
        return '17+'
    
    rating_score = 9  # 기본값
    if horror_count > 2 or competitive_count > 3:
        rating_score = 12
    elif horror_count > 0 or competitive_count > 0:
        rating_score = 9
    elif educational_count > 5:
        rating_score = 4
    
    # 텍스트 길이 고려
    if text_length < 100 and word_count < 20 and educational_count > 0:
        rating_score = min(rating_score, 4)
    elif text_length > 5000 or word_count > 500:
        rating_score = max(rating_score, 12)
    
    # 등급 결정
    if rating_score <= 4:
        final_rating = '4+'
    elif rating_score <= 9:
        final_rating = '9+'
    elif rating_score <= 12:
        final_rating = '12+'
    else:
        final_rating = '17+'
    
    logger.info(f"[ESTIMATE_AGE_RATING_FROM_TEXT] 최종 결정 - 점수: {rating_score}, 등급: {final_rating}")
    return final_rating


def adjust_exam_difficulty_by_age_rating(exam_difficulty, age_rating):
    """
    연령 등급에 따라 시험 난이도를 조정합니다.
    
    조정 규칙:
    - 4+: 난이도 그대로 유지 (가장 낮은 등급이므로)
    - 9+: 난이도를 낮춤 (어린 사용자를 위해 쉬운 문제 제공)
    - 12+: 난이도 약간 낮춤
    - 17+: 난이도를 높임 (성인 사용자를 위해 더 도전적인 문제 제공)
    
    Args:
        exam_difficulty: 현재 시험 난이도 (1~10)
        age_rating: 연령 등급 ('4+', '9+', '12+', '17+')
        
    Returns:
        int: 조정된 시험 난이도 (1~10 범위 내)
    """
    # 난이도 범위 검증
    exam_difficulty = max(1, min(10, int(exam_difficulty)))
    
    if age_rating == '4+':
        # 4+ 등급: 난이도 그대로 유지
        adjusted_difficulty = exam_difficulty
        logger.info(f"[ADJUST_DIFFICULTY] 4+ 등급 → 난이도 유지: {exam_difficulty}")
        
    elif age_rating == '9+':
        # 9+ 등급: 난이도를 낮춤 (최대 3단계 낮춤, 최소 1)
        # 예: 10 → 7, 8 → 6, 5 → 4, 3 → 2, 2 → 1
        adjustment = -3
        adjusted_difficulty = max(1, exam_difficulty + adjustment)
        logger.info(f"[ADJUST_DIFFICULTY] 9+ 등급 → 난이도 조정: {exam_difficulty} → {adjusted_difficulty} (조정: {adjustment})")
        
    elif age_rating == '12+':
        # 12+ 등급: 난이도를 약간 낮춤 (최대 1단계 낮춤, 최소 1)
        # 예: 10 → 9, 8 → 7, 5 → 4, 2 → 1
        adjustment = -1
        adjusted_difficulty = max(1, exam_difficulty + adjustment)
        logger.info(f"[ADJUST_DIFFICULTY] 12+ 등급 → 난이도 조정: {exam_difficulty} → {adjusted_difficulty} (조정: {adjustment})")
        
    else:  # '17+'
        # 17+ 등급: 난이도를 높임 (최대 2단계 높임, 최대 10)
        # 예: 2 → 4, 3 → 5, 5 → 7, 8 → 10, 10 → 10
        adjustment = 2
        adjusted_difficulty = min(10, exam_difficulty + adjustment)
        logger.info(f"[ADJUST_DIFFICULTY] 17+ 등급 → 난이도 조정: {exam_difficulty} → {adjusted_difficulty} (조정: {adjustment})")
    
    return adjusted_difficulty


def get_default_difficulty_by_age_rating(age_rating):
    """
    연령 등급에 따른 기본 시험 난이도를 반환합니다.
    
    Args:
        age_rating: 연령 등급 ('4+', '9+', '12+', '17+')
        
    Returns:
        int: 기본 시험 난이도 (1~10)
    """
    if not age_rating:
        return 5  # 기본값
    
    if age_rating == '4+':
        return 3  # 낮은 난이도
    elif age_rating == '9+':
        return 4  # 낮은 난이도
    elif age_rating == '12+':
        return 5  # 중간 난이도
    elif age_rating == '17+':
        return 7  # 높은 난이도
    else:
        return 5  # 기본값


def get_gemini_safety_settings_by_age_rating(age_rating):
    """
    연령 등급에 따라 Gemini API의 안전 필터 설정을 반환합니다.
    
    등급별 안전 필터 설정:
    - 4+: BLOCK_MEDIUM_AND_ABOVE (MEDIUM 이상 차단, 가장 엄격)
    - 9+: BLOCK_MEDIUM_AND_ABOVE (MEDIUM 이상 차단)
    - 12+: BLOCK_ONLY_HIGH (HIGH 위험도만 차단, 관대)
    - 17+: BLOCK_NONE (차단 없음, 최대 관대)
    - 기본값: BLOCK_ONLY_HIGH
    
    Args:
        age_rating: 연령 등급 ('4+', '9+', '12+', '17+', 또는 None)
    
    Returns:
        list: Gemini API의 safety_settings 리스트
        None: safety_settings를 사용하지 않을 경우 (fallback)
    """
    try:
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        # 연령 등급에 따른 안전 필터 임계값 설정
        if age_rating == '17+':
            # 17+ 등급: BLOCK_NONE (모든 콘텐츠 허용, 성인 콘텐츠)
            threshold = HarmBlockThreshold.BLOCK_NONE
            logger.info(f"[get_gemini_safety_settings] 17+ 등급 감지: 안전 필터 완전 비활성화 (BLOCK_NONE)")
        elif age_rating == '12+':
            # 12+ 등급: BLOCK_ONLY_HIGH (HIGH 위험도만 차단)
            threshold = HarmBlockThreshold.BLOCK_ONLY_HIGH
            logger.info(f"[get_gemini_safety_settings] 12+ 등급 감지: HIGH 위험도만 차단 (BLOCK_ONLY_HIGH)")
        elif age_rating in ['9+', '4+']:
            # 9+, 4+ 등급: BLOCK_MEDIUM_AND_ABOVE (MEDIUM 이상 차단, 엄격한 필터링)
            threshold = HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            logger.info(f"[get_gemini_safety_settings] {age_rating} 등급 감지: MEDIUM 이상 차단 (BLOCK_MEDIUM_AND_ABOVE)")
        else:
            # 기본값: age_rating이 없거나 알 수 없는 경우 BLOCK_ONLY_HIGH 사용
            threshold = HarmBlockThreshold.BLOCK_ONLY_HIGH
            logger.info(f"[get_gemini_safety_settings] age_rating 미지정 또는 알 수 없음 ({age_rating}): 기본값 BLOCK_ONLY_HIGH 사용")
        
        # 모든 카테고리에 동일한 임계값 적용
        safety_settings = [
            {
                "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": threshold
            },
            {
                "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": threshold
            },
            {
                "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": threshold
            },
            {
                "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": threshold
            }
        ]
        
        return safety_settings
    except (ImportError, AttributeError, TypeError) as e:
        # Google Generative AI SDK가 없거나 enum을 가져올 수 없는 경우
        logger.warning(f"[get_gemini_safety_settings] 안전 필터 설정 실패: {e}, None 반환 (기본 설정 사용)")
        return None

