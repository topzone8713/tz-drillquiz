"""
사용자 관련 유틸리티 함수
"""
from datetime import date


def calculate_age_rating(date_of_birth):
    """
    생년월일을 기반으로 나이 등급을 계산합니다.
    
    등급 기준:
    - 4+: 4세 미만 (누구나 사용 가능, 폭력·성적·도박·웹 접근·UGC가 거의 없어야 허용됨)
    - 9+: 4세 이상 9세 미만 (경미한 만화적/가벼운 요소 허용, 위험 기능은 여전히 제한적)
    - 12+: 9세 이상 12세 미만 (UGC 가능, 소셜 기능 가능, 제한된 웹 접근 가능, 약간의 현실적 폭력·공포·경쟁적 요소 허용)
    - 17+: 12세 이상 (성인 콘텐츠, 강한 폭력, 완전한 웹 브라우징, 무제한 UGC, 메시징/DM, 도박, 뉴스/웹 전체 접근 등)
    
    Args:
        date_of_birth: datetime.date 객체 또는 None
        
    Returns:
        str: '4+', '9+', '12+', '17+' 중 하나, date_of_birth가 None이면 '17+' 반환
    """
    if not date_of_birth:
        # 생년월일이 없으면 기본적으로 17+ 등급 (성인 콘텐츠 허용)
        return '17+'
    
    today = date.today()
    
    # 나이 계산
    age = today.year - date_of_birth.year
    # 생일이 아직 지나지 않았으면 1살 빼기
    if today.month < date_of_birth.month or (today.month == date_of_birth.month and today.day < date_of_birth.day):
        age -= 1
    
    # 나이에 따라 등급 결정
    if age < 4:
        return '4+'
    elif age < 9:
        return '9+'
    elif age < 12:
        return '12+'
    else:
        return '17+'

