# Generated manually to assign existing tags to IT Technology category

from django.db import migrations


def assign_tags_to_it_category(apps, schema_editor):
    """기존 모든 태그를 '4.6 IT 기술' 카테고리에 할당"""
    Tag = apps.get_model('quiz', 'Tag')
    TagCategory = apps.get_model('quiz', 'TagCategory')
    
    # "IT 기술" 카테고리 찾기 (level=2, name_ko='IT 기술', parent의 name_ko='IT 기술')
    try:
        # 먼저 1단계 "IT 기술" 카테고리 찾기
        it_category_level1 = TagCategory.objects.filter(
            level=1,
            name_ko='IT 기술'
        ).first()
        
        if it_category_level1:
            # 2단계 "IT 기술" 카테고리 찾기 (4.6 IT 기술)
            it_category = TagCategory.objects.filter(
                parent=it_category_level1,
                level=2,
                name_ko='IT 기술',
                order=6
            ).first()
            
            if it_category:
                # 모든 기존 태그에 카테고리 할당
                all_tags = Tag.objects.all()
                for tag in all_tags:
                    tag.categories.add(it_category)
                print(f"✅ {all_tags.count()}개의 태그를 'IT 기술' 카테고리에 할당했습니다.")
            else:
                print("⚠️ '4.6 IT 기술' 카테고리를 찾을 수 없습니다.")
        else:
            print("⚠️ 1단계 'IT 기술' 카테고리를 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 태그 할당 중 오류 발생: {str(e)}")


def reverse_assign_tags(apps, schema_editor):
    """마이그레이션 롤백 시 태그-카테고리 관계 제거"""
    Tag = apps.get_model('quiz', 'Tag')
    TagCategory = apps.get_model('quiz', 'TagCategory')
    
    try:
        it_category_level1 = TagCategory.objects.filter(
            level=1,
            name_ko='IT 기술'
        ).first()
        
        if it_category_level1:
            it_category = TagCategory.objects.filter(
                parent=it_category_level1,
                level=2,
                name_ko='IT 기술',
                order=6
            ).first()
            
            if it_category:
                # 모든 태그에서 카테고리 제거
                all_tags = Tag.objects.all()
                for tag in all_tags:
                    tag.categories.remove(it_category)
    except Exception as e:
        print(f"❌ 태그 할당 롤백 중 오류 발생: {str(e)}")


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0071_create_initial_tag_categories'),
    ]

    operations = [
        migrations.RunPython(assign_tags_to_it_category, reverse_assign_tags),
    ]

