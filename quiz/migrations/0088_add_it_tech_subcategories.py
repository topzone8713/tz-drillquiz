# Generated manually to add IT Technology subcategories

from django.db import migrations


def add_it_tech_subcategories(apps, schema_editor):
    """IT 기술 > IT 기술 하위에 3단계 카테고리 추가"""
    TagCategory = apps.get_model('quiz', 'TagCategory')
    
    # 1단계 "IT 기술" 카테고리 찾기
    it_category_level1 = TagCategory.objects.filter(
        level=1,
        name_ko='IT 기술'
    ).first()
    
    if not it_category_level1:
        print("⚠️ 1단계 'IT 기술' 카테고리를 찾을 수 없습니다.")
        return
    
    # 2단계 "IT 기술" 카테고리 찾기 (IT 기술 > IT 기술)
    it_tech_category = TagCategory.objects.filter(
        parent=it_category_level1,
        level=2,
        name_ko='IT 기술',
        order=6
    ).first()
    
    if not it_tech_category:
        print("⚠️ 2단계 'IT 기술' 카테고리를 찾을 수 없습니다.")
        return
    
    # 3단계 카테고리들 추가
    subcategories = [
        {
            'name_ko': '개발 · 프로그래밍',
            'name_en': 'Development · Programming',
            'order': 1,
        },
        {
            'name_ko': 'AI',
            'name_en': 'AI',
            'order': 2,
        },
        {
            'name_ko': '게임',
            'name_en': 'Gaming',
            'order': 3,
        },
        {
            'name_ko': '데이터 사이언스',
            'name_en': 'Data Science',
            'order': 4,
        },
        {
            'name_ko': '보안 · 네트워크',
            'name_en': 'Security · Network',
            'order': 5,
        },
        {
            'name_ko': '하드웨어',
            'name_en': 'Hardware',
            'order': 6,
        },
        {
            'name_ko': '디자인 · 아트',
            'name_en': 'Design · Art',
            'order': 7,
        },
    ]
    
    for subcat in subcategories:
        TagCategory.objects.create(
            parent=it_tech_category,
            name_ko=subcat['name_ko'],
            name_en=subcat['name_en'],
            level=3,
            order=subcat['order'],
            is_ko_complete=True,
            is_en_complete=True,
            created_language='ko'
        )
    
    print(f"✅ {len(subcategories)}개의 IT 기술 하위 카테고리를 추가했습니다.")


def reverse_add_subcategories(apps, schema_editor):
    """마이그레이션 롤백 시 추가된 카테고리 삭제"""
    TagCategory = apps.get_model('quiz', 'TagCategory')
    
    # 1단계 "IT 기술" 카테고리 찾기
    it_category_level1 = TagCategory.objects.filter(
        level=1,
        name_ko='IT 기술'
    ).first()
    
    if it_category_level1:
        # 2단계 "IT 기술" 카테고리 찾기
        it_tech_category = TagCategory.objects.filter(
            parent=it_category_level1,
            level=2,
            name_ko='IT 기술',
            order=6
        ).first()
        
        if it_tech_category:
            # 3단계 카테고리들 삭제
            subcategory_names = [
                '개발 · 프로그래밍',
                'AI',
                '게임',
                '데이터 사이언스',
                '보안 · 네트워크',
                '하드웨어',
                '디자인 · 아트',
            ]
            
            TagCategory.objects.filter(
                parent=it_tech_category,
                level=3,
                name_ko__in=subcategory_names
            ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0087_add_multilingual_fields_to_studytask'),
    ]

    operations = [
        migrations.RunPython(add_it_tech_subcategories, reverse_add_subcategories),
    ]

