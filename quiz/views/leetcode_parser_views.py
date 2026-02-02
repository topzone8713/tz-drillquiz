import re
import requests
import openai
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

# OpenAI 클라이언트 초기화
def get_openai_client():
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
    return openai.OpenAI(api_key=settings.OPENAI_API_KEY)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def parse_leetcode_problems(request):
    """
    LeetCode 문제 목록을 파싱하여 문제 정보를 추출합니다.
    
    요청 데이터:
    {
        "description": "146. LRU Cache\n45.9%\nMed.\n1. Two Sum\n56.3%\nEasy\n..."
    }
    
    응답:
    {
        "problems": [
            {
                "id": "146",
                "title": "LRU Cache",
                "difficulty": "Medium",
                "acceptance_rate": "45.9%",
                "url": "https://leetcode.com/problems/lru-cache/"
            },
            ...
        ]
    }
    """
    try:
        description = request.data.get('description', '')
        if not description:
            return Response({'error': '설명이 제공되지 않았습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        problems = parse_leetcode_text(description)
        
        return Response({
            'success': True,
            'problems': problems,
            'total_count': len(problems)
        })
        
    except Exception as e:
        logger.error(f"LeetCode 파싱 오류: {str(e)}")
        return Response({'error': f'파싱 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def parse_leetcode_text(text):
    """
    LeetCode 문제 목록 텍스트를 파싱합니다.
    
    예시 입력:
    146. LRU Cache
    45.9%
    Med.
    1. Two Sum
    56.3%
    Easy
    ...
    """
    problems = []
    lines = text.strip().split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 문제 번호와 제목 패턴 매칭 (예: "146. LRU Cache")
        problem_match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if problem_match:
            problem_id = problem_match.group(1)
            title = problem_match.group(2)
            
            # 다음 줄에서 정답률 찾기
            acceptance_rate = None
            difficulty = None
            
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # 정답률 패턴 (예: "45.9%")
                rate_match = re.match(r'^(\d+\.?\d*)%$', next_line)
                if rate_match:
                    acceptance_rate = next_line
                    i += 1
                    
                    # 그 다음 줄에서 난이도 찾기
                    if i + 1 < len(lines):
                        difficulty_line = lines[i + 1].strip()
                        if difficulty_line in ['Easy', 'Med.', 'Hard']:
                            difficulty = normalize_difficulty(difficulty_line)
                            i += 1
            
            # URL 생성
            url = generate_leetcode_url(title)
            
            problems.append({
                'id': problem_id,
                'title': title,
                'difficulty': difficulty or 'Medium',
                'acceptance_rate': acceptance_rate or '0%',
                'url': url
            })
        
        i += 1
    
    return problems

def normalize_difficulty(difficulty):
    """난이도를 정규화합니다."""
    difficulty_map = {
        'Easy': 'Easy',
        'Med.': 'Medium',
        'Medium': 'Medium',
        'Hard': 'Hard'
    }
    return difficulty_map.get(difficulty, 'Medium')

def generate_leetcode_url(title):
    """
    문제 제목으로부터 LeetCode URL을 생성합니다.
    """
    # 제목을 URL 친화적인 형태로 변환
    url_title = title.lower()
    # 공백을 하이픈으로 변환
    url_title = re.sub(r'\s+', '-', url_title)
    # 특수문자 제거
    url_title = re.sub(r'[^\w\-]', '', url_title)
    # 연속된 하이픈을 하나로 변환
    url_title = re.sub(r'-+', '-', url_title)
    # 앞뒤 하이픈 제거
    url_title = url_title.strip('-')
    
    return f"https://leetcode.com/problems/{url_title}/"

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_questions_from_leetcode(request):
    """
    LeetCode 문제 목록을 기반으로 AI를 통해 문제를 생성합니다.
    """
    try:
        problems = request.data.get('problems', [])
        if not problems:
            return Response({'error': '문제 목록이 제공되지 않았습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        generated_questions = []
        failed_problems = []
        
        for problem in problems:
            try:
                # AI를 통한 문제 생성
                question_data = generate_question_with_ai(problem)
                generated_questions.append(question_data)
                logger.info(f"문제 생성 성공: {problem.get('title', 'Unknown')}")
            except Exception as e:
                logger.error(f"문제 생성 실패 {problem.get('title', 'Unknown')}: {str(e)}")
                failed_problems.append({
                    'problem': problem,
                    'error': str(e)
                })
                continue
        
        response_data = {
            'success': True,
            'generated_questions': generated_questions,
            'total_generated': len(generated_questions),
            'total_requested': len(problems)
        }
        
        if failed_problems:
            response_data['failed_problems'] = failed_problems
            response_data['message'] = f"{len(generated_questions)}개 문제 생성 완료, {len(failed_problems)}개 실패"
        else:
            response_data['message'] = f"{len(generated_questions)}개 문제 모두 성공적으로 생성되었습니다."
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"문제 생성 오류: {str(e)}")
        return Response({'error': f'문제 생성 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def generate_question_with_ai(problem):
    """
    AI를 사용하여 LeetCode 문제 정보를 기반으로 문제를 생성합니다.
    OpenAI API를 호출하여 실제 문제를 생성합니다.
    """
    # OpenAI 사용 가능 여부 확인 (캐시 체크)
    from quiz.utils.multilingual_utils import check_openai_availability, mark_openai_unavailable
    is_openai_unavailable = not check_openai_availability()
    
    # OpenAI가 사용 불가능하면 기본 템플릿 반환
    if is_openai_unavailable:
        logger.warning("[generate_question_with_ai] OpenAI가 캐시에서 사용 불가능 상태로 확인됨, 기본 템플릿 반환")
        return {
            'title': f"{problem['id']}. {problem['title']}",
            'content': f"LeetCode 문제: {problem['title']}\n난이도: {problem['difficulty']}\n정답률: {problem['acceptance_rate']}\nURL: {problem['url']}\n\n이 문제를 해결하는 방법을 설명해주세요.",
            'answer': "문제 해결을 위한 핵심 접근 방법과 구현 포인트를 설명해주세요.",
            'difficulty': problem['difficulty'].lower(),
            'url': problem['url'],
            'leetcode_id': problem['id']
        }
    
    try:
        client = get_openai_client()
        
        # LeetCode 문제 정보를 기반으로 프롬프트 생성
        prompt = f"""
다음 LeetCode 문제 정보를 바탕으로 개발자 면접용 문제를 생성해주세요:

문제 ID: {problem['id']}
제목: {problem['title']}
난이도: {problem['difficulty']}
정답률: {problem['acceptance_rate']}
URL: {problem['url']}

다음 형식으로 응답해주세요:
제목: [문제 제목]
내용: [문제 설명 및 요구사항]
정답: [핵심 해결 방법 및 구현 포인트]
난이도: [쉬움/보통/어려움]

면접관의 관점에서 해당 문제를 어떻게 접근하고 해결할지에 대한 질문과 답변을 만들어주세요.
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 경험 많은 개발자 면접관입니다. LeetCode 문제를 바탕으로 실무에서 사용할 수 있는 면접 질문을 만들어주세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # AI 응답을 파싱하여 구조화된 데이터로 변환
        parsed_data = parse_ai_response(ai_response, problem)
        
        return parsed_data
        
    except Exception as e:
        logger.error(f"OpenAI API 호출 실패: {str(e)}")
        # OpenAI 실패 시 캐시에 마킹
        is_rate_limit = False
        if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            if e.response.status_code == 429:
                is_rate_limit = True
        elif '429' in str(e) or 'insufficient_quota' in str(e) or 'RateLimitError' in str(type(e).__name__):
            is_rate_limit = True
        
        if is_rate_limit:
            logger.warning(f"[generate_question_with_ai] OpenAI 429/quota 초과 에러 감지: {e}, 캐시에 마킹...")
        else:
            logger.warning(f"[generate_question_with_ai] OpenAI API 호출 실패: {e}, 캐시에 마킹...")
        mark_openai_unavailable()
        
        # API 호출 실패 시 기본 템플릿 반환
        return {
            'title': f"{problem['id']}. {problem['title']}",
            'content': f"LeetCode 문제: {problem['title']}\n난이도: {problem['difficulty']}\n정답률: {problem['acceptance_rate']}\nURL: {problem['url']}\n\n이 문제를 해결하는 방법을 설명해주세요.",
            'answer': "문제 해결을 위한 핵심 접근 방법과 구현 포인트를 설명해주세요.",
            'difficulty': problem['difficulty'].lower(),
            'url': problem['url'],
            'leetcode_id': problem['id']
        }

def parse_ai_response(ai_response, original_problem):
    """
    AI 응답을 파싱하여 구조화된 문제 데이터로 변환합니다.
    """
    lines = ai_response.split('\n')
    
    title = f"{original_problem['id']}. {original_problem['title']}"
    content = ""
    answer = ""
    difficulty = original_problem['difficulty'].lower()
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('제목:'):
            current_section = 'title'
            title = line.replace('제목:', '').strip()
        elif line.startswith('내용:'):
            current_section = 'content'
            content = line.replace('내용:', '').strip()
        elif line.startswith('정답:'):
            current_section = 'answer'
            answer = line.replace('정답:', '').strip()
        elif line.startswith('난이도:'):
            difficulty_text = line.replace('난이도:', '').strip().lower()
            if '쉬움' in difficulty_text:
                difficulty = 'easy'
            elif '어려움' in difficulty_text:
                difficulty = 'hard'
            else:
                difficulty = 'medium'
        else:
            # 현재 섹션에 내용 추가
            if current_section == 'content':
                content += '\n' + line
            elif current_section == 'answer':
                answer += '\n' + line
    
    # 기본값 설정
    if not content:
        content = f"LeetCode 문제: {original_problem['title']}\n난이도: {original_problem['difficulty']}\n정답률: {original_problem['acceptance_rate']}\nURL: {original_problem['url']}"
    
    if not answer:
        answer = "문제 해결을 위한 핵심 접근 방법과 구현 포인트를 설명해주세요."
    
    return {
        'title': title,
        'content': content,
        'answer': answer,
        'difficulty': difficulty,
        'url': original_problem['url'],
        'leetcode_id': original_problem['id']
    }
