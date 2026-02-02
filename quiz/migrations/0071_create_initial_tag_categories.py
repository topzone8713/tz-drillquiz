# Generated manually for initial tag categories

from django.db import migrations


def create_initial_categories(apps, schema_editor):
    """초기 태그 카테고리 데이터 생성"""
    TagCategory = apps.get_model('quiz', 'TagCategory')
    
    # 1단계 카테고리 생성
    category1 = TagCategory.objects.create(
        name_ko='취미 · 라이프스타일',
        name_en='Hobbies · Lifestyle',
        level=1,
        order=1,
        color='🟩',
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    category2 = TagCategory.objects.create(
        name_ko='엔터테인먼트 · 문화',
        name_en='Entertainment · Culture',
        level=1,
        order=2,
        color='🟦',
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    category3 = TagCategory.objects.create(
        name_ko='자기계발 · 커리어',
        name_en='Self-Development · Career',
        level=1,
        order=3,
        color='🟨',
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    category4 = TagCategory.objects.create(
        name_ko='IT 기술',
        name_en='IT Technology',
        level=1,
        order=4,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    # 1. 취미 · 라이프스타일 하위 카테고리
    TagCategory.objects.create(
        parent=category1,
        name_ko='요리 · 베이킹',
        name_en='Cooking · Baking',
        level=2,
        order=1,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category1,
        name_ko='여행 · 캠핑',
        name_en='Travel · Camping',
        level=2,
        order=2,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category1,
        name_ko='반려동물 · 펫케어',
        name_en='Pets · Pet Care',
        level=2,
        order=3,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category1,
        name_ko='가드닝 · 플랜테리어',
        name_en='Gardening · Plant Interior',
        level=2,
        order=4,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category1,
        name_ko='홈인테리어 · DIY',
        name_en='Home Interior · DIY',
        level=2,
        order=5,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category1,
        name_ko='패션 · 뷰티 · 스타일링',
        name_en='Fashion · Beauty · Styling',
        level=2,
        order=6,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category1,
        name_ko='건강 · 운동 · 피트니스',
        name_en='Health · Exercise · Fitness',
        level=2,
        order=7,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category1,
        name_ko='음악 · 악기',
        name_en='Music · Instruments',
        level=2,
        order=8,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    # 2. 엔터테인먼트 · 문화 하위 카테고리
    TagCategory.objects.create(
        parent=category2,
        name_ko='드라마 분석 · 해석',
        name_en='Drama Analysis · Interpretation',
        level=2,
        order=1,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category2,
        name_ko='영화 리뷰 · 영화 제작 기초',
        name_en='Movie Review · Film Production Basics',
        level=2,
        order=2,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category2,
        name_ko='예능 · 방송 콘텐츠 분석',
        name_en='Variety Shows · Broadcast Content Analysis',
        level=2,
        order=3,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category2,
        name_ko='음악 감상 · 뮤직비디오 해석',
        name_en='Music Appreciation · Music Video Interpretation',
        level=2,
        order=4,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category2,
        name_ko='K-Pop · 아이돌 관련 콘텐츠',
        name_en='K-Pop · Idol Related Content',
        level=2,
        order=5,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category2,
        name_ko='문화 · 트렌드 이야기',
        name_en='Culture · Trend Stories',
        level=2,
        order=6,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category2,
        name_ko='OTT 추천 · 작품 가이드',
        name_en='OTT Recommendations · Content Guide',
        level=2,
        order=7,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    # 3. 자기계발 · 커리어 하위 카테고리
    TagCategory.objects.create(
        parent=category3,
        name_ko='커뮤니케이션 · 발표',
        name_en='Communication · Presentation',
        level=2,
        order=1,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category3,
        name_ko='시간관리 · 생산성',
        name_en='Time Management · Productivity',
        level=2,
        order=2,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category3,
        name_ko='직장인 실무(Excel/Notion/PowerPoint)',
        name_en='Office Work (Excel/Notion/PowerPoint)',
        level=2,
        order=3,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category3,
        name_ko='리더십 · 조직관리',
        name_en='Leadership · Organization Management',
        level=2,
        order=4,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category3,
        name_ko='취업 · 이직 · 면접',
        name_en='Job Search · Career Change · Interview',
        level=2,
        order=5,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category3,
        name_ko='경제 · 재테크 · 부동산',
        name_en='Economics · Investment · Real Estate',
        level=2,
        order=6,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category3,
        name_ko='창업 · 사이드프로젝트',
        name_en='Startup · Side Project',
        level=2,
        order=7,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    # 4. IT 기술 하위 카테고리
    TagCategory.objects.create(
        parent=category4,
        name_ko='스마트폰 사용법',
        name_en='Smartphone Usage',
        level=2,
        order=1,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    TagCategory.objects.create(
        parent=category4,
        name_ko='엑셀 · 데이터 기초',
        name_en='Excel · Data Basics',
        level=2,
        order=3,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )
    
    # 4.6 IT 기술 (기존 태그들이 여기에 할당될 카테고리)
    it_tech_category = TagCategory.objects.create(
        parent=category4,
        name_ko='IT 기술',
        name_en='IT Technology',
        level=2,
        order=6,
        is_ko_complete=True,
        is_en_complete=True,
        created_language='ko'
    )


def reverse_create_categories(apps, schema_editor):
    """마이그레이션 롤백 시 모든 카테고리 삭제"""
    TagCategory = apps.get_model('quiz', 'TagCategory')
    TagCategory.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0070_tagcategory_tag_categories_and_more'),
    ]

    operations = [
        migrations.RunPython(create_initial_categories, reverse_create_categories),
    ]

